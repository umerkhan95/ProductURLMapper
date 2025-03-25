#!/usr/bin/env python3
"""
Test script for OpenAI FAQ Generator

This script loads product content from files in the content directory and runs them through
the enhanced OpenAI FAQ generator to verify all fields are properly filled.
"""

import os
import json
import sys
from dotenv import load_dotenv
from openai_faq_generator import generate_faq_from_content

# Load environment variables
load_dotenv()

def test_single_product(content_file):
    """
    Test the FAQ generator with a single product content file
    
    Args:
        content_file (str): Path to the product content file
    """
    print(f"Testing FAQ generator with file: {content_file}")
    
    # Check if file exists
    if not os.path.exists(content_file):
        print(f"Error: File not found - {content_file}")
        return
    
    # Read content from file
    with open(content_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        return
    
    # Generate FAQ
    print("Generating FAQ from content...")
    result = generate_faq_from_content(api_key, content)
    
    # Check for errors
    if result.get("error", False):
        print(f"Error: {result.get('message', 'Unknown error')}")
        return
    
    # Verify all fields are present and not empty
    required_fields = ["usage", "benefits", "ingredients", "advantages", "application", "delivery"]
    required_faq_fields = ["package_contents", "usage_instructions", "side_effects", "contraindications", "storage"]
    
    missing_fields = []
    
    # Check main fields
    for field in required_fields:
        if field not in result or not result[field]:
            missing_fields.append(field)
    
    # Check FAQ fields
    if "faqs" not in result:
        missing_fields.append("faqs (entire section)")
    else:
        for field in required_faq_fields:
            if field not in result["faqs"] or not result["faqs"][field]:
                missing_fields.append(f"faqs.{field}")
    
    # Report results
    print("\n=== FAQ GENERATION RESULTS ===")
    
    if missing_fields:
        print("❌ The following fields are missing or empty:")
        for field in missing_fields:
            print(f"  - {field}")
    else:
        print("✅ All required fields are present and filled!")
    
    # Print the JSON output
    print("\n=== JSON OUTPUT ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Print field lengths to help identify potentially too short values
    print("\n=== FIELD LENGTHS ===")
    for field in required_fields:
        print(f"{field}: {len(result.get(field, ''))} characters")
    
    for field in required_faq_fields:
        print(f"faqs.{field}: {len(result.get('faqs', {}).get(field, ''))} characters")

def get_content_files():
    """
    Get a list of all content files in the content directory
    
    Returns:
        list: List of paths to content files
    """
    content_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'content')
    if not os.path.exists(content_dir):
        print(f"Error: Content directory not found - {content_dir}")
        return []
    
    content_files = []
    for filename in os.listdir(content_dir):
        if filename.endswith('.txt'):
            content_files.append(os.path.join(content_dir, filename))
    
    return content_files

def main():
    """Main function"""
    # Check if a specific file was provided
    if len(sys.argv) > 1:
        # Test with the provided file
        test_single_product(sys.argv[1])
        return
    
    # Get all content files
    content_files = get_content_files()
    
    if not content_files:
        print("No content files found in the content directory.")
        print("Usage: python test_faq_generator.py [content_file]")
        print("Example: python test_faq_generator.py content/sanddornfruchtfleischol.txt")
        return
    
    print(f"Found {len(content_files)} content files.")
    
    # Process all content files
    for content_file in content_files:
        print("\n" + "="*80)
        print(f"Processing file: {os.path.basename(content_file)}")
        print("="*80)
        test_single_product(content_file)
        print("\n")

if __name__ == "__main__":
    main()
