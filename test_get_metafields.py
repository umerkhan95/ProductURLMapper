import os
import json
import requests
from dotenv import load_dotenv
from typing import Dict, Any, List

# Load environment variables
load_dotenv()

# Shopify credentials
SHOP_URL = os.getenv('SHOPIFY_SHOP_URL')
ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')
API_VERSION = '2023-01'

def get_product_by_handle(handle: str) -> Dict[str, Any]:
    """Get a product from Shopify by its handle"""
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/products.json?handle={handle}"
    
    headers = {
        "X-Shopify-Access-Token": ACCESS_TOKEN
    }
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    if not data.get('products') or len(data['products']) == 0:
        print(f"❌ Product with handle '{handle}' not found")
        return {}
    
    return data['products'][0]

def get_metafields_for_product(product_id: int) -> Dict[str, Any]:
    """Get all metafields for a product"""
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/products/{product_id}/metafields.json"
    
    headers = {
        "X-Shopify-Access-Token": ACCESS_TOKEN
    }
    
    response = requests.get(url, headers=headers)
    return response.json()

def print_metafield_details(metafields: Dict[str, Any]) -> None:
    """Print detailed information about metafields"""
    if not metafields or not metafields.get('metafields'):
        print("No metafields found")
        return
    
    print("\n=== Metafield Details ===")
    print(f"Total metafields: {len(metafields['metafields'])}")
    
    # Group metafields by namespace for clearer output
    metafields_by_namespace = {}
    for metafield in metafields['metafields']:
        namespace = metafield.get('namespace', 'unknown')
        if namespace not in metafields_by_namespace:
            metafields_by_namespace[namespace] = []
        metafields_by_namespace[namespace].append(metafield)
    
    # Print metafields grouped by namespace
    for namespace, fields in metafields_by_namespace.items():
        print(f"\n## Namespace: {namespace}")
        print("-" * 80)
        
        for field in fields:
            print(f"Key: {field.get('key', 'N/A')}")
            print(f"Type: {field.get('type', 'N/A')}")
            print(f"Value: {field.get('value', 'N/A')[:100]}..." if len(str(field.get('value', 'N/A'))) > 100 else f"Value: {field.get('value', 'N/A')}")
            print(f"ID: {field.get('id', 'N/A')}")
            print("-" * 60)

def get_product_handles() -> List[str]:
    """
    Get a list of all product handles from the content directory
    
    Returns:
        List of product handles derived from content filenames
    """
    content_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'content')
    if not os.path.exists(content_dir):
        print(f"Error: Content directory not found - {content_dir}")
        return []
    
    handles = []
    for filename in os.listdir(content_dir):
        if filename.endswith('.txt'):
            # Extract handle from filename (remove .txt extension)
            handle = os.path.splitext(filename)[0]
            handles.append(handle)
    
    return handles

def process_single_product(handle: str) -> None:
    """Process a single product's metafields"""
    print(f"\n{'='*80}")
    print(f"Fetching metafields for product with handle: {handle}")
    print(f"{'='*80}")
    
    # Get the product
    product = get_product_by_handle(handle)
    if not product:
        return
    
    # Print basic product info
    print(f"\n=== Product Information ===")
    print(f"ID: {product['id']}")
    print(f"Title: {product['title']}")
    print(f"Handle: {product['handle']}")
    
    # Get all metafields for this product
    metafields = get_metafields_for_product(product['id'])
    
    # Print detailed metafield information
    print_metafield_details(metafields)
    
    # Save raw metafields data to a JSON file for reference
    with open(f"metafields_{handle}.json", "w") as f:
        json.dump(metafields, f, indent=2)
    print(f"\nRaw metafields data saved to metafields_{handle}.json")

def main():
    # Get the product handle from command line argument or use default
    import sys
    
    # If a specific handle is provided, only process that one
    if len(sys.argv) > 1:
        handle = sys.argv[1]
        process_single_product(handle)
        return
    
    # Otherwise, process all products from content directory
    handles = get_product_handles()
    
    if not handles:
        print("No product handles found in the content directory.")
        print("Usage: python test_get_metafields.py [handle]")
        print("Example: python test_get_metafields.py reizdarmprofil")
        return
    
    print(f"Found {len(handles)} product handles.")
    
    # Process all handles
    for handle in handles:
        process_single_product(handle)

if __name__ == "__main__":
    main()
