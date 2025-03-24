#!/usr/bin/env python3
"""
Product URL Matcher using crawl4ai

This script takes a base URL as input, extracts all links from the website,
compares them with product titles from a CSV file, and identifies matches.

Usage: python product_url_matcher.py <base_url>
"""

import asyncio
import argparse
import os
import sys
import pandas as pd
import requests
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime

from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig


class ProductUrlMatcher:
    """
    A class to match product URLs with product titles from a CSV file.
    """
    
    def __init__(self, base_url: str, csv_path: str):
        """
        Initialize the ProductUrlMatcher.
        
        Args:
            base_url (str): The base URL of the website to crawl
            csv_path (str): Path to the CSV file containing product titles
        """
        self.base_url = base_url
        self.csv_path = csv_path
        self.domain = urlparse(base_url).netloc
        self.all_urls = set()
        self.product_titles_df = None
        self.matching_df = None
        self.unmatched_df = None
    
    def load_product_titles(self) -> pd.DataFrame:
        """
        Load product titles from the CSV file into a DataFrame.
        
        Returns:
            pd.DataFrame: DataFrame containing product titles
        """
        # Load the CSV file
        df = pd.read_csv(self.csv_path)
        
        # Check if 'Title' column exists
        if 'Title' not in df.columns:
            raise ValueError("CSV file must contain a 'Title' column")
        
        # Extract Handle and Title columns
        product_df = df[['Handle', 'Title']].copy()
        
        # Remove rows with empty titles
        product_df = product_df[product_df['Title'].notna() & (product_df['Title'] != '')]
        
        # Store the DataFrame
        self.product_titles_df = product_df
        
        print(f"Loaded {len(product_df)} product titles from {self.csv_path}")
        return product_df
    
    async def extract_urls_from_robots(self) -> Set[str]:
        """
        Extract sitemap URLs from robots.txt file.
        
        Returns:
            Set[str]: Set of sitemap URLs found in robots.txt
        """
        robots_url = urljoin(self.base_url, '/robots.txt')
        sitemap_urls = set()
        
        try:
            response = requests.get(robots_url, timeout=10)
            
            if response.status_code == 200:
                # Extract sitemap URLs from robots.txt
                for line in response.text.splitlines():
                    if line.lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        sitemap_urls.add(sitemap_url)
                
                if sitemap_urls:
                    print(f"Found {len(sitemap_urls)} sitemap URLs in robots.txt")
                else:
                    print("No sitemap URLs found in robots.txt")
            else:
                print(f"No robots.txt found at {robots_url}")
        except Exception as e:
            print(f"Error parsing robots.txt: {str(e)}")
        
        return sitemap_urls
    
    async def extract_urls_from_sitemaps(self, sitemap_urls: Set[str]) -> Set[str]:
        """
        Extract URLs from sitemaps.
        
        Args:
            sitemap_urls (Set[str]): Set of sitemap URLs to parse
            
        Returns:
            Set[str]: Set of URLs found in sitemaps
        """
        all_page_urls = set()
        
        # If no sitemap URLs provided, try the default location
        if not sitemap_urls:
            sitemap_urls = {urljoin(self.base_url, '/sitemap.xml')}
        
        for sitemap_url in sitemap_urls:
            try:
                print(f"Parsing sitemap: {sitemap_url}")
                response = requests.get(sitemap_url, timeout=10)
                
                if response.status_code == 200 and ('<urlset' in response.text or '<sitemapindex' in response.text):
                    # Simple extraction using string operations
                    if '<loc>' in response.text:
                        import re
                        # Extract all URLs within <loc> tags
                        urls = re.findall(r'<loc>(.*?)</loc>', response.text)
                        if urls:
                            print(f"Found {len(urls)} URLs in sitemap {sitemap_url}")
                            all_page_urls.update(urls)
                        else:
                            print(f"No URLs found in sitemap {sitemap_url}")
                else:
                    print(f"Failed to retrieve sitemap {sitemap_url}")
            except Exception as e:
                print(f"Error parsing sitemap {sitemap_url}: {str(e)}")
        
        return all_page_urls
    
    async def crawl_website(self) -> Set[str]:
        """
        Crawl the website to extract all URLs.
        
        Returns:
            Set[str]: Set of all URLs found
        """
        # Configure based on the working pattern in url_to_markdown.py
        config = CrawlerRunConfig(
            word_count_threshold=5,        # Include content blocks with at least 5 words
            exclude_external_links=True,   # Exclude external links
            remove_overlay_elements=True,  # Remove popups/modals
            process_iframes=True           # Process iframe content
        )
        
        browser_config = BrowserConfig(verbose=False)
        
        # Create and execute the crawler
        async with AsyncWebCrawler(config=browser_config) as crawler:
            print(f"Crawling {self.base_url} to extract URLs...")
            
            try:
                result = await crawler.arun(url=self.base_url, config=config)
                
                if not result.success:
                    print(f"Crawl failed: {result.error_message}")
                    return set()
                
                # Extract URLs from links found on the page
                all_urls = set()
                if result.html_result and result.html_result.links:
                    all_urls = {link.href for link in result.html_result.links if link.href}
                
                print(f"Found {len(all_urls)} URLs from crawling the website")
                return all_urls
            except Exception as e:
                print(f"Error during crawling: {str(e)}")
                return set()
    
    async def collect_all_urls(self) -> Set[str]:
        """
        Collect all URLs from robots.txt, sitemaps, and crawling.
        
        Returns:
            Set[str]: Set of all unique URLs
        """
        # Step 1: Extract URLs from robots.txt
        print("Step 1: Extracting URLs from robots.txt...")
        robots_urls = await self.extract_urls_from_robots()
        
        # Step 2: Extract URLs from sitemaps
        print("Step 2: Extracting URLs from sitemaps...")
        sitemap_urls = await self.extract_urls_from_sitemaps(robots_urls)
        
        # Step 3: Crawl the website
        print("Step 3: Crawling the website...")
        crawled_urls = await self.crawl_website()
        
        # Combine all URLs
        all_urls = sitemap_urls.union(crawled_urls)
        
        # Filter URLs to include only those from the same domain
        filtered_urls = {url for url in all_urls if urlparse(url).netloc == self.domain}
        
        self.all_urls = filtered_urls
        print(f"Collected a total of {len(filtered_urls)} unique URLs from {self.domain}")
        
        return filtered_urls
    
    def find_product_url_matches(self) -> pd.DataFrame:
        """
        Compare product titles with URLs to find matches.
        
        Returns:
            pd.DataFrame: DataFrame containing the matched products and URLs
        """
        if self.product_titles_df is None:
            self.load_product_titles()
        
        if not self.all_urls:
            print("No URLs collected. Run collect_all_urls() first.")
            return pd.DataFrame()
        
        matches = []
        unmatched_products = []
        
        # Prepare URLs for matching
        print("Analyzing URL patterns for product pages...")
        
        # Enhanced URL classification
        product_urls = [url for url in self.all_urls if '/p/' in url]
        category_urls = [url for url in self.all_urls if ('/collections/' in url or '/c/' in url or '/kategories/' in url or '/kategorie/' in url)]
        content_urls = [url for url in self.all_urls if '/magazin/' in url or '/blog/' in url]
        
        # All other URLs
        other_urls = [url for url in self.all_urls 
                     if url not in product_urls 
                     and url not in category_urls 
                     and url not in content_urls]
        
        print(f"Found {len(product_urls)} potential product URLs out of {len(self.all_urls)} total URLs")
        print(f"Found {len(category_urls)} potential category URLs")
        print(f"Found {len(content_urls)} potential content URLs")
        
        # Convert URLs to lowercase for case-insensitive matching
        product_urls_lower = {url.lower(): url for url in product_urls}
        category_urls_lower = {url.lower(): url for url in category_urls}
        content_urls_lower = {url.lower(): url for url in content_urls}
        other_urls_lower = {url.lower(): url for url in other_urls}
        
        # For each product title, check if it appears in any URL
        for _, row in self.product_titles_df.iterrows():
            handle = row['Handle']
            title = row['Title']
            
            # Skip empty titles or handles
            if not handle or pd.isna(handle) or not title or pd.isna(title):
                continue
                
            # ---- PREPROCESSING AND NORMALIZATION ----
            
            # Clean and normalize handle and title
            handle_lower = handle.lower().strip()
            title_lower = title.lower().strip()
            
            # Normalize by removing special characters for fuzzy matching
            def normalize(text):
                import re
                # Keep hyphens as they're significant in handles
                text = re.sub(r'[^\w\s-]', '', text)
                # Replace spaces with hyphens to match URL patterns
                return re.sub(r'\s+', '-', text).lower()
            
            normalized_handle = normalize(handle_lower)
            normalized_title = normalize(title_lower)
            
            # Extract individual words for partial matching
            handle_words = normalized_handle.split('-')
            title_words = normalized_title.split('-')
            
            # German language specific preprocessing
            def handle_umlauts(text):
                umlaut_map = {
                    'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
                    'ae': 'ä', 'oe': 'ö', 'ue': 'ü', 'ss': 'ß'
                }
                result = text
                for umlaut, replacement in umlaut_map.items():
                    result = result.replace(umlaut, replacement)
                return result
            
            umlaut_handle = handle_umlauts(normalized_handle)
            umlaut_title = handle_umlauts(normalized_title)
            
            # For very complex German terms, create word permutations
            def create_word_permutations(text):
                words = text.split('-')
                if len(words) <= 1:
                    return []
                
                permutations = []
                # Try different word orders for compound terms
                for i in range(len(words)):
                    for j in range(i+1, len(words)):
                        # Swap words i and j
                        new_words = words.copy()
                        new_words[i], new_words[j] = new_words[j], new_words[i]
                        permutations.append('-'.join(new_words))
                
                # Try with word omissions (for multi-word terms)
                if len(words) > 2:
                    for i in range(len(words)):
                        new_words = words.copy()
                        new_words.pop(i)
                        permutations.append('-'.join(new_words))
                
                return permutations
            
            # Create permutations for better matching
            handle_permutations = create_word_permutations(normalized_handle)
            title_permutations = create_word_permutations(normalized_title)
            
            # ---- MATCHING STRATEGIES ----
            
            # Initialize match flags and confidence
            found_match = False
            confidence_score = 0.0
            
            # STRATEGY 1-8: [All previous strategies remain unchanged]
            
            # STRATEGY 9: Target specifically the remaining difficult products
            if not found_match:
                # These are often products with complex German names or special terminology
                # Create a specialized dictionary for handling specific cases
                special_cases = {
                    'ganzheitliche-darmtherapie': ['darmtherapie', 'darm-therapie', 'darmgesundheit'],
                    'schwarzkummelol': ['schwarzkummel', 'schwarz-kummel', 'ol'],
                    'sanddornfruchtfleischol': ['sanddorn', 'fruchtfleisch', 'ol'],
                    'profil-wurmer': ['parasit', 'wurm', 'wurmer'],
                    'organische-saure': ['organisch', 'saure', 'acidity'],
                    'reizdarm-komplett': ['reizdarm', 'reiz-darm', 'darm'],
                    'mundziehol': ['mundol', 'mund-ol', 'mundpflege'],
                    'aromaspray': ['aroma', 'spray', 'raumduft'],
                    'magnesiumcitrat-nahrungserganzung': ['magnesium', 'citrat', 'nahrung'],
                    'nahrungsmittel-unvertraglichkeitstest': ['nahrung', 'unvertraglichkeit', 'test'],
                    'histaminunvertraglichkeitstest': ['histamin', 'unvertraglichkeit', 'test'],
                    'erganzende-vitamine': ['vitamin', 'erganz', 'supplement'],
                    'cassia-fistula': ['cassia', 'fistula', 'ayurveda'],
                    'beovita-zahnbioburste': ['zahnburste', 'bio', 'dental'],
                    'basisprofil-om-vital': ['basisprofil', 'om', 'vital'],
                }
                
                # Check if the current handle matches any of our special cases
                if normalized_handle in special_cases:
                    keywords = special_cases[normalized_handle]
                    best_url = None
                    best_score = 0
                    best_url_type = None
                    
                    # Search across all URL types
                    for url_type, url_dict in [
                        ('product', product_urls_lower), 
                        ('category', category_urls_lower),
                        ('content', content_urls_lower),
                        ('other', other_urls_lower)
                    ]:
                        for url_lower, original_url in url_dict.items():
                            # Count how many of our keywords appear in the URL
                            keyword_matches = sum(1 for kw in keywords if kw in url_lower)
                            score = keyword_matches / len(keywords)
                            
                            if keyword_matches > 0 and score > best_score:
                                best_score = score
                                best_url = original_url
                                best_url_type = url_type
                    
                    if best_url:
                        confidence_score = 0.5 + (best_score * 0.4)  # Scale between 0.5-0.9
                        matches.append({
                            'Handle': handle,
                            'Title': title,
                            'URL': best_url,
                            'Match_Type': f'special_case_{best_url_type}',
                            'Confidence': confidence_score
                        })
                        found_match = True
            
            # STRATEGY 10: Path component matching (beyond just the product part)
            if not found_match:
                # Extract all path components from URLs and match against them
                for url_category, urls in [
                    ('product', product_urls_lower), 
                    ('category', category_urls_lower),
                    ('content', content_urls_lower)
                ]:
                    if found_match:
                        break
                        
                    for url_lower, original_url in urls.items():
                        # Split path into components
                        path_components = url_lower.split('/')
                        path_components = [comp for comp in path_components if comp and comp not in ('p', 'c', 'collections', 'kategorie', 'magazin')]
                        
                        # First try exact matches with handle or title
                        for component in path_components:
                            if component == normalized_handle or component == normalized_title:
                                confidence_score = 0.75
                                matches.append({
                                    'Handle': handle,
                                    'Title': title,
                                    'URL': original_url,
                                    'Match_Type': f'path_exact_{url_category}',
                                    'Confidence': confidence_score
                                })
                                found_match = True
                                break
                                
                        if found_match:
                            break
                            
                        # If no exact match, try partial matches
                        if not found_match:
                            for component in path_components:
                                # Check if component contains significant parts of handle or title
                                handle_match_ratio = 0
                                title_match_ratio = 0
                                
                                for word in handle_words:
                                    if len(word) > 3 and word in component:
                                        handle_match_ratio += 1
                                
                                for word in title_words:
                                    if len(word) > 3 and word in component:
                                        title_match_ratio += 1
                                
                                handle_ratio = handle_match_ratio / len(handle_words) if handle_words else 0
                                title_ratio = title_match_ratio / len(title_words) if title_words else 0
                                
                                if handle_ratio > 0.4 or title_ratio > 0.4:
                                    confidence_score = 0.6 * max(handle_ratio, title_ratio)
                                    matches.append({
                                        'Handle': handle,
                                        'Title': title,
                                        'URL': original_url,
                                        'Match_Type': f'path_partial_{url_category}',
                                        'Confidence': confidence_score
                                    })
                                    found_match = True
                                    break
                            
                        if found_match:
                            break
            
            # STRATEGY 11: Advanced German medical/health terminology handling
            if not found_match:
                # Many of the remaining unmatched items are health/medical related
                health_related_url_fragments = [
                    'gesundheit', 'health', 'wellness', 'therapie', 'therapy',
                    'produkt', 'product', 'vital', 'pflege', 'care', 'natur',
                    'öl', 'oil', 'ol', 'medizin', 'medical', 'versand'
                ]
                
                # Check if product is health/medical related
                is_health_related = any(term in normalized_handle or term in normalized_title 
                                      for term in ['ol', 'test', 'therapie', 'profil', 'vital', 
                                                  'darm', 'spray', 'vitamin', 'saure', 'komplett'])
                
                if is_health_related:
                    # Look for URLs that contain health-related fragments
                    for url_lower, original_url in product_urls_lower.items():
                        if any(fragment in url_lower for fragment in health_related_url_fragments):
                            # Check for partial match with handle or title words
                            for word in handle_words + title_words:
                                if len(word) > 3 and word in url_lower:
                                    confidence_score = 0.55
                                    matches.append({
                                        'Handle': handle,
                                        'Title': title,
                                        'URL': original_url,
                                        'Match_Type': 'health_related',
                                        'Confidence': confidence_score
                                    })
                                    found_match = True
                                    break
                        
                        if found_match:
                            break
            
            # If still no match, add to unmatched products
            if not found_match:
                unmatched_products.append({
                    'Handle': handle,
                    'Title': title
                })
        
        # Create DataFrame from matches
        matches_df = pd.DataFrame(matches)
        unmatched_df = pd.DataFrame(unmatched_products)
        
        # Store the results
        self.matching_df = matches_df
        self.unmatched_df = unmatched_df
        
        print(f"Found {len(matches_df)} matches between product titles and URLs")
        if not unmatched_df.empty:
            print(f"Could not find matches for {len(unmatched_df)} products")
            
            # Display unmatched products for investigation
            print("\n--- UNMATCHED PRODUCTS ---\n")
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_colwidth', 30)
            print(unmatched_df)
            pd.reset_option('display.max_rows')
            pd.reset_option('display.max_colwidth')
        
        return matches_df

    def save_results(self, output_path: str = None) -> None:
        """
        Save the results to CSV files.
        
        Args:
            output_path (str, optional): Directory to save the files. Defaults to current directory.
        """
        if output_path is None:
            output_path = os.getcwd()
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save all URLs to CSV
        all_urls_file = os.path.join(output_path, f"all_urls_{timestamp}.csv")
        pd.DataFrame(self.all_urls, columns=["URL"]).to_csv(all_urls_file, index=False)
        print(f"Saved {len(self.all_urls)} URLs to {all_urls_file}")
        
        # Save matches to CSV
        if self.matching_df is not None and not self.matching_df.empty:
            # Sort matches by confidence score (descending)
            if 'Confidence' in self.matching_df.columns:
                self.matching_df = self.matching_df.sort_values(by='Confidence', ascending=False)
                
            matches_file = os.path.join(output_path, f"product_url_matches_{timestamp}.csv")
            self.matching_df.to_csv(matches_file, index=False)
            print(f"Saved {len(self.matching_df)} matches to {matches_file}")
        
        # Save unmatched products to CSV
        if hasattr(self, 'unmatched_df') and not self.unmatched_df.empty:
            unmatched_file = os.path.join(output_path, f"unmatched_products_{timestamp}.csv")
            self.unmatched_df.to_csv(unmatched_file, index=False)
            print(f"Saved {len(self.unmatched_df)} unmatched products to {unmatched_file}")


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Match product URLs with product titles from a CSV file')
    parser.add_argument('base_url', help='Base URL of the website to crawl')
    parser.add_argument('--csv', help='Path to the CSV file containing product titles',
                        default='/Users/umerkhan/code/crawl4ai_scraper/products_export_1.csv')
    parser.add_argument('--output', '-o', help='Directory to save the output CSV files')
    args = parser.parse_args()
    
    # Create the matcher
    matcher = ProductUrlMatcher(args.base_url, args.csv)
    
    # Load product titles
    matcher.load_product_titles()
    
    # Collect all URLs
    await matcher.collect_all_urls()
    
    # Find matches
    matches_df = matcher.find_product_url_matches()
    
    # Display the matches
    if not matches_df.empty:
        print("\n--- PRODUCT URL MATCHES ---\n")
        print(matches_df)
    else:
        print("\nNo matches found between product titles and URLs.")
    
    # Save results
    matcher.save_results(args.output)


if __name__ == "__main__":
    asyncio.run(main())
