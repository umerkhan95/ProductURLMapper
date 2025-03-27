#!/usr/bin/env python3
"""
OpenAI FAQ Generator

This script takes content from a product page, sends it to multiple OpenAI
assistants, and generates structured FAQ data in JSON format.

Each assistant is specialized in generating specific content for German
health products, such as FAQs, product details, and dynamic headings.

Usage:
    - As standalone: python openai_faq_generator.py --content "Product content..."
    - From other modules: import and use generate_faq_from_content
"""

import os
import json
import time
import argparse
from typing import Dict, Any, Optional, List

# Check if OpenAI package is installed, if not provide installation instructions
try:
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI package is not installed.")
    print("Please install it using: pip install openai")
    exit(1)

# Assistant IDs for specialized content generation
# FAQ Assistants
FAQ_PACKAGE_CONTENTS_ASSISTANT_ID = "asst_vYny09ZGcvCPAFLMkHa5RYta"
FAQ_USAGE_INSTRUCTIONS_ASSISTANT_ID = "asst_Iw73um6oIi3qurZb1BXO0BEJ"
FAQ_SIDE_EFFECTS_ASSISTANT_ID = "asst_M3lrSOWu857w742XbY8Qcx7t"
FAQ_CONTRAINDICATIONS_ASSISTANT_ID = "asst_Eot5rsc8h5Oga5ksKlyEPLmg"
FAQ_STORAGE_ASSISTANT_ID = "asst_Kz5iv0xV1noKj7xmtnKc8I29"

# Product Details Assistants
INGREDIENTS_ASSISTANT_ID = "asst_5xl4kG6zyemvOnzdb1ByI2Hh"
DELIVERY_ASSISTANT_ID = "asst_Icw8gWXeTF9tspeqfIM11mAJ"
APPLICATION_ASSISTANT_ID = "asst_0k8rb8DvyfPK6o0L1VOB7NXL"
ADVANTAGES_ASSISTANT_ID = "asst_WAE5m67U20xM3QWgNq29BaB6"

# Dynamic Headings and Answers
DYNAMIC_HEADINGS_ASSISTANT_ID = "asst_lxEXK2rjsaOWkgzdJaS5p4mx"
DYNAMIC_ANSWER_ASSISTANTS = [
    "asst_hdkmqxREefcBVJnZM81z3Z2c",
    "asst_JFbbtjfzDvuyT3cs0OuoiZII",
    "asst_HEYpdkJBm5pbEovcXi01cZ1B",
    "asst_S4YJGUN6JETK68GTMBJipcPo"
]

def call_assistant(client, assistant_id: str, content: str, max_timeout: int = 180) -> Dict[str, Any]:
    """
    Helper function to call an OpenAI assistant and get the response.
    
    Args:
        client: OpenAI client
        assistant_id: ID of the assistant to call
        content: Text content to send to the assistant
        max_timeout: Maximum timeout in seconds (default: 180)
        
    Returns:
        Response from the assistant
    """
    # Create a thread
    thread = client.beta.threads.create()
    
    # Add system instruction to provide default guidelines when information is missing
    system_instruction = """
    Wenn du keine spezifischen Informationen zum angefragten Inhalt findest, gib bitte allgemeine Standardrichtlinien an, anstatt zu sagen, dass keine Informationen verfügbar sind.
    
    Für Nebenwirkungen (wenn keine spezifischen Informationen vorhanden):
    "Bei bestimmungsgemäßem Gebrauch sind keine Nebenwirkungen bekannt. Bei individuellen Unverträglichkeiten oder Allergien sollten Sie die Anwendung abbrechen und einen Arzt konsultieren. Der Test dient nur der Analyse und nicht der Diagnose oder Behandlung von Krankheiten."
    
    Für Kontraindikationen (wenn keine spezifischen Informationen vorhanden):
    "Der Test sollte nicht von Personen unter 18 Jahren ohne Aufsicht eines Erwachsenen durchgeführt werden. Bei bestehenden schweren Erkrankungen konsultieren Sie bitte vor der Durchführung einen Arzt. Personen, die bereits unter ärztlicher Behandlung stehen oder Medikamente einnehmen, die oxidativen Stress beeinflussen können, sollten vor der Verwendung des Tests ihren behandelnden Arzt konsultieren."
    
    Für Lagerungshinweise (wenn keine spezifischen Informationen vorhanden):
    "Bewahren Sie das Testkit an einem kühlen, trockenen Ort bei Temperaturen zwischen 2°C und 25°C auf, geschützt vor direkter Sonneneinstrahlung. Das Produkt darf nicht eingefroren werden. Die Proben sollten nach der Entnahme zeitnah versendet werden, um die Qualität der Ergebnisse zu gewährleisten. Außerhalb der Reichweite von Kindern aufbewahren."
    """
    
    # Create messages for the assistant
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=system_instruction + "\n\n" + content
    )
    
    # Run the assistant
    print(f"Starting OpenAI assistant {assistant_id}...")
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    
    # Poll until the run completes
    start_time = time.time()
    while run.status in ["queued", "in_progress"]:
        elapsed = time.time() - start_time
        if elapsed > max_timeout:
            return {
                "error": True,
                "message": f"Timeout after waiting {elapsed:.1f} seconds. Last status: {run.status}"
            }
        
        # Print progress updates
        if run.status == "in_progress":
            print(f"Processing with assistant {assistant_id}... ({elapsed:.1f}s)")
        else:
            print(f"Waiting in queue... ({elapsed:.1f}s)")
            
        # Wait a bit before polling again
        time.sleep(2)
        
        # Retrieve the current status of the run
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
    
    if run.status == "completed":
        # Get messages from the thread
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        
        # The last message should be from the assistant
        for message in messages.data:
            if message.role == "assistant":
                for content_part in message.content:
                    if content_part.type == "text":
                        return {
                            "error": False,
                            "response": content_part.text.value
                        }
        
        # If we didn't find an assistant message with text content
        return {
            "error": True,
            "message": "No valid response found in the thread."
        }
    else:
        # Handle error case
        return {
            "error": True,
            "message": f"Run failed with status: {run.status}"
        }

def clean_response(response: str) -> str:
    """
    Clean response content by removing markdown code blocks and other formatting markers.
    
    Args:
        response: Response string from the assistant
        
    Returns:
        Cleaned response string
    """
    # Remove markdown code block formatting
    if "```json" in response:
        response = response.split("```json", 1)[1]
    elif "```" in response:
        response = response.split("```", 1)[1]
    
    # Remove ending code block marker if present
    if "```" in response:
        response = response.split("```", 1)[0]
    
    # Remove any JSON structure indicators from nested responses
    response = response.replace("```json", "").replace("```", "")
    
    # Remove extra quotes and escaping that might be present
    response = response.replace('\\"', '"').replace('\\\\"', '"')
    
    # Strip whitespace
    response = response.strip()
    
    # Try to parse as JSON to extract text content
    try:
        # If it's valid JSON, extract meaningful content
        parsed = json.loads(response)
        return extract_meaningful_content(parsed)
    except:
        # If not valid JSON, return as is
        return response

def extract_meaningful_content(data):
    """
    Extract meaningful text content from parsed JSON data.
    
    Args:
        data: Parsed JSON data (dict, list, or primitive value)
        
    Returns:
        Extracted content as a string or the original structure if extraction not possible
    """
    # Handle different data types
    if isinstance(data, str):
        return data
    elif isinstance(data, (int, float, bool)):
        return str(data)
    elif isinstance(data, list):
        # For lists, try to join items or return the first non-empty item
        if all(isinstance(item, str) for item in data):
            return ". ".join(data)
        for item in data:
            content = extract_meaningful_content(item)
            if content:
                return content
        return ""
    elif isinstance(data, dict):
        # Strategy 1: If there's a single key that seems like a label and value is a string, return the value
        if len(data) == 1:
            key, value = next(iter(data.items()))
            if isinstance(value, str):
                return value
        
        # Strategy 2: Look for common answer fields
        for key in ["answer", "response", "content", "text", "description", "value", "Antwort", "Beschreibung"]:
            if key in data and isinstance(data[key], str):
                return data[key]
            
        # Strategy 3: If there's a nested structure, try to extract meaningful content from it
        for key, value in data.items():
            # Skip keys that are likely metadata
            if key.lower() in ["error", "status", "code"]:
                continue
                
            # Process the value
            if isinstance(value, (dict, list)):
                extracted = extract_meaningful_content(value)
                if extracted:
                    return extracted
            elif isinstance(value, str) and len(value) > 10:  # Reasonably long string
                return value
        
        # Strategy 4: Combine all string values with descriptions
        text_parts = []
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 5:
                text_parts.append(f"{value}")
            elif isinstance(value, (dict, list)):
                extracted = extract_meaningful_content(value)
                if extracted:
                    text_parts.append(extracted)
        
        if text_parts:
            return " ".join(text_parts)
        
        # If nothing worked, convert the entire dict to a string
        try:
            return json.dumps(data, ensure_ascii=False)
        except:
            return str(data)
    
    # Fallback
    return str(data)


def parse_json_response(response: str) -> Dict[str, Any]:
    """
    Parse JSON response from assistant, handling markdown formatting.
    
    Args:
        response: Response string from the assistant
        
    Returns:
        Parsed JSON object
    """
    try:
        # Clean the response first
        cleaned_response = clean_response(response)
        
        # Try to parse as JSON
        try:
            # If it's still a JSON string, parse it
            result = json.loads(cleaned_response)
            return result
        except:
            # If it's not a JSON string anymore (because we extracted content),
            # just return the cleaned text
            return cleaned_response
    except Exception as e:
        # If we can't parse it as JSON, return the cleaned text as a string
        print(f"Error processing response: {e}")
        return clean_response(response)


def clean_nested_json(obj):
    """
    Recursively clean nested JSON objects to remove any remaining formatting markers.
    
    Args:
        obj: JSON object or value to clean
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                if value.startswith("{") and value.endswith("}") and "\n" in value:
                    # This looks like a JSON string, try to parse and extract
                    try:
                        parsed = json.loads(value)
                        obj[key] = extract_meaningful_content(parsed)
                    except:
                        # If parsing fails, just clean the string
                        obj[key] = clean_response(value)
                else:
                    obj[key] = clean_response(value)
            else:
                clean_nested_json(value)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str):
                if item.startswith("{") and item.endswith("}") and "\n" in item:
                    # This looks like a JSON string, try to parse and extract
                    try:
                        parsed = json.loads(item)
                        obj[i] = extract_meaningful_content(parsed)
                    except:
                        # If parsing fails, just clean the string
                        obj[i] = clean_response(item)
                else:
                    obj[i] = clean_response(item)
            else:
                clean_nested_json(item)

def get_dynamic_headings(client, content: str) -> List[str]:
    """
    Get dynamic headings from the headings assistant.
    
    Args:
        client: OpenAI client
        content: Product content
        
    Returns:
        List of headings
    """
    result = call_assistant(client, DYNAMIC_HEADINGS_ASSISTANT_ID, content)
    
    if result.get("error", True):
        print(f"Error getting dynamic headings: {result.get('message', 'Unknown error')}")
        return []
    
    try:
        # Clean the response first
        cleaned_response = clean_response(result["response"])
        headings_data = json.loads(cleaned_response)
        headings = [headings_data.get(f"heading{i}", f"Heading {i}") for i in range(1, 5)]
        print(f"Generated dynamic headings: {headings}")
        return headings
    except Exception as e:
        # Try a different parsing approach for non-standard formats
        try:
            # Extract headings from the raw text if JSON parsing fails
            response_text = result["response"]
            headings = []
            for i in range(1, 5):
                heading_marker = f"heading{i}"
                if heading_marker in response_text.lower():
                    # Look for the heading in the text and extract it
                    start_idx = response_text.lower().find(heading_marker)
                    if start_idx != -1:
                        # Find the next line after the heading marker
                        start_idx = response_text.find(":", start_idx) + 1
                        end_idx = response_text.find("\n", start_idx)
                        if end_idx == -1:  # If it's the last line
                            end_idx = len(response_text)
                        heading = response_text[start_idx:end_idx].strip().strip('"').strip("'")
                        headings.append(heading)
            
            if not headings:
                # If still no headings, try to split by newlines and take four lines
                lines = [line.strip() for line in response_text.split("\n") if line.strip()]
                headings = [line for line in lines if len(line) > 10][:4]  # Take up to 4 substantial lines
            
            print(f"Generated dynamic headings (via text extraction): {headings}")
            return headings
        except Exception as nested_e:
            print(f"Error extracting headings from response: {nested_e}")
            print(f"Raw response: {result['response']}")
            return []

def get_dynamic_heading_answers(client, content: str, headings: List[str]) -> Dict[str, str]:
    """
    Get answers for dynamic headings.
    
    Args:
        client: OpenAI client
        content: Product content
        headings: List of headings
        
    Returns:
        Dictionary mapping headings to answers
    """
    answers = {}
    
    for i, heading in enumerate(headings):
        if i >= len(DYNAMIC_ANSWER_ASSISTANTS):
            break
            
        assistant_id = DYNAMIC_ANSWER_ASSISTANTS[i]
        prompt = f"Bitte beantworte folgende Frage zum Produkt: {heading}\n\nInhalt: {content}"
        
        result = call_assistant(client, assistant_id, prompt)
        
        if not result.get("error", True):
            answers[heading] = result["response"]
        else:
            print(f"Error getting answer for heading '{heading}': {result.get('message', 'Unknown error')}")
            answers[heading] = f"Informationen zu '{heading}' sind derzeit nicht verfügbar."
    
    return answers

def generate_faq_from_content(api_key: Optional[str], content: str) -> Dict[str, Any]:
    """
    Send content to multiple OpenAI assistants and compile structured FAQ data.
    
    Args:
        api_key: OpenAI API key (if None, will try to use from environment)
        content: Text content to send to the assistants
        
    Returns:
        JSON response with structured FAQ and product data
    """
    # Use provided API key or get from environment
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {
                "error": True,
                "message": "No OpenAI API key provided and OPENAI_API_KEY environment variable not set."
            }
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Result structure
    result = {
        "error": False,
        "usage": "",
        "benefits": "",
        "ingredients": "",
        "advantages": "",
        "application": "",
        "delivery": "",
        "faqs": {
            "package_contents": "",
            "usage_instructions": "",
            "side_effects": "",
            "contraindications": "",
            "storage": ""
        },
        "dynamic_headings": {}
    }
    
    # Get product details
    print("\n=== Generating Product Details ===")
    
    # Ingredients & Composition
    ingredients_result = call_assistant(client, INGREDIENTS_ASSISTANT_ID, content)
    if not ingredients_result.get("error", True):
        result["ingredients"] = clean_response(ingredients_result["response"])
        print("✓ Generated ingredients content")
    else:
        result["ingredients"] = "Informationen zu Inhaltsstoffen sind derzeit nicht vollständig verfügbar."
        print("✗ Failed to generate ingredients content")
    
    # Advantages & Special Features
    advantages_result = call_assistant(client, ADVANTAGES_ASSISTANT_ID, content)
    if not advantages_result.get("error", True):
        result["advantages"] = clean_response(advantages_result["response"])
        # Extract benefits from advantages if not explicitly available
        result["benefits"] = clean_response(advantages_result["response"])
        print("✓ Generated advantages content")
    else:
        result["advantages"] = "Informationen zu Vorteilen sind derzeit nicht vollständig verfügbar."
        result["benefits"] = "Informationen zu Vorteilen sind derzeit nicht vollständig verfügbar."
        print("✗ Failed to generate advantages content")
    
    # Application & Dosage
    application_result = call_assistant(client, APPLICATION_ASSISTANT_ID, content)
    if not application_result.get("error", True):
        result["application"] = clean_response(application_result["response"])
        # Extract usage from application if not explicitly available
        result["usage"] = clean_response(application_result["response"])
        print("✓ Generated application content")
    else:
        result["application"] = "Informationen zur Anwendung sind derzeit nicht vollständig verfügbar."
        result["usage"] = "Informationen zur Anwendung sind derzeit nicht vollständig verfügbar."
        print("✗ Failed to generate application content")
    
    # Delivery & Timeframe
    delivery_result = call_assistant(client, DELIVERY_ASSISTANT_ID, content)
    if not delivery_result.get("error", True):
        result["delivery"] = clean_response(delivery_result["response"])
        print("✓ Generated delivery content")
    else:
        result["delivery"] = "Informationen zur Lieferung sind derzeit nicht vollständig verfügbar."
        print("✗ Failed to generate delivery content")
    
    # Get FAQs
    print("\n=== Generating FAQs ===")
    
    # What's in the package?
    package_result = call_assistant(client, FAQ_PACKAGE_CONTENTS_ASSISTANT_ID, content)
    if not package_result.get("error", True):
        result["faqs"]["package_contents"] = clean_response(package_result["response"])
        print("✓ Generated package contents FAQ")
    else:
        result["faqs"]["package_contents"] = "Informationen zum Paketinhalt sind derzeit nicht vollständig verfügbar."
        print("✗ Failed to generate package contents FAQ")
    
    # How should it be used?
    usage_result = call_assistant(client, FAQ_USAGE_INSTRUCTIONS_ASSISTANT_ID, content)
    if not usage_result.get("error", True):
        result["faqs"]["usage_instructions"] = clean_response(usage_result["response"])
        print("✓ Generated usage instructions FAQ")
    else:
        result["faqs"]["usage_instructions"] = "Informationen zur Verwendung sind derzeit nicht vollständig verfügbar."
        print("✗ Failed to generate usage instructions FAQ")
    
    # Are there possible side effects?
    side_effects_result = call_assistant(client, FAQ_SIDE_EFFECTS_ASSISTANT_ID, content)
    if not side_effects_result.get("error", True):
        cleaned_response = clean_response(side_effects_result["response"])
        # Check if the response indicates no information is available
        if any(phrase in cleaned_response.lower() for phrase in [
                "keine spezifischen informationen", 
                "nicht erwähnt", 
                "keine informationen", 
                "keine angaben",
                "nicht explizit",
                "keine hinweise",
                "nicht genannt"
            ]):
            result["faqs"]["side_effects"] = "Bei bestimmungsgemäßem Gebrauch sind keine Nebenwirkungen bekannt. Bei individuellen Unverträglichkeiten oder Allergien sollten Sie die Anwendung abbrechen und einen Arzt konsultieren. Der 8-Hydroxydesoxyguanosin-Test dient nur der Analyse und nicht der Diagnose oder Behandlung von Krankheiten."
        else:
            result["faqs"]["side_effects"] = cleaned_response
        print("✓ Generated side effects FAQ")
    else:
        result["faqs"]["side_effects"] = "Bei bestimmungsgemäßem Gebrauch sind keine Nebenwirkungen bekannt. Bei individuellen Unverträglichkeiten oder Allergien sollten Sie die Anwendung abbrechen und einen Arzt konsultieren. Der 8-Hydroxydesoxyguanosin-Test dient nur der Analyse und nicht der Diagnose oder Behandlung von Krankheiten."
        print("✗ Failed to generate side effects FAQ")
    
    # Who should not use this product?
    contraindications_result = call_assistant(client, FAQ_CONTRAINDICATIONS_ASSISTANT_ID, content)
    if not contraindications_result.get("error", True):
        cleaned_response = clean_response(contraindications_result["response"])
        # Check if the response indicates no information is available
        if any(phrase in cleaned_response.lower() for phrase in [
                "keine spezifischen informationen", 
                "nicht erwähnt", 
                "keine informationen", 
                "keine angaben",
                "nicht explizit",
                "keine hinweise",
                "nicht genannt"
            ]):
            result["faqs"]["contraindications"] = "Der Test sollte nicht von Personen unter 18 Jahren ohne Aufsicht eines Erwachsenen durchgeführt werden. Bei bestehenden schweren Erkrankungen konsultieren Sie bitte vor der Durchführung einen Arzt. Personen, die bereits unter ärztlicher Behandlung stehen oder Medikamente einnehmen, die oxidativen Stress beeinflussen können, sollten vor der Verwendung des Tests ihren behandelnden Arzt konsultieren."
        else:
            result["faqs"]["contraindications"] = cleaned_response
        print("✓ Generated contraindications FAQ")
    else:
        result["faqs"]["contraindications"] = "Der Test sollte nicht von Personen unter 18 Jahren ohne Aufsicht eines Erwachsenen durchgeführt werden. Bei bestehenden schweren Erkrankungen konsultieren Sie bitte vor der Durchführung einen Arzt. Personen, die bereits unter ärztlicher Behandlung stehen oder Medikamente einnehmen, die oxidativen Stress beeinflussen können, sollten vor der Verwendung des Tests ihren behandelnden Arzt konsultieren."
        print("✗ Failed to generate contraindications FAQ")
    
    # How should it be stored?
    storage_result = call_assistant(client, FAQ_STORAGE_ASSISTANT_ID, content)
    if not storage_result.get("error", True):
        cleaned_response = clean_response(storage_result["response"])
        # Check if the response indicates no information is available
        if any(phrase in cleaned_response.lower() for phrase in [
                "keine spezifischen informationen", 
                "nicht erwähnt", 
                "keine informationen", 
                "keine angaben",
                "nicht explizit",
                "keine hinweise",
                "nicht genannt"
            ]):
            result["faqs"]["storage"] = "Bewahren Sie das Testkit an einem kühlen, trockenen Ort bei Temperaturen zwischen 2°C und 25°C auf, geschützt vor direkter Sonneneinstrahlung. Das Produkt darf nicht eingefroren werden. Die Proben sollten nach der Entnahme zeitnah versendet werden, um die Qualität der Ergebnisse zu gewährleisten. Außerhalb der Reichweite von Kindern aufbewahren."
        else:
            result["faqs"]["storage"] = cleaned_response
        print("✓ Generated storage FAQ")
    else:
        result["faqs"]["storage"] = "Bewahren Sie das Testkit an einem kühlen, trockenen Ort bei Temperaturen zwischen 2°C und 25°C auf, geschützt vor direkter Sonneneinstrahlung. Das Produkt darf nicht eingefroren werden. Die Proben sollten nach der Entnahme zeitnah versendet werden, um die Qualität der Ergebnisse zu gewährleisten. Außerhalb der Reichweite von Kindern aufbewahren."
        print("✗ Failed to generate storage FAQ")
    
    # Get dynamic headings and answers
    print("\n=== Generating Dynamic Content ===")
    headings = get_dynamic_headings(client, content)
    
    if headings:
        dynamic_answers = get_dynamic_heading_answers(client, content, headings)
        # Clean the dynamic answers
        cleaned_dynamic_answers = {}
        for heading, answer in dynamic_answers.items():
            cleaned_dynamic_answers[heading] = clean_response(answer)
        result["dynamic_headings"] = cleaned_dynamic_answers
        print(f"✓ Generated {len(cleaned_dynamic_answers)} dynamic answers")
    else:
        result["dynamic_headings"] = {}
        print("✗ Failed to generate dynamic headings")
    
    print("\n=== Generation Complete ===")
    
    # Final deep cleaning pass to ensure all JSON formatting markers are removed
    clean_nested_json(result)
    
    return result

def main():
    """
    Parse command line arguments and run the FAQ generator.
    """
    parser = argparse.ArgumentParser(description="Generate FAQs from product content using OpenAI")
    parser.add_argument("--content", type=str, help="Product content to generate FAQs from")
    parser.add_argument("--file", type=str, help="Path to file containing product content")
    parser.add_argument("--api-key", type=str, help="OpenAI API key (optional, can use OPENAI_API_KEY env var)")
    parser.add_argument("--output", type=str, help="Output JSON file path (optional)")
    
    args = parser.parse_args()
    
    # Get content from file or argument
    content = None
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {args.file}: {e}")
            exit(1)
    elif args.content:
        content = args.content
    else:
        print("Error: Either --content or --file must be provided")
        exit(1)
    
    # Generate FAQ
    result = generate_faq_from_content(args.api_key, content)
    
    # Print result and write to file if requested
    if not result.get("error", False):
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"Output written to {args.output}")
            except Exception as e:
                print(f"Error writing to file {args.output}: {e}")
        else:
            # Pretty print the JSON output
            print("\n=== Final Output ===")
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Error generating FAQ: {result.get('message', 'Unknown error')}")
        exit(1)

if __name__ == "__main__":
    main()