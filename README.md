# ProductURLMapper

## Overview
ProductURLMapper is a specialized web scraping and product matching tool designed for e-commerce sites, with particular focus on German language optimization. The tool extracts URLs from a website, compares them with product titles from a CSV file, and identifies matches using multiple sophisticated matching strategies.

## Key Features
- **Multi-source URL Extraction**: Harvests URLs from robots.txt, sitemaps, and direct web crawling
- **Advanced German Language Support**: Handles German-specific challenges like umlauts, compound words, and specialized terminology
- **Multiple Matching Strategies**: Employs 11 different matching algorithms with confidence scoring
- **Health/Medical Terminology Optimization**: Special handling for health and wellness product terminology
- **Detailed Reporting**: Generates comprehensive CSV reports of matched and unmatched products
- **Confidence Scoring**: Rates each match with a confidence score to prioritize the most reliable matches

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup
1. Clone the repository:
```bash
git clone https://github.com/umerkhan95/ProductURLMapper.git
cd ProductURLMapper
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Command
```bash
python product_url_matcher.py https://www.example.com
```

### With Custom CSV File
```bash
python product_url_matcher.py https://www.example.com --csv_path /path/to/your/products.csv
```

### Required CSV Format
The CSV file must contain at least these columns:
- `Handle`: Product identifier/slug
- `Title`: Product title/name

## How It Works

### URL Collection
1. Extracts sitemap URLs from robots.txt
2. Parses sitemaps to collect product URLs
3. Crawls the website to find additional URLs

### Matching Strategies
The tool employs multiple matching strategies in sequence:

1. **Direct Handle Matching**: Exact match of product handle in URL
2. **Handle Word Matching**: Matching significant parts of multi-word handles
3. **Title Matching**: Matching normalized product title in URL
4. **Fuzzy Matching**: Finding significant words from title in URLs
5. **Collection URL Matching**: Checking for product handle in collection URLs
6. **Variant Product Detection**: Identifying product variants (e.g., with -1, -2 suffixes)
7. **German Language Handling**: Special processing for umlauts and German spellings
8. **Compound Word Handling**: Handling German compound words with various splitting approaches
9. **Special Case Handling**: Targeted matching for difficult German product names
10. **Path Component Analysis**: Analyzing all parts of URL paths for matches
11. **Health/Medical Terminology**: Specialized matching for health-related products

### Output Files
The tool generates three CSV files:
1. All extracted URLs from the website
2. Matched products with confidence scores
3. Unmatched products for further investigation

## Example
```bash
python product_url_matcher.py https://www.ory-berlin.de
```

Output:
```
Loaded 139 product titles from products_export_1.csv
Step 1: Extracting URLs from robots.txt...
Found 1 sitemap URLs in robots.txt
Step 2: Extracting URLs from sitemaps...
Parsing sitemap: https://www.ory-berlin.de/sitemap.xml
Found 366 URLs in sitemap
Step 3: Crawling the website...
Collected a total of 366 unique URLs
Found 125 matches between product titles and URLs
Saved results to CSV files
```

## License
MIT License

## Author
Umer Khan
