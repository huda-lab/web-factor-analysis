import json
import os
import re
import csv
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def normalize_url(url):
    """
    Normalizes a URL by removing specific query parameters (like utm_source).
    This ensures that 'example.com?utm_source=chatgpt.com' and 'example.com' are treated as the same URL.
    """
    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Remove 'utm_source' if it exists
        if 'utm_source' in query_params:
            del query_params['utm_source']
            
        # Reconstruct the query string
        new_query = urlencode(query_params, doseq=True)
        
        # Reconstruct the full URL
        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
        
        # Remove trailing '?' if query is empty now
        if new_url.endswith('?'):
            new_url = new_url[:-1]
            
        return new_url
    except Exception:
        # If parsing fails, return original
        return url

def extract_urls(text):
    # Regex designed to capture URLs while trying to avoid trailing punctuation common in text
    # It catches http/https/www, then non-space characters.
    # We refine the match by stripping trailing punctuation that usually isn't part of the URL.
    
    # Basic pattern
    pattern = r'(https?://[^\s<>"]+|www\.[^\s<>"]+)'
    matches = re.findall(pattern, text)
    
    cleaned_urls = []
    for url in matches:
        # Remove trailing punctuation that might have been matched
        # We strip .,;)]} but we try to respect balanced parens if possible, 
        # but for simplicity we just strip common sentence enders if they are at the end.
        
        while len(url) > 0 and url[-1] in '.,;)]}"\'':
            url = url[:-1]
        
        if url:
             cleaned_urls.append(url)
             
    return cleaned_urls

def is_main_page(url):
    """
    Checks if a URL is just the main page (e.g. www.example.com, example.com/, example.com/index.html).
    """
    try:
        if not url.startswith('http'):
            # Add valid scheme for parsing if missing (e.g. www.google.com)
            parsed = urlparse('http://' + url)
        else:
            parsed = urlparse(url)
            
        path = parsed.path
        # Remove trailing slash for comparison
        if path.endswith('/'):
            path = path[:-1]
            
        # Consider empty path or just index.html/php/etc as main page
        is_root = path == '' or path == '/' or path.lower() in ['/index.html', '/index.php', '/index.htm', '/home']
        
        # Also ensure no query parameters or fragments that might make it specific content
        # But wait, main pages can have query params (e.g. ?lang=en). 
        # The prompt examples are "www.pacegallery.com", "www.bxscience.edu".
        # Let's be strict: Main page means essentially no path and no significant query.
        
        return is_root and not parsed.query and not parsed.fragment
    except Exception:
        return False

def main():
    folder = 'conversations_files'
    cited_rows = []
    uncited_rows = []
    
    # Prepare CSV headers
    headers = ['conversation_id', 'title', 'url']

    files = [f for f in os.listdir(folder) if f.endswith('.json')]
    print(f"Found {len(files)} conversation files.")

    for filename in files:
        filepath = os.path.join(folder, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue

        title = data.get('title', 'Untitled')
        conversation_id = data.get('conversation_id', 'Unknown')
        
        # 1. Identify Cited URLs
        file_cited_urls = set()
        normalized_cited_urls = set()
        
        mapping = data.get('mapping', {})
        
        # Walk through the conversation mapping to find content_references
        for node_id, node in mapping.items():
            if not node or 'message' not in node or not node['message']:
                continue
            
            message = node['message']
            metadata = message.get('metadata', {})
            content_references = metadata.get('content_references', [])
            
            for ref in content_references:
                if 'items' in ref:
                    for item in ref['items']:
                        if 'url' in item:
                            url = item['url']
                            # Normalize immediately for storage
                            norm_url = normalize_url(url)
                            if not is_main_page(norm_url):
                                file_cited_urls.add(norm_url)
                                normalized_cited_urls.add(norm_url)
        
        # 2. Identify All URLs in the file (by walking the JSON text content)
        file_all_urls = set()
        
        def walk_json(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    walk_json(v)
            elif isinstance(obj, list):
                for item in obj:
                    walk_json(item)
            elif isinstance(obj, str):
                found = extract_urls(obj)
                for url in found:
                    norm_url = normalize_url(url)
                    file_all_urls.add(norm_url)

        walk_json(data)
        
        # 3. Determine Uncited URLs
        # Uncited = All URLs where (normalized version) is NOT in (normalized cited urls)
        file_uncited_urls = set()
        for url in file_all_urls:
            # url is already normalized here
            if url not in normalized_cited_urls:
                if not is_main_page(url):
                    file_uncited_urls.add(url)
        
        # 4. Add to rows
        for url in file_cited_urls:
            cited_rows.append({'conversation_id': conversation_id, 'title': title, 'url': url})
            
        for url in file_uncited_urls:
            uncited_rows.append({'conversation_id': conversation_id, 'title': title, 'url': url})

    # Write CSVs
    # Sort distinct rows by title to make it cleaner, although DictWriter writes in order.
    # We want to ensure uniqueness of the PAIR (title, url) just in case.
    # Actually, sets above guarantee uniqueness per filte.
    
    with open('cited_urls.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(cited_rows)
    
    print(f"Written {len(cited_rows)} cited URLs to cited_urls.csv")

    with open('uncited_urls.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(uncited_rows)

    print(f"Written {len(uncited_rows)} uncited URLs to uncited_urls.csv")

if __name__ == "__main__":
    main()
