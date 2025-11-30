#!/usr/bin/env python3
"""
Extract all unique safe_urls from the last content_references array in each conversation file.
Outputs CSV with conversation title and URL.
"""

import json
import csv
from pathlib import Path
from typing import Set, List, Any, Dict, Tuple


def find_last_content_references(data: Any, path: str = "") -> List[dict]:
    """
    Recursively find all content_references arrays in the JSON structure.
    Returns the last one found.
    """
    content_refs = []
    
    def traverse(obj, current_path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "content_references" and isinstance(value, list):
                    content_refs.append((current_path, value))
                traverse(value, f"{current_path}.{key}" if current_path else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                traverse(item, f"{current_path}[{i}]" if current_path else f"[{i}]")
    
    traverse(data)
    return content_refs[-1][1] if content_refs else []


def extract_safe_urls_from_content_references(content_refs: List[dict]) -> Set[str]:
    """Extract all safe_urls from a content_references array."""
    urls = set()
    for ref in content_refs:
        if isinstance(ref, dict) and "safe_urls" in ref:
            safe_urls = ref["safe_urls"]
            if isinstance(safe_urls, list):
                urls.update(safe_urls)
    return urls


def main():
    conversations_dir = Path(__file__).parent / "conversations"
    # Store URLs grouped by file (file order maintained)
    file_urls: List[Tuple[str, List[str]]] = []  # List of (title, [urls]) tuples
    
    # Process each JSON file
    json_files = sorted(conversations_dir.glob("*.json"))
    print(f"Processing {len(json_files)} conversation files...")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get conversation title
            conversation_title = data.get("title", "Untitled")
            
            # Find the last content_references array
            last_content_refs = find_last_content_references(data)
            
            if last_content_refs:
                # Extract safe_urls from this content_references array
                urls = extract_safe_urls_from_content_references(last_content_refs)
                if urls:
                    # Sort URLs for this file
                    sorted_urls = sorted(urls)
                    # Store with conversation title
                    file_urls.append((conversation_title, sorted_urls))
                    print(f"  {json_file.name}: Found {len(urls)} URLs (title: {conversation_title})")
            else:
                print(f"  {json_file.name}: No content_references found")
                
        except json.JSONDecodeError as e:
            print(f"  {json_file.name}: Error parsing JSON - {e}")
        except Exception as e:
            print(f"  {json_file.name}: Error - {e}")
    
    # Count total URLs
    total_urls = sum(len(urls) for _, urls in file_urls)
    print(f"\nTotal unique URLs found: {total_urls}")
    print(f"Across {len(file_urls)} conversation files")
    
    # Save to CSV file
    output_file = Path(__file__).parent / "unique_safe_urls.csv"
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["conversation_title", "url"])  # Header row
        # Write URLs grouped by file (maintaining file order)
        for title, urls in file_urls:
            for url in urls:
                writer.writerow([title, url])
    
    print(f"Results saved to: {output_file}")
    
    # Also print first few URLs as preview
    if file_urls:
        print("\nFirst 5 URLs with their conversation titles:")
        count = 0
        for title, urls in file_urls:
            for url in urls:
                print(f"  {title}: {url}")
                count += 1
                if count >= 5:
                    break
            if count >= 5:
                break
        if total_urls > 5:
            print(f"  ... and {total_urls - 5} more URLs")


if __name__ == "__main__":
    main()

