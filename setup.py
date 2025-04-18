from setuptools import setup, find_packages

setup(
    name="rune_gpt",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "beautifulsoup4",
        "numpy",
        "pandas",
        "scikit-learn",
        "transformers",
        "torch",
    ],
    python_requires=">=3.8",
) 