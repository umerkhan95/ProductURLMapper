#!/usr/bin/env python3
"""
Test script to update products with FAQ data
This will help verify that our field mapping is correct
"""

import os
import json
from dotenv import load_dotenv
from openai_faq_generator import generate_faq_from_content
from product_updater import process_product_with_faq

# Load environment variables
load_dotenv()

def test_single_product_update(handle, content_file):
    """
    Test updating a single product with FAQ data generated from a content file
    
    Args:
        handle (str): Product handle in Shopify
        content_file (str): Path to content file
    """
    print(f"\n=== Testing Product Update for '{handle}' ===\n")
    
    # Check if file exists
    if not os.path.exists(content_file):
        print(f"Error: Content file not found - {content_file}")
        return
    
    # Read content from file
    with open(content_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        return
    
    # Generate FAQ data
    print("Generating FAQ data from content...")
    faq_data = generate_faq_from_content(api_key, content)
    
    # Check for errors
    if faq_data.get("error", False):
        print(f"Error generating FAQ data: {faq_data.get('message', 'Unknown error')}")
        return
    
    # Print the FAQ data
    print("\n=== Generated FAQ Data ===")
    print(json.dumps(faq_data, indent=2, ensure_ascii=False))
    
    # Update the product
    print("\n=== Updating Product in Shopify ===")
    success = process_product_with_faq(handle, faq_data)
    
    if success:
        print("\n✅ Product update successful!")
        print("Please check the product in Shopify to verify all fields are filled correctly.")
    else:
        print("\n❌ Product update failed!")

def get_content_files():
    """
    Get a list of all content files in the content directory
    
    Returns:
        list: A list of (handle, content_file_path) tuples
    """
    content_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'content')
    if not os.path.exists(content_dir):
        print(f"Error: Content directory not found - {content_dir}")
        return []
    
    content_files = []
    for filename in os.listdir(content_dir):
        if filename.endswith('.txt'):
            handle = os.path.splitext(filename)[0]
            content_file_path = os.path.join(content_dir, filename)
            content_files.append((handle, content_file_path))
    
    return content_files

if __name__ == "__main__":
    import sys
    
    # If specific handle and content file provided, only process that one
    if len(sys.argv) == 3:
        handle = sys.argv[1]
        content_file = sys.argv[2]
        test_single_product_update(handle, content_file)
    else:
        # Otherwise, process all files in content directory
        content_files = get_content_files()
        
        if not content_files:
            print("No content files found in the content directory.")
            print("Usage: python test_product_update.py [product_handle] [content_file]")
            print("Example: python test_product_update.py sanddornfruchtfleischol content/sanddornfruchtfleischol.txt")
            sys.exit(1)
        
        print(f"Found {len(content_files)} content files to process.")
        
        # Process all content files
        for handle, content_file in content_files:
            print(f"\n{'='*80}")
            print(f"Processing {handle} from {os.path.basename(content_file)}")
            print(f"{'='*80}")
            test_single_product_update(handle, content_file)
