#!/usr/bin/env python3
"""
Main script to run the full workflow:

1. Uses ProductUrlMatcher to find URLs matching product titles from a CSV file
2. Passes the matched products to url_to_markdown to extract content
3. Content is sent to OpenAI for FAQ generation
4. FAQs are used to update product metafields in Shopify

Usage:
python main.py <base_url> --csv <csv_file_path> [--save-content] [--skip-shopify]
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

# Import our modules
from product_url_matcher import ProductUrlMatcher
from url_to_markdown import extract_products_content

# Load environment variables
load_dotenv()

# Check for required environment variables
def check_environment():
    """Check if required environment variables are set"""
    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API key for generating FAQs',
        'SHOPIFY_SHOP_URL': 'Shopify shop URL (e.g., your-store.myshopify.com)',
        'SHOPIFY_ACCESS_TOKEN': 'Shopify access token for API authentication'
    }
    
    missing = []
    for var, description in required_vars.items():
        if not os.environ.get(var):
            missing.append(f"{var} ({description})")
    
    if missing:
        print("⚠️ The following environment variables are missing:")
        for var in missing:
            print(f"  - {var}")
        print("\nSome functionality may be limited.")
    else:
        print("✅ All required environment variables are set.")

async def main():
    """Main workflow function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Match product URLs, extract content, generate FAQs, and update products')
    parser.add_argument('base_url', help='Base URL of the website to crawl')
    parser.add_argument('--csv', help='Path to the CSV file containing product titles',
                        default='products_export_1.csv')
    parser.add_argument('--output', '-o', help='Directory to save the extracted content',
                        default='content')
    parser.add_argument('--save-content', action='store_true', 
                        help='Save content to text files')
    parser.add_argument('--save-csv', action='store_true', 
                        help='Save URL matching results to CSV files')
    parser.add_argument('--skip-openai', action='store_true',
                        help='Skip the OpenAI FAQ generation step')
    parser.add_argument('--skip-shopify', action='store_true',
                        help='Skip updating products in Shopify')
    args = parser.parse_args()
    
    # Welcome banner
    print("\n" + "="*80)
    print(" 🌐 PRODUCT CONTENT EXTRACTOR AND SHOPIFY UPDATER")
    print("="*80)
    
    # Check environment variables
    check_environment()
    
    # Verify CSV file existence
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"\n❌ Error: CSV file not found: {args.csv}")
        print("Please provide a valid CSV file containing product data.")
        return
    
    print(f"\n🔍 Starting workflow for {args.base_url}")
    
    # Step 1: Create the matcher and collect URLs
    print("\n" + "="*80)
    print(" STEP 1: MATCHING PRODUCTS WITH URLS")
    print("="*80)
    
    matcher = ProductUrlMatcher(args.base_url, args.csv)
    
    # Load product titles
    matcher.load_product_titles()
    
    # Collect all URLs
    await matcher.collect_all_urls()
    
    # Find matches between product titles and URLs
    matches_df = matcher.find_product_url_matches()
    
    if matches_df.empty:
        print("\n❌ No matches found between product titles and URLs. Exiting.")
        return
    
    # Optionally save the CSV files
    if args.save_csv:
        print("\nSaving results to CSV files...")
        matcher.save_results()
    
    # Step 2: Extract content, generate FAQs, and update products
    print("\n" + "="*80)
    print(" STEP 2: EXTRACTING CONTENT, GENERATING FAQS, AND UPDATING PRODUCTS")
    print("="*80)
    
    # Get the matched products DataFrame
    matched_products = matcher.get_matched_products_and_urls()
    
    print(f"\nFound {len(matched_products)} products with matching URLs")
    
    # Extract content, generate FAQs, and update products
    results = await extract_products_content(
        products_df=matched_products, 
        output_dir=args.output,
        use_openai=not args.skip_openai,
        save_to_file=args.save_content
    )
    
    # Summary
    print("\n" + "="*80)
    print(" WORKFLOW SUMMARY")
    print("="*80)
    
    total_products = len(matched_products)
    content_extracted = sum(1 for r in results if r.get("content_extracted", False))
    faq_generated = sum(1 for r in results if r.get("faq_generated", False))
    product_updated = sum(1 for r in results if r.get("product_updated", False))
    failed = total_products - content_extracted
    
    print(f"\n• Total products processed: {total_products}")
    print(f"• Content successfully extracted: {content_extracted}")
    
    if not args.skip_openai:
        print(f"• FAQs successfully generated: {faq_generated}")
    
    if not args.skip_shopify:
        print(f"• Products updated in Shopify: {product_updated}")
    
    if failed > 0:
        print(f"• Failed to process: {failed}")
        print("\nFailed products:")
        for r in results:
            if not r.get("content_extracted", False):
                print(f"  - {r.get('handle', 'Unknown')}: {r.get('error', 'Unknown error')}")
    
    if args.save_content:
        print(f"\nContent saved to {os.path.abspath(args.output)} directory")
    
    print("\n" + "="*80)
    print(" WORKFLOW COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user. Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        sys.exit(1)