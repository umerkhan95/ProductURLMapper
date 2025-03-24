#!/usr/bin/env python3
"""
URL to Text converter using crawl4ai

This script extracts text content from a specified URL and converts it to clean text format,
removing links, media, and non-essential elements.
Usage: python url_to_markdown.py <url> [output_file]
If output_file is not specified, the text content will be printed to stdout.
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter


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
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text_content)
    print(f"Text content saved to {output_file}")


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Extract text content from a URL')
    parser.add_argument('url', help='URL to extract content from')
    parser.add_argument('-o', '--output', help='Output file path (if not specified, prints to stdout)')
    args = parser.parse_args()
    
    # Extract content
    print(f"Extracting text content from {args.url}...")
    result = await extract_text_from_url(args.url)
    
    if not result["success"]:
        print(result["error"], file=sys.stderr)
        sys.exit(1)
    
    # Prepare the content
    content = result["title"] + result["clean_text"]
    
    # Print status
    print(f"Status code: {result['status_code']}")
    
    # Output the content
    if args.output:
        save_text_to_file(content, args.output)
    else:
        print("\n--- TEXT CONTENT ---\n")
        print(content)


if __name__ == "__main__":
    asyncio.run(main())
