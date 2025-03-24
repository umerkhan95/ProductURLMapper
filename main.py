#!/usr/bin/env python3
"""
Main script to run the full product URL matching and content extraction workflow.

This script:
1. Uses ProductUrlMatcher to find URLs matching product titles from a CSV file
2. Passes the matched products to url_to_markdown to extract and save content

Usage:
python main.py <base_url> --csv <csv_file_path>
"""

import os
import asyncio
import argparse
import pandas as pd
from product_url_matcher import ProductUrlMatcher
from url_to_markdown import extract_products_content


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Match product URLs and extract content')
    parser.add_argument('base_url', help='Base URL of the website to crawl')
    parser.add_argument('--csv', help='Path to the CSV file containing product titles',
                        default='products_export_1.csv')
    parser.add_argument('--output', '-o', help='Directory to save the extracted content',
                        default='content')
    parser.add_argument('--save-csv', action='store_true', 
                        help='Also save the results to CSV files (optional)')
    args = parser.parse_args()
    
    print(f"Starting workflow for {args.base_url}")
    
    # Step 1: Create the matcher and collect URLs
    print("\n=== STEP 1: MATCHING PRODUCTS WITH URLS ===\n")
    matcher = ProductUrlMatcher(args.base_url, args.csv)
    
    # Load product titles
    matcher.load_product_titles()
    
    # Collect all URLs
    await matcher.collect_all_urls()
    
    # Find matches between product titles and URLs
    matches_df = matcher.find_product_url_matches()
    
    if matches_df.empty:
        print("\nNo matches found between product titles and URLs. Exiting.")
        return
    
    # Optionally save the CSV files
    if args.save_csv:
        print("\nSaving results to CSV files...")
        matcher.save_results()
    
    # Step 2: Extract content for matched products
    print("\n=== STEP 2: EXTRACTING CONTENT FOR MATCHED PRODUCTS ===\n")
    
    # Get the matched products DataFrame
    matched_products = matcher.get_matched_products_and_urls()
    
    # Extract and save content for each matched product
    extracted_files = await extract_products_content(matched_products, args.output)
    
    # Summary
    print("\n=== WORKFLOW COMPLETE ===\n")
    print(f"Matched {len(matched_products)} products with URLs")
    print(f"Successfully extracted content for {len(extracted_files)} products")
    print(f"Content saved to {os.path.abspath(args.output)} directory")
    
    if len(extracted_files) < len(matched_products):
        print(f"Failed to extract content for {len(matched_products) - len(extracted_files)} products")


if __name__ == "__main__":
    asyncio.run(main())