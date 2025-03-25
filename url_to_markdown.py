#!/usr/bin/env python3
"""
URL to Text converter using crawl4ai

This script extracts text content from a specified URL and converts it to clean text format,
removing links, media, and non-essential elements.

Usage: 
- As standalone: python url_to_markdown.py <url> [output_file]
- From other modules: import and use extract_products_content

If output_file is not specified, the text content will be printed to stdout.
"""
import asyncio
import argparse
import os
import sys
import pandas as pd
from datetime import datetime
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

# Import the OpenAI FAQ generator function
try:
    from openai_faq_generator import generate_faq_from_content
except ImportError:
    print("Warning: openai_faq_generator module not found. Will save to files instead.")
    generate_faq_from_content = None

# Import the product updater function
try:
    from product_updater import process_product_with_faq
except ImportError:
    print("Warning: product_updater module not found. Will not update products.")
    process_product_with_faq = None


async def extract_text_from_url(url, config=None):
    """
    Extract clean text content from a URL, removing links, media and non-essential elements.
    
    Args:
        url (str): The URL to extract content from
        config (CrawlerRunConfig, optional): Custom crawler configuration
        
    Returns:
        dict: A dictionary containing the extracted text content and metadata
    """
    # Create a content filter to remove non-essential elements
    content_filter = PruningContentFilter(
        threshold=0.5,             # Score boundary for content to keep
        threshold_type="fixed",    # Use fixed threshold
        min_word_threshold=5       # Minimum words required to keep a text block
    )
    
    # Configure the markdown generator to ignore links and images
    md_generator = DefaultMarkdownGenerator(
        content_filter=content_filter,
        options={
            "ignore_links": True,      # Remove all hyperlinks
            "ignore_images": True,     # Remove all images
            "escape_html": True,       # Convert HTML entities to text
            "body_width": 0,           # No line wrapping
            "skip_internal_links": True,
            "include_sup_sub": False
        }
    )
    
    # Default configuration if none is provided
    if config is None:
        config = CrawlerRunConfig(
            word_count_threshold=5,        # Include content blocks with at least 5 words
            exclude_external_links=True,   # Exclude external links
            remove_overlay_elements=True,  # Remove popups/modals
            process_iframes=True,          # Process iframe content
            markdown_generator=md_generator
        )
    
    browser_config = BrowserConfig(verbose=False)  # Set to True for debugging
    
    # Create and execute the crawler
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=config)
        
        if not result.success:
            return {
                "success": False,
                "error": f"Crawl failed: {result.error_message}",
                "status_code": result.status_code
            }
        
        # Extract the filtered markdown content (if available) or raw markdown
        markdown_result = result.markdown
        clean_text = markdown_result.fit_markdown if markdown_result.fit_markdown else markdown_result.raw_markdown
        
        return {
            "success": True,
            "url": result.url,
            "title": f"Content from {result.url}\n\nExtracted on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n",
            "clean_text": clean_text,
            "status_code": result.status_code
        }


def save_text_to_file(text_content, output_file):
    """
    Save text content to a file.
    
    Args:
        text_content (str): The text content to save
        output_file (str): The file path to save to
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text_content)
    print(f"Text content saved to {output_file}")


async def extract_products_content(products_df, output_dir='content', use_openai=True, save_to_file=False):
    """
    Extract content from product URLs in the dataframe and either save it to files
    or pass it to OpenAI for FAQ generation and then to product updater for Shopify update.
    
    Args:
        products_df (pd.DataFrame): DataFrame with product URLs and handles
                                   Must have 'URL' and 'Handle' columns
        output_dir (str): Directory where content will be saved (if save_to_file=True)
        use_openai (bool): Whether to pass content to OpenAI for FAQ generation
        save_to_file (bool): Whether to save content to files
    
    Returns:
        list: List of processed products with results
    """
    if not isinstance(products_df, pd.DataFrame):
        raise ValueError("products_df must be a pandas DataFrame")
    
    if 'URL' not in products_df.columns or 'Handle' not in products_df.columns:
        raise ValueError("DataFrame must contain both 'URL' and 'Handle' columns")
    
    # Create the output directory if saving to files
    if save_to_file:
        os.makedirs(output_dir, exist_ok=True)
    
    processed_results = []
    total_products = len(products_df)
    
    print(f"Starting extraction of {total_products} products...")
    
    # Check if the OpenAI API key is available
    api_key = os.environ.get("OPENAI_API_KEY")
    if use_openai and not api_key:
        print("Warning: OPENAI_API_KEY environment variable is not set.")
        print("Will save content to files instead of generating FAQs.")
        use_openai = False
    
    for i, (_, row) in enumerate(products_df.iterrows(), 1):
        url = row['URL']
        handle = row['Handle']
        title = row.get('Title', handle)
        
        # Sanitize the filename
        safe_handle = "".join([c if c.isalnum() or c in ['-', '_'] else '_' for c in handle])
        
        print(f"Processing [{i}/{total_products}]: {handle} ({url})")
        
        try:
            # Extract content from URL
            result = await extract_text_from_url(url)
            
            if not result["success"]:
                print(f"Failed to extract content from {url}: {result.get('error', 'Unknown error')}")
                processed_results.append({
                    "handle": handle,
                    "url": url,
                    "success": False,
                    "error": result.get('error', 'Unknown error')
                })
                continue
            
            # Prepare content with title
            content = f"# {title}\n\n"
            content += f"URL: {url}\n\n"
            content += result["clean_text"]
            
            # Save to file if requested
            if save_to_file:
                output_file = os.path.join(output_dir, f"{safe_handle}.txt")
                save_text_to_file(content, output_file)
                print(f"  Saved content to {output_file}")
            
            # Process with OpenAI if requested and available
            faq_result = None
            if use_openai and generate_faq_from_content:
                try:
                    print(f"  Generating FAQ for: {handle}")
                    faq_result = generate_faq_from_content(api_key, content)
                    
                    if faq_result.get("error", False):
                        print(f"  Error generating FAQ: {faq_result.get('message', 'Unknown error')}")
                        processed_results.append({
                            "handle": handle,
                            "url": url,
                            "content_extracted": True,
                            "faq_generated": False,
                            "error": faq_result.get('message', 'Unknown error')
                        })
                        continue
                    
                    # Process the product with the FAQ result if the function is available
                    if process_product_with_faq:
                        print(f"  Updating product in Shopify: {handle}")
                        update_result = process_product_with_faq(handle, faq_result)
                        
                        processed_results.append({
                            "handle": handle,
                            "url": url,
                            "content_extracted": True,
                            "faq_generated": True,
                            "product_updated": update_result
                        })
                    else:
                        print(f"  Product updater not available, cannot update Shopify product")
                        processed_results.append({
                            "handle": handle,
                            "url": url,
                            "content_extracted": True,
                            "faq_generated": True,
                            "product_updated": False,
                            "error": "Product updater not available"
                        })
                        
                except Exception as e:
                    print(f"  Error in FAQ generation or product update: {str(e)}")
                    processed_results.append({
                        "handle": handle,
                        "url": url,
                        "content_extracted": True,
                        "error": str(e)
                    })
            else:
                # If not using OpenAI, just record that we saved the content
                processed_results.append({
                    "handle": handle,
                    "url": url,
                    "content_extracted": True,
                    "saved_to_file": save_to_file
                })
                
        except Exception as e:
            print(f"  Error processing {handle}: {str(e)}")
            processed_results.append({
                "handle": handle,
                "url": url,
                "success": False,
                "error": str(e)
            })
    
    # Print summary
    print("\n=== Processing Summary ===")
    successful = sum(1 for r in processed_results if r.get("content_extracted", False))
    faq_generated = sum(1 for r in processed_results if r.get("faq_generated", False))
    product_updated = sum(1 for r in processed_results if r.get("product_updated", False))
    
    print(f"Total products: {total_products}")
    print(f"Successfully extracted content: {successful}")
    print(f"Generated FAQs: {faq_generated}")
    print(f"Updated products in Shopify: {product_updated}")
    
    return processed_results


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Extract text content from a URL and convert it to clean text format.')
    parser.add_argument('url', type=str, help='The URL to extract content from')
    parser.add_argument('output_file', type=str, nargs='?', default=None, help='The file path to save the extracted content to')
    args = parser.parse_args()

    if args.output_file:
        output_dir = os.path.dirname(args.output_file)
        os.makedirs(output_dir, exist_ok=True)

    result = await extract_text_from_url(args.url)

    if not result["success"]:
        print(f"Failed to extract content from {args.url}: {result.get('error', 'Unknown error')}")
        sys.exit(1)

    content = result["title"] + result["clean_text"]

    if args.output_file:
        save_text_to_file(content, args.output_file)
    else:
        print(content)

if __name__ == "__main__":
    asyncio.run(main())