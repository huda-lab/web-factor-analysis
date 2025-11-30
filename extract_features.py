#!/usr/bin/env python3
"""
Feature extraction script using Gemini and a custom prompt.
"""

import argparse
import json
import os
import sys
import datetime
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

# Import the prompt
try:
    from prompt import prompt as BASE_PROMPT
except ImportError:
    # Fallback if running from a different directory context
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from prompt import prompt as BASE_PROMPT

# Load environment variables
load_dotenv()

def setup_gemini(api_key):
    """Configure Gemini API."""
    genai.configure(api_key=api_key)
    # Using the flash model for speed and efficiency
    return genai.GenerativeModel('gemini-2.5-flash')

def clean_text(text):
    """Clean extracted text."""
    # Simple cleaning to remove excessive whitespace
    import re
    cleaned = re.sub(r'\s+', ' ', text).strip()
    return cleaned

def fetch_content(url, timeout=15):
    """Fetch and extract main text content from URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            script.decompose()
            
        # Get text
        text = soup.get_text(separator=' ')
        
        # Clean text
        cleaned_text = clean_text(text)
        
        # Truncate if too long (Gemini Flash has a large context, but let's be reasonable)
        # 100k chars is usually plenty for a web page
        if len(cleaned_text) > 100000:
            cleaned_text = cleaned_text[:100000]
            
        return cleaned_text, "success"
        
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return str(e), "failed"

def extract_features(url, api_key):
    """
    Extract features from the given URL using Gemini.
    """
    model = setup_gemini(api_key)
    
    print(f"Fetching content from {url}...", file=sys.stderr)
    page_text, status = fetch_content(url)
    
    if status == "failed":
        return {
            "meta": {
                "url": url,
                "timestamp": datetime.datetime.now().isoformat(),
                "language": "unknown",
                "fetch_status": "failed"
            },
            "factors": [],
            "summary": {
                "indexability_score": 0,
                "key_observations": f"Failed to fetch content: {page_text}",
                "content_gaps": ["Content fetch failed"]
            }
        }
    
    # Prepare the prompt
    # Inject the URL and Content into the prompt
    final_prompt = BASE_PROMPT.replace("PUT_URL_HERE", url)
    
    # We need to pass the content to the model. 
    # The prompt says "based strictly on the provided `page_html` and `page_text`"
    # We will append the text to the prompt.
    
    final_prompt += f"\n\n--- PAGE TEXT START ---\n{page_text}\n--- PAGE TEXT END ---\n"
    
    print("Sending request to Gemini...", file=sys.stderr)
    try:
        response = model.generate_content(final_prompt, generation_config={"response_mime_type": "application/json"})
        
        # Parse JSON
        try:
            result = json.loads(response.text)
            return result
        except json.JSONDecodeError:
            # Fallback cleanup if needed (though response_mime_type should handle it)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            return json.loads(text)
            
    except Exception as e:
        print(f"Error calling Gemini: {e}", file=sys.stderr)
        return {
            "meta": {
                "url": url,
                "timestamp": datetime.datetime.now().isoformat(),
                "language": "unknown",
                "fetch_status": "failed"
            },
            "factors": [],
            "summary": {
                "indexability_score": 0,
                "key_observations": f"LLM generation failed: {str(e)}",
                "content_gaps": ["LLM processing failed"]
            }
        }

def main():
    parser = argparse.ArgumentParser(description="Extract features from a webpage using Gemini.")
    parser.add_argument("url", help="The URL to analyze")
    parser.add_argument("--api-key", help="Gemini API Key (overrides env var)")
    parser.add_argument("--output", help="Output file path (optional)")
    
    args = parser.parse_args()
    
    api_key = args.api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found. Set it in .env or pass --api-key.", file=sys.stderr)
        sys.exit(1)
        
    result = extract_features(args.url, api_key)
    
    json_output = json.dumps(result, indent=2)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(json_output)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(json_output)

if __name__ == "__main__":
    main()
