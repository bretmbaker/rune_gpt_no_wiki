#!/usr/bin/env python3
# wiki_scraper.py - Scrape and save clean OSRS wiki content into categorized .txt files

import os
import re
import time
import json
import logging
import argparse
import datetime
import shutil
from typing import List, Dict, Any, Set, Tuple, Optional
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin, urlparse, unquote, quote
import hashlib
from nltk import sent_tokenize
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("wiki_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("wiki_scraper")

# Constants
BASE_URL = "https://oldschool.runescape.wiki"
OUTPUT_DIR = "wiki_data"
RAW_HTML_DIR = "raw_html"  # Directory to store raw HTML temporarily
MAX_CHUNK_SIZE = 500  # Approximate token count per chunk

# Define content categories and their corresponding directories
CONTENT_CATEGORIES = {
    "quests": "wiki_data/quests",
    "skills": "wiki_data/skills",
    "minigames": "wiki_data/minigames",
    "diaries": "wiki_data/diaries",
    "npcs": "wiki_data/npcs",
    "mechanics": "wiki_data/mechanics",
    "items": "wiki_data/items",
    "activities": "wiki_data/activities",
    "bestiary": "wiki_data/bestiary",
    "achievements": "wiki_data/achievements",
    "collection": "wiki_data/collection",
    "equipment": "wiki_data/equipment",
    "training_methods": "wiki_data/training_methods",
    "tutorial": "wiki_data/tutorial"
}

# Default categories to scrape
CATEGORIES = list(CONTENT_CATEGORIES.keys())

# Quest pages to scrape
QUEST_PAGES = [
    # Quest List Pages
    "Quests/List",
    "Quests/Free-to-play",
    "Quests/Members",
    "Quests/Novice",
    "Quests/Intermediate", 
    "Quests/Experienced",
    "Quests/Master",
    "Quests/Grandmaster",
    "Quests/Special",
    "Quests/Series",
    "Quests/Requirements",
    "Quests/Skill requirements",
    "Quests/Release dates",
    
    # Individual Quest Pages - will be populated dynamically
]

# User agent to avoid being blocked
HEADERS = {
    "User-Agent": "RuneGPT Knowledge Engine/1.0 (Educational Project)"
}

class WikiScraper:
    """Enhanced scraper for OSRS Wiki content."""
    
    def __init__(self, output_dir: str = OUTPUT_DIR, raw_html_dir: str = RAW_HTML_DIR, max_chunk_size: int = MAX_CHUNK_SIZE):
        """
        Initialize the scraper.
        
        Args:
            output_dir: Directory to save scraped content
            raw_html_dir: Directory to store raw HTML content temporarily
            max_chunk_size: Maximum size of text chunks in tokens
        """
        self.output_dir = output_dir
        self.raw_html_dir = raw_html_dir
        self.max_chunk_size = max_chunk_size
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.headers = HEADERS  # Store headers as instance variable
        
        # Configure logging first
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('wiki_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Base URLs for OSRS wiki
        self.base_url = "https://oldschool.runescape.wiki"
        self.api_url = f"{self.base_url}/api.php"
        
        # Statistics tracking
        self.stats = {
            "start_time": datetime.datetime.now(),
            "pages_processed": 0,
            "successful_scrapes": 0,
            "skipped_pages": 0,
            "failed_pages": 0,
            "failed_categories": 0,
            "visited_urls": set()
        }
        
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(raw_html_dir, exist_ok=True)
        
        # Create category directories
        for category_dir in CONTENT_CATEGORIES.values():
            os.makedirs(category_dir, exist_ok=True)
        
        # Track visited pages to avoid duplicates
        self.visited_urls = set()
        
        # Load progress if exists
        self.load_progress()
        
        # Load existing files to avoid re-scraping
        self.existing_files = self._load_existing_files()
        
        # Initialize quest list
        self.quest_list = set()
        
        # Track files that have been processed from raw_html
        self.processed_raw_files = set()
    
    def load_progress(self):
        """Load scraping progress from file."""
        try:
            with open("scraper_progress.json", "r") as f:
                progress = json.load(f)
                self.stats["start_time"] = datetime.datetime.fromisoformat(progress["start_time"])
                self.stats["pages_processed"] = progress["pages_processed"]
                self.stats["successful_scrapes"] = progress["successful_scrapes"]
                self.stats["skipped_pages"] = progress["skipped_pages"]
                self.stats["failed_pages"] = progress["failed_pages"]
                self.stats["failed_categories"] = progress["failed_categories"]
                self.stats["visited_urls"] = set(progress["visited_urls"])
                self.logger.info(f"Loaded progress: {len(self.stats['visited_urls'])} URLs already visited")
        except FileNotFoundError:
            self.logger.info("No progress file found, starting fresh")
            self.stats["start_time"] = datetime.datetime.now()
        except Exception as e:
            self.logger.error(f"Error loading progress: {e}")
            self.stats["start_time"] = datetime.datetime.now()
    
    def save_progress(self):
        """Save scraping progress to file."""
        progress = {
            "start_time": self.stats["start_time"].isoformat() if isinstance(self.stats["start_time"], datetime.datetime) else self.stats["start_time"],
            "pages_processed": self.stats["pages_processed"],
            "successful_scrapes": self.stats["successful_scrapes"],
            "skipped_pages": self.stats["skipped_pages"],
            "failed_pages": self.stats["failed_pages"],
            "failed_categories": self.stats["failed_categories"],
            "visited_urls": list(self.stats["visited_urls"])
        }
        
        with open("scraper_progress.json", "w") as f:
            json.dump(progress, f)
        self.logger.info("Progress saved")
    
    def _load_existing_files(self) -> Set[str]:
        """
        Load a set of existing filenames to avoid re-scraping.
        
        Returns:
            Set of existing filenames
        """
        existing_files = set()
        
        # Walk through all category directories
        for category_dir in CONTENT_CATEGORIES.values():
            if os.path.exists(category_dir):
                for root, _, files in os.walk(category_dir):
                    for file in files:
                        if file.endswith('.txt') or file.endswith('.json'):
                            # Extract the base filename without the chunk index
                            base_name = re.sub(r'_\d+\.txt$', '', file)
                            base_name = re.sub(r'_\d+\.json$', '', base_name)
                            existing_files.add(base_name)
        
        self.logger.info(f"Found {len(existing_files)} existing files")
        return existing_files
    
    def clean_filename(self, title: str) -> str:
        """
        Clean a title to create a filesystem-safe filename.
        
        Args:
            title: The title to clean
            
        Returns:
            Cleaned filename
        """
        # Convert to lowercase
        filename = title.lower()
        
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        
        # Remove special characters
        filename = re.sub(r'[^\w\-_]', '', filename)
        
        # Replace multiple underscores with a single one
        filename = re.sub(r'_+', '_', filename)
        
        # Remove leading/trailing underscores
        filename = filename.strip('_')
        
        return filename
    
    def clean_text(self, text: str) -> str:
        """
        Clean the scraped text by removing unnecessary elements.
        
        Args:
            text: Raw text from the wiki
            
        Returns:
            Cleaned text
        """
        # Remove references like [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        
        # Remove edit links like [edit]
        text = re.sub(r'\[edit\]', '', text)
        
        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove multiple spaces
        text = re.sub(r' {2,}', ' ', text)
        
        return text.strip()
    
    def extract_tables(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract tables from the page content."""
        tables = []
        
        # Find all tables except those in infoboxes
        for table in soup.find_all('table', {'class': ['wikitable', 'infobox']}):
            # Skip tables inside infoboxes
            if table.find_parent('table', {'class': 'infobox'}):
                continue
            
            table_data = {
                'headers': [],
                'rows': [],
                'links': [],
                'images': []
            }
            
            # Extract headers
            headers = table.find_all('th')
            if headers:
                table_data['headers'] = [h.get_text(strip=True) for h in headers]
            
            # Extract rows
            rows = table.find_all('tr')[1:]  # Skip header row
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if cells:
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    table_data['rows'].append(row_data)
            
            # Extract links
            links = table.find_all('a')
            table_data['links'] = [{'text': link.get_text(strip=True), 
                                  'href': link.get('href', '')} 
                                 for link in links if link.get('href')]
            
            # Extract images
            images = table.find_all('img')
            table_data['images'] = [{'src': img.get('src', ''),
                                    'alt': img.get('alt', '')}
                                   for img in images if img.get('src')]
            
            # Only add tables that have content
            if table_data['rows'] or table_data['links'] or table_data['images']:
                tables.append(table_data)
        
        return tables
    
    def extract_main_content(self, soup: BeautifulSoup) -> Tuple[str, Dict]:
        """Extract the main content from a wiki page."""
        try:
            # Find the main content div
            content_div = soup.find('div', {'id': 'mw-content-text'})
            if not content_div:
                self.logger.warning("Main content div not found")
                return "", {}

            # Remove unwanted elements
            for element in content_div.find_all(['div', 'table'], class_=['mw-editsection', 'reference', 'noprint', 'navbox', 'toc']):
                element.decompose()

            # Extract text from paragraphs, lists, and headers
            content = []
            for element in content_div.find_all(['p', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                text = element.get_text(strip=True)
                if text and not text.startswith('Jump to') and not text.endswith('navigation'):
                    content.append(text)

            # Extract metadata
            metadata = {
                'url': self.current_url,
                'title': soup.find('h1', {'id': 'firstHeading'}).get_text(strip=True) if soup.find('h1', {'id': 'firstHeading'}) else '',
                'categories': [cat.get_text(strip=True) for cat in soup.find_all('div', class_='mw-normal-catlinks')],
                'infobox': self.extract_infobox(soup)
            }

            return '\n\n'.join(content), metadata

        except Exception as e:
            self.logger.error(f"Error extracting main content: {str(e)}")
            return "", {}
    
    def extract_infobox(self, infobox: BeautifulSoup) -> Dict:
        """Extract data from an infobox."""
        if not infobox:
            return {}
        
        infobox_data = {}
        
        # Extract all rows from the infobox
        for row in infobox.find_all('tr'):
            # Get the label (first cell)
            label_cell = row.find('th')
            if not label_cell:
                continue
            
            label = label_cell.get_text(strip=True)
            if not label:
                continue
            
            # Get the value (second cell)
            value_cell = row.find('td')
            if not value_cell:
                continue
            
            # Extract links
            links = []
            for link in value_cell.find_all('a'):
                link_text = link.get_text(strip=True)
                link_href = link.get('href', '')
                if link_text and link_href:
                    links.append({
                        'text': link_text,
                        'href': link_href
                    })
                
            # Extract images
            images = []
            for img in value_cell.find_all('img'):
                src = img.get('src', '')
                alt = img.get('alt', '')
                if src:
                    images.append({
                        'src': src,
                        'alt': alt
                    })
                
            # Get the raw text value
            value = value_cell.get_text(strip=True)
            
            # Store the data
            infobox_data[label] = {
                'value': value,
                'links': links,
                'images': images
            }
        
        return infobox_data
    
    def chunk_text(self, text: str, title: str, category: str) -> List[Dict[str, Any]]:
        """
        Split text into chunks of approximately equal size.
        
        Args:
            text: Text to split
            title: Title of the page
            category: Category of the page
            
        Returns:
            List of chunks with metadata
        """
        # Split text into sentences
        sentences = sent_tokenize(text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            # Skip empty sentences
            if not sentence.strip():
                continue
            
            # Get size of sentence in bytes
            sentence_size = len(sentence.encode("utf-8"))
            
            # If adding this sentence would exceed chunk size, save current chunk
            if current_size + sentence_size > self.max_chunk_size and current_chunk:
                chunks.append({
                    "text": " ".join(current_chunk),
                    "title": title,
                    "category": category
                })
                current_chunk = []
                current_size = 0
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add final chunk if not empty
        if current_chunk:
            chunks.append({
                "text": " ".join(current_chunk),
                "title": title,
                "category": category
            })
        
        return chunks
    
    def get_full_url(self, path: str) -> str:
        """Convert a wiki path to a full URL."""
        # Handle category URLs
        if path.startswith('Category:'):
            # Keep the Category: prefix as is
            return urljoin(BASE_URL, f"/w/{path}")
        return urljoin(BASE_URL, path)
    
    def get_category_pages(self, category):
        """Get all pages in a category"""
        try:
            # Construct category URL - remove 'Category:' prefix if it exists
            category_name = category.replace('Category:', '')
            category_url = f"{self.base_url}/wiki/Category:{category_name}"
            
            # Make the request with proper headers
            try:
                response = self.session.get(category_url, headers=self.headers, timeout=30)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request failed for category {category}: {str(e)}")
                self.stats['failed_categories'] += 1
                return []
            
            # Parse the page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all links in the category page
            pages = []
            for link in soup.find_all('a'):
                href = link.get('href', '')
                
                # Skip invalid URLs
                if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                    continue
                    
                # Skip special pages, user pages, etc.
                if any(x in href.lower() for x in [
                    'special:', 'user:', 'talk:', 'file:', 'template:', 
                    'category:', 'help:', 'portal:', 'module:', 'mediawiki:',
                    'action=edit', 'action=history', 'action=purge',
                    'printable=yes', 'print=yes', 'mobileaction='
                ]):
                    continue
                
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    href = f"{self.base_url}{href}"
                elif not href.startswith('http'):
                    href = f"{self.base_url}/wiki/{href}"
                
                # Skip if already visited
                normalized_url = self._normalize_url(href)
                if normalized_url in self.visited_urls:
                    continue
                
                # Skip if file already exists
                title = self._extract_title_from_url(normalized_url)
                if title:
                    filename = f"{title}.txt"
                    if any(os.path.exists(os.path.join(cat_dir, filename)) 
                          for cat_dir in CONTENT_CATEGORIES.values()):
                        continue
                
                # Validate URL format
                try:
                    parsed_url = urlparse(href)
                    if not all([parsed_url.scheme, parsed_url.netloc]):
                        continue
                except Exception:
                    continue
                
                pages.append(href)
            
            self.logger.info(f"Found {len(pages)} new pages in category {category}")
            return pages
            
        except Exception as e:
            self.logger.error(f"Error getting pages for category {category}: {str(e)}")
            self.stats['failed_categories'] += 1
            return []
    
    def get_page_content(self, title: str) -> Tuple[str, str]:
        """
        Get the content of a wiki page.
        
        Args:
            title: Page title
            
        Returns:
            Tuple of (HTML content, page URL)
        """
        # Properly encode the title for the URL
        encoded_title = title.replace(' ', '_')
        encoded_title = encoded_title.replace("'", "%27")
        encoded_title = encoded_title.replace('"', "%22")
        encoded_title = encoded_title.replace('&', "%26")
        
        url = f"{BASE_URL}/wiki/{encoded_title}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.text, url
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Page not found: {url}")
            else:
                logger.error(f"HTTP error getting content for page {title}: {str(e)}")
            return "", ""
        except Exception as e:
            logger.error(f"Error getting content for page {title}: {str(e)}")
            return "", ""
    
    def save_chunks(self, chunks: List[Dict[str, Any]], category: str):
        """
        Save text chunks to files in JSON format.
        
        Args:
            chunks: List of chunks with metadata
            category: Category name
        """
        # Create category directory
        category_dir = os.path.join(self.output_dir, self.clean_filename(category))
        os.makedirs(category_dir, exist_ok=True)
        
        # Save each chunk
        for chunk in chunks:
            title = self.clean_filename(chunk["title"])
            chunk_index = chunk["chunk_index"]
            
            filename = f"{title}_{chunk_index}.txt"
            filepath = os.path.join(category_dir, filename)
            
            # Create JSON structure matching existing format
            chunk_data = {
                "text": chunk["text"],
                "title": chunk["title"],
                "chunk_index": chunk_index,
                "metadata": {
                    "source": chunk["title"],
                    "type": "content",
                    "category": category,
                    "timestamp": time.time()
                }
            }
            
            # Save as JSON
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(chunk_data, f, indent=2, ensure_ascii=False)
    
    def save_raw_html(self, html: str, title: str):
        """
        Save raw HTML content.
        
        Args:
            html: HTML content
            title: Page title
        """
        # Create directory if it doesn't exist
        os.makedirs(self.raw_html_dir, exist_ok=True)
        
        # Save raw HTML
        filename = f"{self.clean_filename(title)}.html"
        filepath = os.path.join(self.raw_html_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
    
    def _file_exists(self, title: str, category: str) -> bool:
        """
        Check if a file for the given title already exists in the specified category.
        
        Args:
            title: Page title
            category: Category name
            
        Returns:
            True if file exists, False otherwise
        """
        if category not in CONTENT_CATEGORIES:
            logger.warning(f"Unknown category: {category}")
            return False
            
        category_dir = CONTENT_CATEGORIES[category]
        if not os.path.exists(category_dir):
            return False
            
        clean_title = self.clean_filename(title)
        
        # Check if any files with this title exist
        for file in os.listdir(category_dir):
            if file.startswith(f"{clean_title}") and (file.endswith(".txt") or file.endswith(".json")):
                return True
                
        return False
    
    def scrape_page(self, url):
        """Scrape a single wiki page"""
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                # Normalize URL
                normalized_url = self._normalize_url(url)
                
                # Skip if already visited
                if normalized_url in self.visited_urls:
                    self.logger.info(f"Skipping already visited URL: {url}")
                    self.stats['skipped_pages'] += 1
                    return False
                    
                # Skip non-content pages
                if self._is_non_content_page(normalized_url):
                    self.logger.info(f"Skipping non-content page: {url}")
                    self.stats['skipped_pages'] += 1
                    return False
                
                # Extract title from URL
                title = self._extract_title_from_url(normalized_url)
                if not title:
                    self.logger.warning(f"Could not extract title from URL: {url}")
                    self.stats['failed_pages'] += 1
                    return False
                
                # Check if file already exists in any category
                filename = f"{title}.txt"
                if any(os.path.exists(os.path.join(cat_dir, filename)) 
                      for cat_dir in CONTENT_CATEGORIES.values()):
                    self.logger.info(f"File already exists: {filename}")
                    self.stats['skipped_pages'] += 1
                    return False
                
                # Make the request with proper headers and timeout
                try:
                    response = self.session.get(
                        url, 
                        headers=self.headers, 
                        timeout=30,
                        allow_redirects=True
                    )
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Request failed for {url} (attempt {attempt + 1}/{max_retries}): {str(e)}")
                        time.sleep(retry_delay)
                        continue
                    else:
                        self.logger.error(f"Request failed for {url} after {max_retries} attempts: {str(e)}")
                        self.stats['failed_pages'] += 1
                        return False
                
                # Parse the page
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract content
                content = self._extract_content(soup)
                if not content:
                    self.logger.warning(f"No content found for page: {url}")
                    self.stats['failed_pages'] += 1
                    return False
                
                # Determine category
                category = self._determine_category(soup, content)
                if not category:
                    self.logger.warning(f"Could not determine category for: {url}")
                    self.stats['failed_pages'] += 1
                    return False
                
                # Create category directory if it doesn't exist
                category_dir = CONTENT_CATEGORIES[category]
                os.makedirs(category_dir, exist_ok=True)
                
                # Save content
                filepath = os.path.join(category_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Update stats
                self.visited_urls.add(normalized_url)
                self.stats['successful_scrapes'] += 1
                self.logger.info(f"Successfully scraped: {url}")
                self.logger.info(f"  Category: {category}")
                self.logger.info(f"  File: {filename}")
                
                return True
                
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Error scraping {url} (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(retry_delay)
                    continue
                else:
                    self.logger.error(f"Error scraping {url} after {max_retries} attempts: {str(e)}")
                    self.stats['failed_pages'] += 1
                    return False
        
        return False

    def determine_category_dir(self, categories: List[str]) -> Optional[str]:
        """Determine the appropriate category directory for a page."""
        # Map of keywords to directories
        category_mapping = {
            "quest": "quests",
            "skill": "skills",
            "minigame": "minigames",
            "diary": "diaries",
            "npc": "npcs",
            "monster": "bestiary",
            "item": "items",
            "activity": "activities",
            "mechanic": "mechanics",
            "achievement": "achievements",
            "collection": "collection",
            "tutorial": "tutorial"
        }
        
        # Check each category against our mapping
        for category in categories:
            category_lower = category.lower()
            for keyword, directory in category_mapping.items():
                if keyword in category_lower:
                    return os.path.join(self.output_dir, directory)
                
                return None
    
    def scrape_category(self, category):
        """Scrape all pages in a category"""
        try:
            self.logger.info(f"Scraping category: {category}")
            
            # Get all pages in the category
            pages = self.get_category_pages(category)
            
            # Filter out already visited pages and non-content pages
            missing_pages = []
            skipped_pages = []
            for page in pages:
                # Normalize URL to prevent duplicates
                normalized_url = self._normalize_url(page)
                
                # Skip if already visited
                if normalized_url in self.visited_urls:
                    skipped_pages.append(page)
                    continue
                    
                # Skip non-content pages
                if self._is_non_content_page(normalized_url):
                    skipped_pages.append(page)
                    continue
                    
                # Check if file exists in any category
                title = self._extract_title_from_url(normalized_url)
                if title:
                    filename = f"{title}.txt"
                    if any(os.path.exists(os.path.join(cat_dir, filename)) 
                          for cat_dir in CONTENT_CATEGORIES.values()):
                        skipped_pages.append(page)
                        continue
                
                missing_pages.append(page)
            
            # Log progress
            total_pages = len(pages)
            new_pages = len(missing_pages)
            skipped = len(skipped_pages)
            self.logger.info(f"Category {category}:")
            self.logger.info(f"  Total pages found: {total_pages}")
            self.logger.info(f"  Already scraped: {skipped}")
            self.logger.info(f"  New pages to scrape: {new_pages}")
            
            if not missing_pages:
                self.logger.info(f"No new pages to scrape in category {category}")
                return
            
            # Scrape missing pages
            for page in missing_pages:
                if self.scrape_page(page):
                    self.stats['successful_scrapes'] += 1
                    self.save_progress()
                    time.sleep(0.5)  # Small delay between requests
                else:
                    self.stats['failed_pages'] += 1
            
        except Exception as e:
            self.logger.error(f"Error scraping category {category}: {str(e)}")
            self.stats['failed_categories'] += 1

    def _normalize_url(self, url):
        """Normalize URL to prevent duplicates"""
        # Remove trailing slashes
        url = url.rstrip('/')
        
        # Convert to lowercase
        url = url.lower()
        
        # Remove URL encoding
        url = url.split('?')[0]
        
        # Remove fragment identifiers
        url = url.split('#')[0]
        
        return url

    def _is_non_content_page(self, url):
        """Check if URL is for a non-content page"""
        non_content_patterns = [
            r'/special:',
            r'/category:',
            r'/file:',
            r'/template:',
            r'/user:',
            r'/user_talk:',
            r'/talk:',
            r'/help:',
            r'/update:',
            r'/\d{1,2}_\w+$',  # Dates like "4_January"
            r'/\d{4}$',        # Years like "2001"
            r'/archive',
            r'/index',
            r'/main_page',
            r'/random',
            r'/recent_changes',
            r'/what_links_here',
            r'/wiki$',
            r'/wiki/$',
            r'/wiki/index\.php$'
        ]
        
        url_lower = url.lower()
        return any(re.search(pattern, url_lower, re.IGNORECASE) for pattern in non_content_patterns)

    def _extract_title_from_url(self, url):
        """Extract title from URL"""
        # Remove base URL if present
        if self.base_url in url:
            url = url[len(self.base_url):]
            
        # Remove leading/trailing slashes
        url = url.strip('/')
        
        # Split on slashes and take the last part
        parts = url.split('/')
        if not parts:
            return None
    
        title = parts[-1]
        
        # Remove file extension if present
        title = title.split('.')[0]
        
        # URL decode
        title = urllib.parse.unquote(title)
        
        # Replace underscores with spaces
        title = title.replace('_', ' ')
        
        return title

    def print_stats(self):
        """Print scraping statistics"""
        self.logger.info("\nScraping Statistics:")
        self.logger.info("===================")
        self.logger.info(f"Total URLs processed: {len(self.visited_urls)}")
        self.logger.info(f"Successful scrapes: {self.stats['successful_scrapes']}")
        self.logger.info(f"Failed pages: {self.stats['failed_pages']}")
        self.logger.info(f"Skipped pages: {self.stats['skipped_pages']}")
        self.logger.info(f"Failed categories: {self.stats['failed_categories']}")
        
        # Count files in each category
        self.logger.info("\nFiles by Category:")
        self.logger.info("=================")
        for category, directory in CONTENT_CATEGORIES.items():
            if os.path.exists(directory):
                files = len([f for f in os.listdir(directory) if f.endswith('.txt')])
                self.logger.info(f"{category}: {files} files")
            else:
                self.logger.info(f"{category}: 0 files")
        
        # Calculate completion percentage
        total_files = sum(len([f for f in os.listdir(d) if f.endswith('.txt')]) 
                         for d in CONTENT_CATEGORIES.values() 
                         if os.path.exists(d))
        self.logger.info(f"\nTotal files scraped: {total_files}")
        
        # Save final stats
        self.save_progress()

    def run(self, force: bool = False):
        """
        Run the scraper for all categories.
        
        Args:
            force: Whether to force re-scraping of existing pages
        """
        logger.info("Starting OSRS Wiki scraper")
        
        # If force flag is set, clear existing files
        if force:
            logger.info("Force flag set, will re-scrape existing pages")
            self.existing_files = set()
        
        try:
            for category in CATEGORIES:
                self.scrape_category(category)
            
            self.print_stats()
            logger.info("Scraping complete")
            
        except KeyboardInterrupt:
            logger.info("Scraping interrupted by user")
            self.save_progress()
            self.print_stats()
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            self.save_progress()
            self.print_stats()

    def get_all_quests(self):
        """Get a list of all quests from both the quest list pages and category pages."""
        quest_urls = set()
        
        # Get quests from quest list pages
        for page in QUEST_PAGES:
            url = f"{BASE_URL}/w/{page}"
            try:
                response = self.session.get(url, headers={"User-Agent": "RuneGPT Knowledge Engine/1.0 (Educational Project)"})
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Find quest links in tables and lists
                for link in soup.find_all("a"):
                    href = link.get("href", "")
                    if href.startswith("/w/") and not any(x in href.lower() for x in ["category:", "file:", "template:", "#"]):
                        quest_urls.add(href.replace("/w/", ""))
                    
            except Exception as e:
                logger.error(f"Failed to get quests from {page}: {str(e)}")
            
        # Get quests from category pages
        for category in ["Category:Free-to-play_quests", "Category:Members'_quests"]:
            url = f"{BASE_URL}/w/{category}"
            try:
                response = self.session.get(url, headers={"User-Agent": "RuneGPT Knowledge Engine/1.0 (Educational Project)"})
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Find quest links in category pages
                for link in soup.find_all("a"):
                    href = link.get("href", "")
                    if href.startswith("/w/") and not any(x in href.lower() for x in ["category:", "file:", "template:", "#"]):
                        quest_urls.add(href.replace("/w/", ""))
                    
            except Exception as e:
                logger.error(f"Failed to get quests from {category}: {str(e)}")
            
        return quest_urls

    def scrape_optimal_quests(self):
        """
        Scrape quests in the optimal order from the OSRS wiki.
        """
        logger.info("Starting optimal quest scraping")
        
        # Create optimal quests directory
        optimal_dir = os.path.join(self.output_dir, "quests", "optimal")
        os.makedirs(optimal_dir, exist_ok=True)
        
        # Get the optimal quest guide page
        url = f"{BASE_URL}/w/Optimal_quest_guide"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find the quest order table
            quest_table = None
            for table in soup.find_all("table", class_="wikitable"):
                if "Quest" in table.get_text() and "Order" in table.get_text():
                    quest_table = table
                    break
            
            if not quest_table:
                logger.error("Could not find quest order table")
                return
            
            # Extract quest order
            quest_order = []
            for row in quest_table.find_all("tr")[1:]:  # Skip header row
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:  # Ensure we have at least quest name and notes
                    quest_name = cells[0].get_text(strip=True)
                    notes = cells[1].get_text(strip=True).lower()
                    
                    # Skip optional quests
                    if "optional" in notes or "not recommended" in notes:
                        logger.info(f"Skipping optional quest: {quest_name}")
                        continue
                    
                    # Get quest link
                    quest_link = cells[0].find("a")
                    if quest_link and "href" in quest_link.attrs:
                        quest_url = quest_link["href"].replace("/w/", "")
                        quest_order.append((quest_name, quest_url))
            
            logger.info(f"Found {len(quest_order)} quests in optimal order")
            
            # Scrape each quest
            for quest_name, quest_url in tqdm(quest_order, desc="Scraping optimal quests"):
                # Check if already scraped
                clean_name = self.clean_filename(quest_name)
                output_file = os.path.join(optimal_dir, f"{clean_name}.txt")
                
                if os.path.exists(output_file) and not self.force_rescrape:
                    logger.debug(f"Skipping {quest_name} - already scraped")
                    self.stats["skipped_pages"] += 1
                    continue
                
                # Scrape quest page
                full_url = f"{BASE_URL}/w/{quest_url}"
                try:
                    response = self.session.get(full_url)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # Get main content
                    content = soup.find(id="mw-content-text")
                    if not content:
                        logger.warning(f"No content found for {quest_name}")
                        self.stats["failed_pages"] += 1
                        continue
                    
                    # Remove unwanted elements
                    for element in content.find_all(["script", "style"]):
                        element.decompose()
                    
                    # Remove infoboxes and navboxes
                    for element in content.find_all(class_=["infobox", "navbox"]):
                        element.decompose()
                    
                    # Clean and save content
                    text = content.get_text()
                    text = self.clean_text(text)
                    
                    # Add source URL as comment
                    text = f"# Source: {full_url}\n\n{text}"
                    
                    # Save to file
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(text)
                    
                    self.stats["successful_pages"] += 1
                    logger.info(f"Successfully scraped {quest_name}")
                    
            # Be nice to the wiki server
            time.sleep(1)
    
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 404:
                        logger.warning(f"Quest page not found: {quest_name}")
                    else:
                        logger.error(f"HTTP error scraping {quest_name}: {str(e)}")
                    self.stats["failed_pages"] += 1
                    
                except Exception as e:
                    logger.error(f"Error scraping {quest_name}: {str(e)}")
                    self.stats["failed_pages"] += 1
            
            # Print statistics
            logger.info("\nOptimal Quest Scraping Statistics:")
            logger.info(f"Total quests found: {len(quest_order)}")
            logger.info(f"Successfully scraped: {self.stats['successful_pages']}")
            logger.info(f"Skipped (already exists): {self.stats['skipped_pages']}")
            logger.info(f"Failed: {self.stats['failed_pages']}")
            
        except Exception as e:
            logger.error(f"Error scraping optimal quest guide: {str(e)}")

    def _get_category_from_content(self, content: str, metadata: Dict[str, Any]) -> str:
        """
        Determine the appropriate category for content based on its metadata and content.
        
        Args:
            content: The page content
            metadata: The page metadata
            
        Returns:
            Category name
        """
        # Check categories in metadata first
        categories = metadata.get("categories", [])
        for category in categories:
            category = category.lower()
            if "quest" in category:
                return "quests"
            elif "skill" in category:
                return "skills"
            elif "minigame" in category:
                return "minigames"
            elif "diary" in category or "achievement diary" in category:
                return "diaries"
            elif "npc" in category or "monster" in category:
                return "npcs"
            elif "mechanic" in category:
                return "mechanics"
        
        # Check content for keywords
        content_lower = content.lower()
        if "quest points" in content_lower or "quest requirements" in content_lower:
            return "quests"
        elif "experience" in content_lower and any(skill in content_lower for skill in ["attack", "strength", "defence", "magic", "ranged", "prayer"]):
            return "skills"
        elif "minigame" in content_lower:
            return "minigames"
        elif "diary" in content_lower or "achievement diary" in content_lower:
            return "diaries"
        elif "combat level" in content_lower or "hitpoints" in content_lower:
            return "npcs"
        elif "game mechanic" in content_lower or "game engine" in content_lower:
            return "mechanics"
        
        # Default to mechanics if no clear category
        return "mechanics"

    def process_raw_html(self, filename: str) -> bool:
        """
        Process a raw HTML file and move its content to the appropriate category.
        
        Args:
            filename: Name of the HTML file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if filename in self.processed_raw_files:
            return True
            
        filepath = os.path.join(self.raw_html_dir, filename)
        if not os.path.exists(filepath):
            return False
            
        try:
            # Read the HTML file
            with open(filepath, "r", encoding="utf-8") as f:
                html = f.read()
            
            # Parse the HTML
            soup = BeautifulSoup(html, "html.parser")
            
            # Extract content and metadata
            content, metadata = self.extract_main_content(soup)
            if not content:
                logger.warning(f"No content found in {filename}")
                return False
            
            # Determine appropriate category
            category = self._get_category_from_content(content, metadata)
            
            # Get clean title from filename
            title = filename.replace(".html", "")
            
            # Save content to appropriate category
            clean_name = self.clean_filename(title)
            category_dir = self._get_category_dir(category)
            output_file = os.path.join(category_dir, f"{clean_name}.txt")
            
            # Add source URL as comment if available
            if "url" in metadata:
                content = f"# Source: {metadata['url']}\n\n{content}"
            
            # Save the content
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Mark as processed
            self.processed_raw_files.add(filename)
            
            # Delete the raw HTML file
            os.remove(filepath)
            
            logger.info(f"Processed {filename} into {category}/{clean_name}.txt")
            return True
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            return False

    def cleanup_raw_html(self):
        """Clean up the raw_html directory by processing all files."""
        logger.info("Starting raw_html cleanup")
        
        if not os.path.exists(self.raw_html_dir):
            logger.info("No raw_html directory found")
            return
        
        # Get list of HTML files
        html_files = [f for f in os.listdir(self.raw_html_dir) if f.endswith(".html")]
        
        if not html_files:
            logger.info("No HTML files to process")
            return
        
        logger.info(f"Found {len(html_files)} HTML files to process")
        
        # Process each file
        for filename in tqdm(html_files, desc="Processing raw HTML files"):
            self.process_raw_html(filename)
        
        # Remove raw_html directory if empty
        if not os.listdir(self.raw_html_dir):
            os.rmdir(self.raw_html_dir)
            logger.info("Removed empty raw_html directory")
        
        logger.info("Raw HTML cleanup complete")

    def organize_content(self):
        """Organize existing content into appropriate categories."""
        logger.info("Starting content organization")
        
        # Create all category directories
        for category_dir in CONTENT_CATEGORIES.values():
            os.makedirs(category_dir, exist_ok=True)
        
        # Process raw HTML files first
        self.cleanup_raw_html()
        
        # Walk through the output directory
        for root, _, files in os.walk(self.output_dir):
            for file in files:
                # Skip already processed files and non-content files
                if not (file.endswith(".txt") or file.endswith(".json")):
                    continue
                    
                if "equipment" in root:
                    continue  # Skip equipment data
                    
                filepath = os.path.join(root, file)
                
                try:
                    # Read the file
                    with open(filepath, "r", encoding="utf-8") as f:
                        if file.endswith(".json"):
                            data = json.load(f)
                            content = data.get("content", "")
                            metadata = data.get("metadata", {})
                        else:
                            content = f.read()
                            metadata = {}
                    
                    # Determine appropriate category
                    category = self._get_category_from_content(content, metadata)
                    
                    # Get the category directory
                    category_dir = self._get_category_dir(category)
                    
                    # Move file if it's not already in the right place
                    if root != category_dir:
                        new_filepath = os.path.join(category_dir, file)
                        shutil.move(filepath, new_filepath)
                        logger.info(f"Moved {file} to {category}")
                    
                except Exception as e:
                    logger.error(f"Error processing {file}: {str(e)}")
                    continue
        
        logger.info("Content organization complete")

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from a wiki page."""
        try:
            # Find the main content div
            content_div = soup.find('div', {'id': 'mw-content-text'})
            if not content_div:
                self.logger.warning("Main content div not found")
                return ""

            # Remove unwanted elements
            for element in content_div.find_all(['div', 'table'], class_=['mw-editsection', 'reference', 'noprint', 'navbox', 'toc']):
                element.decompose()

            # Extract text from paragraphs, lists, and headers
            content = []
            for element in content_div.find_all(['p', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                text = element.get_text(strip=True)
                if text and not text.startswith('Jump to') and not text.endswith('navigation'):
                    content.append(text)

            # Join content with newlines
            return '\n\n'.join(content)

        except Exception as e:
            self.logger.error(f"Error extracting content: {str(e)}")
            return ""

    def _determine_category(self, soup: BeautifulSoup, content: str) -> str:
        """Determine the appropriate category for a page."""
        try:
            # First check page categories
            categories = []
            category_div = soup.find('div', {'id': 'mw-normal-catlinks'})
            if category_div:
                for link in category_div.find_all('a'):
                    categories.append(link.get_text().lower())
            
            # Map categories to our content categories
            if any('quest' in cat for cat in categories):
                return 'quests'
            elif any('skill' in cat for cat in categories):
                return 'skills'
            elif any('minigame' in cat for cat in categories):
                return 'minigames'
            elif any('diary' in cat for cat in categories):
                return 'diaries'
            elif any('npc' in cat or 'monster' in cat for cat in categories):
                return 'npcs'
            elif any('item' in cat for cat in categories):
                return 'items'
            elif any('activity' in cat for cat in categories):
                return 'activities'
            elif any('bestiary' in cat for cat in categories):
                return 'bestiary'
            elif any('achievement' in cat for cat in categories):
                return 'achievements'
            elif any('collection' in cat for cat in categories):
                return 'collection'
            elif any('tutorial' in cat for cat in categories):
                return 'tutorial'
            
            # If no category found, check content for keywords
            content_lower = content.lower()
            if 'quest points' in content_lower or 'quest requirements' in content_lower:
                return 'quests'
            elif 'experience' in content_lower and any(skill in content_lower for skill in ['attack', 'strength', 'defence', 'magic', 'ranged', 'prayer']):
                return 'skills'
            elif 'minigame' in content_lower:
                return 'minigames'
            elif 'diary' in content_lower or 'achievement diary' in content_lower:
                return 'diaries'
            elif 'combat level' in content_lower or 'hitpoints' in content_lower:
                return 'npcs'
            elif 'item id' in content_lower or 'inventory icon' in content_lower:
                return 'items'
            
            # Default to mechanics if no clear category
            return 'mechanics'
            
        except Exception as e:
            self.logger.error(f"Error determining category: {str(e)}")
            return 'mechanics'  # Default category

def main():
    """Main entry point."""
    try:
        parser = argparse.ArgumentParser(description='OSRS Wiki Scraper')
        parser.add_argument('--categories', nargs='+', help='Specific categories to scrape')
        parser.add_argument('--force', action='store_true', help='Force re-scraping of existing pages')
        parser.add_argument('--output-dir', default=OUTPUT_DIR, help='Output directory for scraped content')
        parser.add_argument('--raw-html-dir', default=RAW_HTML_DIR, help='Directory for raw HTML content')
        parser.add_argument('--max-chunk-size', type=int, default=MAX_CHUNK_SIZE, help='Maximum chunk size for text splitting')
        
        args = parser.parse_args()
        
        # Initialize scraper with arguments
        scraper = WikiScraper(
            output_dir=args.output_dir,
            raw_html_dir=args.raw_html_dir,
            max_chunk_size=args.max_chunk_size
        )
        
        # Use specified categories or default to all
        categories_to_scrape = args.categories if args.categories else CATEGORIES
        
        # Create output directories if they don't exist
        os.makedirs(args.output_dir, exist_ok=True)
        os.makedirs(args.raw_html_dir, exist_ok=True)
        
        # Load existing progress
        scraper.load_progress()
        
        # Scrape each category
        for category in categories_to_scrape:
            if category not in CONTENT_CATEGORIES:
                logger.warning(f"Unknown category: {category}. Skipping...")
                continue
                
            logger.info(f"Scraping category: {category}")
            try:
                pages = scraper.get_category_pages(category)
                for page in pages:
                    scraper.scrape_page(page)
                    scraper.save_progress()
            except Exception as e:
                logger.error(f"Error scraping category {category}: {e}")
                continue
        
        scraper.print_stats()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main() 