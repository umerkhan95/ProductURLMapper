import os
import json
import requests
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional, Union
import sys
import re

# Load environment variables from .env file
load_dotenv()

# Set up Shopify API credentials from environment variables
SHOP_URL = os.environ.get('SHOPIFY_SHOP_URL')
ACCESS_TOKEN = os.environ.get('SHOPIFY_ACCESS_TOKEN')
API_VERSION = '2024-01'

# Headers for API requests
headers = {
    'X-Shopify-Access-Token': ACCESS_TOKEN,
    'Content-Type': 'application/json'
}

# Function to clean text from unwanted prompts
def clean_text(text):
    # Remove instruction prompts that might be in the text
    patterns = [
        r'Use this text to answer questions in as much detail as possible for your customers\.',
        r'Provide detailed information about the product\.',
        r'Answer the following question:',
        r'Write a description for:',
        r'Explain in detail:'
    ]
    
    cleaned_text = text
    for pattern in patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text).strip()
    
    return cleaned_text

# Function to clean heading text from unwanted characters
def clean_heading(heading):
    """
    Clean heading text by removing unwanted characters like quotes and commas.
    
    Args:
        heading: The heading text to clean
        
    Returns:
        Cleaned heading text
    """
    if not heading:
        return heading
    
    # Remove trailing commas, quotes, and other unwanted characters
    heading = re.sub(r'[",\\]+$', '', heading.strip())
    
    # Remove leading quotes and other unwanted characters
    heading = re.sub(r'^[",\\]+', '', heading.strip())
    
    # Remove any remaining quotes that might be in the middle or elsewhere
    heading = heading.replace('"', '').replace('\\', '')
    
    return heading.strip()

# Product content for Leber Galle Kur
product_content = {
    "leber-galle-kur": {
        "p1": "Die Leber-Galle-Kur ist eine ganzheitliche Entgiftungstherapie, die dem Körper Lebendigkeit und Stärke zurückgibt, indem sie hilft, angesammelte Schadstoffe und Schlacken effektiv auszuleiten. Diese viertägige Kur fokussiert sich auf die Leber - das größte Organ im Körper, das etwa 2% des gesamten Körpergewichts ausmacht und bei einem durchschnittlichen Erwachsenen circa 1,5 Kilogramm wiegt. Als eines der wichtigsten Organe übernimmt die Leber zahlreiche lebenswichtige Funktionen: Sie fungiert als hocheffizientes Filtersystem für Blut und Lymphe zur Entfernung schädlicher Substanzen und gleichzeitig als biochemisches Laboratorium, das Nährstoffe in essentielle Enzyme und Hormone umwandelt. Eine beeinträchtigte Leberfunktion kann zu diversen gesundheitlichen Problemen führen, weshalb eine regelmäßige Entgiftung dieses zentralen Organs besonders wichtig ist.",
        "p2": "Die ORY Leber-Galle-Kur kombiniert verschiedene natürliche Therapieansätze für eine umfassende Entgiftung und Regeneration. Während der viertägigen Kur kommen eine spezielle Mischung aus frisch gepressten Säften, wirksamen Kräutertees, hochwertigen Ölen und wohltuenden Leberwickeln zum Einsatz, ergänzt durch zwei Colon-Hydro-Therapie-Sitzungen zur gründlichen Darmreinigung. Diese ganzheitliche Methode unterstützt die natürliche Ausscheidung von Gift- und Schadstoffen, die sich in den Gallengängen angesammelt haben. Die integrierte Colon-Hydro-Therapie fördert nicht nur den Fastenprozess und verringert das Hungergefühl, sondern stärkt auch die Darmflora als wichtigen Teil des Immunsystems. Erfahrungsgemäß sind Menschen mit gesunder Darmflora deutlich widerstandsfähiger gegen Erkältungen und Allergien, da die nützlichen Darmbakterien die erste Verteidigungslinie unseres Körperabwehrsystems bilden.",
        "nhaltsstoffe": "• Ory Saftkur: 2x5 Flaschen/ je 250ml (4 Fl. Saft und 1 Fl. Kräutertee)\n• 100% natürlich, frei von Farb- und Konservierungsstoffen\n• Olivenöl und Rizinusöl zum Abführen\n• Material für Leberwickel\n• 2 Colon-Hydro-Therapie-Sitzungen",
        "vorteile": "• Unterstützt die natürliche Entgiftungsfunktion der Leber\n• Fördert die Ausscheidung von Gift- und Schadstoffen aus den Gallengängen\n• Kombiniert mit Darmreinigung durch Colon-Hydro-Therapie\n• Natives Olivenöl kann schützende Wirkungen auf die Leber haben\n• Rizinusöl kann als Abführmittel die Dünndarmperistaltik verstärken\n• Frisch gepresste Säfte liefern wichtige Nährstoffe während der Fastenkur",
        "anwendung": "Die viertägige Kur sollte nur durchgeführt werden, wenn Sie sich gesundheitlich fit fühlen. Da die Säfte frisch gepresst werden, können diese nur für 2 Tage mitgegeben werden. Bei einer längeren Saftkur müssen die Säfte alle zwei Tage abgeholt werden. Die Kur umfasst den Verzehr von Säften, Kräutertees, die Anwendung von Leberwickeln sowie Olivenöl und Rizinusöl als Abführmittel, ergänzt durch zwei Colon-Hydro-Therapie-Sitzungen.",
        "lieferung": "Nur für Berlin verfügbar: Da die Säfte zum Fasten wirklich frisch sein müssen, können unsere Saftkuren nicht über weite Strecken geliefert werden. Bei der Bestellung bitte Telefonnummer und E-Mail angeben. Wir melden uns zeitnah, um den Start der Saftkur abzusprechen. Alternativ können Sie uns auch direkt anrufen: (030) 886-63373. Lieferung per Kurier innerhalb Berlins möglich.",
        "ans1": "Die Packung enthält die Ory Saftkur mit 2x5 Flaschen je 250ml (4 Flaschen Saft und 1 Flasche Kräutertee), Olivenöl, Rizinusöl zum Abführen, Material für Leberwickel sowie 2 Colon-Hydro-Therapie-Sitzungen.",
        "ans2": "Bitte beachten Sie, dass eine Fastenkur Ihren Organismus belasten kann und es daher wichtig ist, dass Sie sich gesundheitlich ausreichend fit fühlen. Die Kur umfasst den Verzehr von Säften und Kräutertees nach einem speziellen Zeitplan, die Anwendung von Leberwickeln sowie die Einnahme von Olivenöl und Rizinusöl, ergänzt durch zwei Colon-Hydro-Therapie-Sitzungen. Detaillierte Anweisungen erhalten Sie zu Beginn der Kur.",
        "ans3": "Während der Fastenkur können typische Entgiftungserscheinungen wie Kopfschmerzen, Müdigkeit oder leichte Übelkeit auftreten. Diese sind in der Regel vorübergehend und Teil des Reinigungsprozesses. Bei anhaltendem Unwohlsein sollte die Kur abgebrochen und ärztlicher Rat eingeholt werden.",
        "ans4": "Die Leber-Galle-Kur ist nicht geeignet für Schwangere, Stillende, Personen mit schweren Leber- oder Gallenerkrankungen, akuten Infektionen, Untergewicht, Diabetes oder schweren Herzerkrankungen. Im Zweifelsfall sollte vor Beginn der Kur ein Arzt konsultiert werden.",
        "ans5": "Die Säfte werden frisch gepresst und sollten im Kühlschrank bei 2-8°C gelagert werden. Die Haltbarkeit beträgt maximal 2 Tage. Die Öle sollten kühl und dunkel gelagert werden."
    }
}

def update_product_metafields(product_id: int, metafields_data: list) -> bool:
    """
    Update product metafields in Shopify.
    
    Args:
        product_id: Product ID
        metafields_data: List of metafield data
        
    Returns:
        True if update was successful, False otherwise
    """
    # Build headers for API request
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN
    }
    
    # Base URL for API calls
    base_url = f"https://{SHOP_URL}/admin/api/{API_VERSION}"
    
    success = True  # Track if all updates succeeded
    
    # Process each metafield individually
    for metafield in metafields_data:
        # Clean the value text to remove any unwanted instructions
        if isinstance(metafield.get("value"), str):
            metafield["value"] = clean_text(metafield["value"])
        
        # Special handling for rich text fields
        if metafield.get('type') == 'rich_text':
            url = f"{base_url}/metafields.json"
            
            # For rich text, we need to use a different endpoint and format
            payload = {
                "metafield": {
                    "owner_id": product_id,
                    "owner_resource": "product",
                    "namespace": metafield['namespace'],
                    "key": metafield['key'],
                    "value": metafield['value'],
                    "type": "rich_text"  
                }
            }
        else:
            # Standard metafield update
            url = f"{base_url}/products/{product_id}/metafields.json"
            
            payload = {
                "metafield": metafield
            }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                print(f"✅ Successfully updated metafield: {metafield['key']}")
            else:
                print(f"❌ Failed to update metafield: {metafield['key']}")
                print(f"Error: {response.text}")
                success = False
        except Exception as e:
            print(f"❌ Exception updating metafield {metafield['key']}: {str(e)}")
            success = False
    
    return success

def get_product_by_handle(handle):
    """Get a product from Shopify by its handle"""
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/products.json?handle={handle}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    products = response.json()['products']
    
    if not products:
        print(f"No product found with handle: {handle}")
        return None
    
    return products[0]

def normalize_faq_data(faq_data):
    """
    Normalize field names to handle case sensitivity issues between OpenAI response and Shopify fields.
    Ensures field names like "Ans1" are converted to "ans1" as expected by the code.
    
    Args:
        faq_data: Dictionary with the FAQ data from OpenAI
        
    Returns:
        Normalized dictionary with proper field names
    """
    normalized_data = {}
    
    # Copy values with normalized keys
    for key, value in faq_data.items():
        # Handle main fields - convert to lowercase
        normalized_key = key.lower()
        normalized_data[normalized_key] = value
        
        # Also keep the original key for compatibility
        normalized_data[key] = value
    
    # Handle FAQ fields if they exist
    if "faqs" in faq_data and isinstance(faq_data["faqs"], dict):
        normalized_data["faqs"] = {}
        for key, value in faq_data["faqs"].items():
            normalized_key = key.lower()
            normalized_data["faqs"][normalized_key] = value
            normalized_data["faqs"][key] = value
    
    return normalized_data

def process_product_with_faq(handle, faq_data):
    """
    Process a product with FAQ data and update it in Shopify.
    
    Args:
        handle: Product handle
        faq_data: FAQ data from OpenAI
        
    Returns:
        True if update was successful, False otherwise
    """
    # Check for required credentials
    if not SHOP_URL or not ACCESS_TOKEN:
        print("Error: Shopify credentials not found. Please set SHOPIFY_SHOP_URL and SHOPIFY_ACCESS_TOKEN.")
        return False

    # Normalize FAQ data to handle case sensitivity
    faq_data = normalize_faq_data(faq_data)

    # Get product from Shopify
    product = get_product_by_handle(handle)
    
    if not product:
        print(f"Unable to update product with handle '{handle}': Product not found")
        return False
    
    product_id = product['id']
    product_title = product['title']
    
    print(f"Updating product: {product_title} (Handle: {handle}, ID: {product_id})")
    
    # Map FAQ data to metafields
    metafields = []
    
    # ========== DYNAMIC HEADINGS AND CONTENT ==========
    # Handle dynamic headings and their content
    if 'dynamic_headings' in faq_data and isinstance(faq_data['dynamic_headings'], dict):
        # Clean heading keys before processing
        cleaned_headings = {}
        for heading, content in faq_data['dynamic_headings'].items():
            cleaned_heading = clean_heading(heading)
            cleaned_headings[cleaned_heading] = content
        
        # Replace original dynamic headings with cleaned ones
        faq_data['dynamic_headings'] = cleaned_headings
        
        headings = list(faq_data['dynamic_headings'].keys())
        
        # Heading 1 and p1
        if len(headings) >= 1:
            heading1 = headings[0]
            p1_content = faq_data['dynamic_headings'].get(heading1, "")
            
            metafields.append({
                "namespace": "heading",
                "key": "tag1",
                "value": heading1,
                "type": "single_line_text_field"
            })
            
            metafields.append({
                "namespace": "custom",
                "key": "p1",
                "value": p1_content,
                "type": "multi_line_text_field"
            })
            
        # Heading 2 and p2
        if len(headings) >= 2:
            heading2 = headings[1]
            p2_content = faq_data['dynamic_headings'].get(heading2, "")
            
            metafields.append({
                "namespace": "heading2",
                "key": "tag",
                "value": heading2,
                "type": "single_line_text_field"
            })
            
            metafields.append({
                "namespace": "custom",
                "key": "p2",
                "value": p2_content,
                "type": "multi_line_text_field"
            })
            
        # Heading 3 and para3
        if len(headings) >= 3:
            heading3 = headings[2]
            para3_content = faq_data['dynamic_headings'].get(heading3, "")
            
            metafields.append({
                "namespace": "heading3",
                "key": "tag",
                "value": heading3,
                "type": "single_line_text_field"
            })
            
            metafields.append({
                "namespace": "para3",
                "key": "tag",
                "value": para3_content,
                "type": "multi_line_text_field"
            })
            
        # Heading 4 and para4
        if len(headings) >= 4:
            heading4 = headings[3]
            para4_content = faq_data['dynamic_headings'].get(heading4, "")
            
            metafields.append({
                "namespace": "heading4",
                "key": "tag",
                "value": heading4,
                "type": "single_line_text_field"
            })
            
            metafields.append({
                "namespace": "para4",
                "key": "tag",
                "value": para4_content,
                "type": "multi_line_text_field"
            })
    
    # ========== PRODUCT DETAILS ==========
    # Map product details
    product_details_mapping = {
        "ingredients": {
            "namespace": "custom",
            "key": "pd1",
            "type": "multi_line_text_field"
        },
        "delivery": {
            "namespace": "custom",
            "key": "pd2",
            "type": "multi_line_text_field"
        },
        "application": {
            "namespace": "custom",
            "key": "pd3",
            "type": "multi_line_text_field"
        },
        "advantages": {
            "namespace": "custom",
            "key": "pd4",
            "type": "multi_line_text_field"
        }
    }
    
    for source_key, target in product_details_mapping.items():
        if source_key in faq_data and faq_data[source_key]:
            metafields.append({
                "namespace": target["namespace"],
                "key": target["key"],
                "value": faq_data[source_key],
                "type": target["type"]
            })
    
    # ========== FAQs ==========
    # Add FAQ answers
    if 'faqs' in faq_data and isinstance(faq_data['faqs'], dict):
        faq_mapping = {
            'package_contents': 'ans1',
            'usage_instructions': 'ans2',
            'side_effects': 'ans3',
            'contraindications': 'ans4',
            'storage': 'ans5'
        }
        
        for source_key, target_key in faq_mapping.items():
            if source_key in faq_data['faqs'] and faq_data['faqs'][source_key]:
                metafields.append({
                    "namespace": "custom",
                    "key": target_key,
                    "value": faq_data['faqs'][source_key],
                    "type": "multi_line_text_field"
                })
    
    if not metafields:
        print("No valid metafields found in FAQ data. Nothing to update.")
        return False
    
    # Update product metafields
    success = update_product_metafields(product_id, metafields)
    
    print(f"{'Product update completed successfully!' if success else 'There were issues during the update.'}")
    
    return success

def main():
    # Product handle to update
    handle = "leber-galle-kur"
    
    # Get product
    product = get_product_by_handle(handle)
    
    if not product:
        print(f"Product with handle '{handle}' not found!")
        return
    
    product_id = product['id']
    product_title = product['title']
    
    print(f"\n🔄 Updating product: {product_title} (Handle: {handle}, ID: {product_id})")
    
    # Prepare metafields data
    metafields = [
        {
            "namespace": "custom",
            "key": "p1",
            "value": product_content[handle]["p1"],
            "type": "multi_line_text_field"
        },
        {
            "namespace": "custom",
            "key": "p2",
            "value": product_content[handle]["p2"],
            "type": "multi_line_text_field"
        },
        {
            "namespace": "custom",
            "key": "nhaltsstoffe",
            "value": product_content[handle]["nhaltsstoffe"],
            "type": "multi_line_text_field"
        },
        {
            "namespace": "custom",
            "key": "vorteile",
            "value": product_content[handle]["vorteile"],
            "type": "multi_line_text_field"
        },
        {
            "namespace": "custom",
            "key": "anwendung",
            "value": product_content[handle]["anwendung"],
            "type": "multi_line_text_field"
        },
        {
            "namespace": "custom",
            "key": "lieferung",
            "value": product_content[handle]["lieferung"],
            "type": "multi_line_text_field"
        },
        {
            "namespace": "custom",
            "key": "faq_answers",
            "value": product_content[handle]["ans1"],
            "type": "multi_line_text_field"
        },
        {
            "namespace": "custom",
            "key": "ans1",
            "value": product_content[handle]["ans1"],
            "type": "multi_line_text_field"
        },
        {
            "namespace": "custom",
            "key": "ans2",
            "value": product_content[handle]["ans2"],
            "type": "multi_line_text_field"
        },
        {
            "namespace": "custom",
            "key": "ans3",
            "value": product_content[handle]["ans3"],
            "type": "multi_line_text_field"
        },
        {
            "namespace": "custom",
            "key": "ans4",
            "value": product_content[handle]["ans4"],
            "type": "multi_line_text_field"
        },
        {
            "namespace": "custom",
            "key": "ans5",
            "value": product_content[handle]["ans5"],
            "type": "multi_line_text_field"
        }
    ]
    
    # Update product metafields
    success = update_product_metafields(product_id, metafields)
    
    # Print updated content for verification
    print("\n📋 Updated Fields:")
    for field in metafields:
        value = field['value']
        print(f"{field['key']}: {value[:50]}..." if len(value) > 50 else f"{field['key']}: {value}")
    
    print(f"\n{'✅ Product update completed successfully!' if success else '❌ There were issues during the update.'}")

if __name__ == "__main__":
    main()