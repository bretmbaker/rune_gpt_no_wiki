# wiki_query_engine.py – Enhanced wiki fetcher for RuneGPT

import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from typing import Optional, Set, Dict
import time

class WikiQueryEngine:
    def __init__(self):
        self.visited_pages: Set[str] = set()
        self.cache: Dict[str, str] = {}
        self.max_retries = 2
        self.retry_delay = 1  # seconds
        
    def _clean_query(self, query: str) -> str:
        """Clean up the query to focus on key terms."""
        # Remove common suffixes that might lead to less relevant results
        query = re.sub(r'\b(step|walkthrough|guide|tutorial|how to|instructions)\b', '', query, flags=re.IGNORECASE)
        # Remove location modifiers that might confuse the search
        query = re.sub(r'\b(nearby|close|next to|around)\b', '', query, flags=re.IGNORECASE)
        # Add Tutorial Island context if not present
        if "tutorial island" not in query.lower():
            query = f"Tutorial Island {query}"
        return query.strip()
    
    def _is_bad_result(self, text: str) -> bool:
        """Check if the result appears to be unrelated or a search help page."""
        bad_indicators = [
            "search syntax",
            "cirrussearch",
            "search results",
            "did you mean",
            "no results found",
            "special:search",
            "search cheatsheet"
        ]
        return any(indicator in text.lower() for indicator in bad_indicators)
    
    def _get_page_content(self, url: str) -> Optional[str]:
        """Fetch and parse the content of a wiki page."""
        if url in self.visited_pages:
            return None
            
        self.visited_pages.add(url)
        try:
            page_res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            page_soup = BeautifulSoup(page_res.text, "html.parser")
            
            content_div = page_soup.find("div", class_="mw-parser-output")
            if not content_div:
                return None
                
            # Extract relevant content
            content = []
            
            # Get the first paragraph
            first_p = content_div.find("p")
            if first_p:
                content.append(first_p.get_text(strip=True))
            
            # Look for relevant sections
            sections = content_div.find_all(["h2", "h3", "p"])
            relevant_sections = ["Requirements", "Steps", "Guide", "Instructions", "Tutorial"]
            
            for section in sections:
                if section.name in ["h2", "h3"]:
                    section_title = section.get_text(strip=True)
                    if any(title in section_title for title in relevant_sections):
                        next_elem = section.find_next_sibling()
                        while next_elem and next_elem.name == "p":
                            content.append(next_elem.get_text(strip=True))
                            next_elem = next_elem.find_next_sibling()
            
            guide_text = "\n\n".join(content[:3])  # Limit to first 3 relevant pieces
            return guide_text if guide_text else None
            
        except Exception as e:
            print(f"[WikiEngine]: Error fetching page {url}: {str(e)}")
            return None
    
    def query_osrs_wiki(self, query: str, retry_count: int = 0) -> str:
        """Query the OSRS Wiki with smart retry logic and caching."""
        print(f"[WikiEngine]: Querying OSRS Wiki for: {query}")
        
        # Check cache first
        if query in self.cache:
            print("[WikiEngine]: Returning cached result")
            return self.cache[query]
        
        # Clean up the query
        clean_query = self._clean_query(query)
        
        # Use simplified search on OSRS wiki
        search_url = f"https://oldschool.runescape.wiki/w/Special:Search?search={urllib.parse.quote(clean_query)}"
        
        try:
            res = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Find all links that match our criteria
            result_links = soup.find_all("a", href=re.compile(r'^/w/(?!Special:|Help:|Category:|Template:|User:|Talk:|File:|MediaWiki:).*'))
            
            # Filter for Tutorial Island or relevant content
            relevant_links = []
            for link in result_links:
                href = link.get('href', '')
                title = link.get('title', '').lower()
                # Prioritize Tutorial Island content
                if 'tutorial_island' in href.lower():
                    relevant_links.insert(0, link)
                # Then specific skill or activity content
                elif any(term in title for term in ['fishing', 'cooking', 'mining', 'combat', 'magic']):
                    relevant_links.append(link)
            
            # If no specific matches, fall back to the first result
            if not relevant_links and result_links:
                relevant_links = [result_links[0]]
            
            if not relevant_links:
                if retry_count < self.max_retries:
                    print(f"[WikiEngine]: No results found, retrying with simplified query (attempt {retry_count + 1})")
                    time.sleep(self.retry_delay)
                    simplified_query = ' '.join(query.split()[-2:])  # Take last 2 words
                    return self.query_osrs_wiki(simplified_query, retry_count + 1)
                return "[WikiEngine]: No relevant wiki page found."
            
            # Use the first relevant link
            result_link = relevant_links[0]
            page_url = "https://oldschool.runescape.wiki" + result_link['href']
            print(f"[WikiEngine]: Found page: {page_url}")
            
            guide_text = self._get_page_content(page_url)
            if not guide_text:
                if retry_count < self.max_retries:
                    print(f"[WikiEngine]: No content found, retrying with next result (attempt {retry_count + 1})")
                    time.sleep(self.retry_delay)
                    if len(relevant_links) > 1:
                        next_link = relevant_links[1]
                        page_url = "https://oldschool.runescape.wiki" + next_link['href']
                        guide_text = self._get_page_content(page_url)
                
                if not guide_text:
                    return "[WikiEngine]: Page structure unexpected or already visited."
            
            # Check if we got a bad result
            if self._is_bad_result(guide_text):
                if retry_count < self.max_retries:
                    print(f"[WikiEngine]: Bad result detected, retrying with simplified query (attempt {retry_count + 1})")
                    time.sleep(self.retry_delay)
                    simplified_query = ' '.join(clean_query.split()[:3])  # Take first 3 words
                    return self.query_osrs_wiki(simplified_query, retry_count + 1)
                else:
                    return "[WikiEngine]: Unable to find relevant information after multiple attempts."
            
            # Cache the successful result
            self.cache[query] = guide_text
            return guide_text
            
        except Exception as e:
            print(f"[WikiEngine]: Error during wiki query: {str(e)}")
            return "[WikiEngine]: Error occurred while querying the wiki."

# Create a singleton instance
wiki_engine = WikiQueryEngine()

# For backward compatibility
def query_osrs_wiki(query: str) -> str:
    return wiki_engine.query_osrs_wiki(query)

# Test
if __name__ == "__main__":
    print(query_osrs_wiki("Tutorial Island Gielinor Guide"))
