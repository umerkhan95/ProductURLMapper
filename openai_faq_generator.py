#!/usr/bin/env python3
"""
OpenAI FAQ Generator

This script takes content from a product page, sends it to an OpenAI
assistant, and generates structured FAQ data in JSON format.

The assistant is designed to generate FAQs and product information
from website content in German.

Usage:
    - As standalone: python openai_faq_generator.py --content "Product content..."
    - From other modules: import and use generate_faq_from_content
"""

import os
import json
import time
import argparse
from typing import Dict, Any, Optional

# Check if OpenAI package is installed, if not provide installation instructions
try:
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI package is not installed.")
    print("Please install it using: pip install openai")
    exit(1)

# OpenAI Assistant ID
ASSISTANT_ID = "asst_RgJy51O86dc91CRkzlvQO5jY"  # Website Content FAQ Generator

def generate_faq_from_content(api_key: Optional[str], content: str) -> Dict[str, Any]:
    """
    Send content to OpenAI assistant and retrieve the FAQ response.
    
    Args:
        api_key: OpenAI API key (if None, will try to use from environment)
        content: Text content to send to the assistant
        
    Returns:
        JSON response from the assistant with structured FAQ data
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
    
    # Create a thread
    thread = client.beta.threads.create()
    
    # Add a message to the thread with instructions
    prompt = """
    Bitte extrahiere aus dem folgenden Produktinhalt strukturierte Informationen für ein deutsches Gesundheitsprodukt.
    Analysiere den Text und extrahiere Antworten für diese Fragen:
    
    1. Wofür wird es verwendet? (usage)
    2. Was sind die Vorteile? (benefits)
    
    3. Produktdetails:
       - INHALTSSTOFFE & ZUSAMMENSETZUNG (ingredients)
       - VORTEILE & BESONDERHEITEN (advantages)
       - ANWENDUNG & DOSIERUNG (application)
       - LIEFERUNG & ZEITRAHMEN (delivery)
    
    4. Häufig gestellte Fragen (FAQs):
       - Was enthält die Packung? (package_contents)
       - Wie sollte es verwendet werden? (usage_instructions)
       - Gibt es mögliche Nebenwirkungen? (side_effects)
       - Wer sollte dieses Produkt nicht verwenden? (contraindications)
       - Wie sollte es gelagert werden? (storage)
    
    Dies ist der zu analysierende Inhalt:
    """
    
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"{prompt}\n\n{content}"
    )
    
    # Add instructions for output format
    format_instructions = """
    Gib die Antworten als JSON-Objekt in folgendem Format zurück:
    
    ```json
    {
      "usage": "Text...",
      "benefits": "Text...",
      "ingredients": "Text...",
      "advantages": "Text...",
      "application": "Text...",
      "delivery": "Text...",
      "faqs": {
        "package_contents": "Text...",
        "usage_instructions": "Text...",
        "side_effects": "Text...",
        "contraindications": "Text...",
        "storage": "Text..."
      }
    }
    ```
    
    WICHTIG: Stelle sicher, dass alle Felder ausgefüllt sind. Kein Feld darf leer bleiben.
    Wenn du keine spezifischen Informationen zu einem Feld findest:
    - Für Produktdetails: Gib einen allgemeinen informativen Text an, der für diese Art von Produkt typisch ist.
    - Für FAQ-Antworten: Erstelle eine hilfreiche, allgemeine Antwort basierend auf üblichen Informationen für ähnliche Produkte.
    
    Alle Ausgaben müssen auf Deutsch sein und jedes Feld muss mindestens einen Satz enthalten.
    """
    
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=format_instructions
    )
    
    # Run the assistant
    print("Starting OpenAI assistant for FAQ generation...")
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )
    
    # Poll until the run completes
    start_time = time.time()
    while run.status in ["queued", "in_progress"]:
        elapsed = time.time() - start_time
        if elapsed > 180:  # 3 minutes timeout
            return {
                "error": True,
                "message": f"Timeout after waiting {elapsed:.1f} seconds. Last status: {run.status}"
            }
        
        # Print progress updates
        if run.status == "in_progress":
            print(f"Processing content... ({elapsed:.1f}s)")
        else:
            print(f"Waiting in queue... ({elapsed:.1f}s)")
            
        time.sleep(2)  # Wait for 2 seconds before checking again
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
    
    # If there was an error, return the error information
    if run.status != "completed":
        return {
            "error": True,
            "status": run.status,
            "details": run.last_error if hasattr(run, "last_error") else "Unknown error"
        }
    
    # Retrieve the messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    
    # Get the last assistant message
    assistant_messages = [msg for msg in messages.data if msg.role == "assistant"]
    
    if assistant_messages:
        last_message = assistant_messages[0]
        response_content = last_message.content[0].text.value
        
        # Try to parse the response as JSON
        try:
            # Remove any markdown code block formatting if present
            if "```json" in response_content:
                response_content = response_content.split("```json", 1)[1]
            if "```" in response_content:
                response_content = response_content.split("```", 1)[0]
            
            # Strip whitespace
            response_content = response_content.strip()
            
            # Parse the JSON
            result = json.loads(response_content)
            
            # Validate and fill any missing fields
            required_fields = ["usage", "benefits", "ingredients", "advantages", "application", "delivery"]
            required_faq_fields = ["package_contents", "usage_instructions", "side_effects", "contraindications", "storage"]
            
            # Create faqs object if it doesn't exist
            if "faqs" not in result:
                result["faqs"] = {}
            
            # Set default values for any missing fields
            for field in required_fields:
                if field not in result or not result[field]:
                    result[field] = f"Informationen zu {field} sind derzeit nicht vollständig verfügbar. Bitte kontaktieren Sie uns für weitere Details."
            
            for field in required_faq_fields:
                if field not in result["faqs"] or not result["faqs"][field]:
                    if field == "package_contents":
                        result["faqs"][field] = "Die genauen Packungsinhalte entnehmen Sie bitte der Produktbeschreibung oder kontaktieren Sie unseren Kundenservice."
                    elif field == "usage_instructions":
                        result["faqs"][field] = "Für detaillierte Anwendungshinweise lesen Sie bitte die Produktbeschreibung oder die beiliegende Packungsbeilage."
                    elif field == "side_effects":
                        result["faqs"][field] = "Bei bestimmungsgemäßem Gebrauch sind keine Nebenwirkungen bekannt. Bei individuellen Unverträglichkeiten brechen Sie die Anwendung ab und konsultieren Sie einen Arzt."
                    elif field == "contraindications":
                        result["faqs"][field] = "Das Produkt sollte nicht verwendet werden bei bekannten Allergien gegen einen der Inhaltsstoffe. Im Zweifelsfall konsultieren Sie bitte einen Arzt."
                    elif field == "storage":
                        result["faqs"][field] = "Bitte lagern Sie das Produkt kühl, trocken und lichtgeschützt, außerhalb der Reichweite von Kindern."
            
            result["error"] = False
            return result
        except json.JSONDecodeError as e:
            # If it's not valid JSON, return the raw text and error
            return {
                "error": True,
                "message": f"Failed to parse JSON: {str(e)}",
                "raw_response": response_content
            }
    
    return {"error": True, "message": "No assistant response found"}


def main():
    """Main function to parse arguments and run the FAQ generator."""
    parser = argparse.ArgumentParser(description='Generate FAQs from content using OpenAI assistant')
    parser.add_argument('--file', type=str, 
                        help='Path to text file containing product content')
    parser.add_argument('--content', type=str,
                        help='Direct product content string')
    parser.add_argument('--output', type=str,
                        help='Output JSON file path (if not specified, prints to console)')
    args = parser.parse_args()
    
    # Get content from file or direct input
    content = None
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"Read content from {args.file}")
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            return
    elif args.content:
        content = args.content
    else:
        print("Error: Either --file or --content must be specified")
        parser.print_help()
        return
    
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please set your OpenAI API key with:")
        print("  export OPENAI_API_KEY='your-api-key'")
        return
    
    # Send to OpenAI assistant
    print(f"Sending content to OpenAI assistant (ID: {ASSISTANT_ID})...")
    response = generate_faq_from_content(api_key, content)
    
    # Handle the response
    if args.output:
        # Save to file
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(response, f, indent=2, ensure_ascii=False)
            print(f"Response saved to {args.output}")
        except Exception as e:
            print(f"Error saving output: {str(e)}")
            print("\nResponse from assistant:")
            print(json.dumps(response, indent=2, ensure_ascii=False))
    else:
        # Print to console
        print("\nResponse from assistant:")
        print(json.dumps(response, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()