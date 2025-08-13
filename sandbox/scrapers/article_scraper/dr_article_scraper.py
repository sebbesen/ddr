import os
import requests
import collections
import time
import re

def sanitize_for_filename(text):
    """
    Removes or replaces characters from a string to make it a valid filename.
    """
    # Remove the protocol and domain part for the filename itself
    text = re.sub(r'https?://[^/]+/', '', text)
    # Replace any characters that are not letters, numbers, hyphens, or underscores
    return re.sub(r'[^a-zA-Z0-9_-]', '_', text)

def sanitize_for_foldername(text):
    """
    Removes or replaces characters from a string to make it a valid folder name.
    """
    # Remove protocol
    text = text.replace("https://", "").replace("http://", "")
    # Replace slashes and other invalid characters with underscores
    text = re.sub(r'[^a-zA-Z0-9_-]', '_', text)
    # Clean up any trailing underscores that might result
    return text.strip('_')

def archive_articles(input_filename="dr_urls.txt", base_output_dir="archive"):
    """
    Downloads the raw HTML of URLs from a file and saves them into
    organized folders based on their link type frequency.

    Args:
        input_filename (str): The file containing URLs.
        base_output_dir (str): The root directory to save the archive.
    """
    # --- Phase 1: Analyze URL types and determine folder order ---
    print("--- Phase 1: Analyzing URL types and frequencies ---")
    
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: The input file '{input_filename}' was not found.")
        return

    if not urls:
        print("The URL file is empty. Nothing to do.")
        return

    # Count frequencies of each link type
    link_type_counts = collections.Counter()
    for url in urls:
        last_slash_index = url.rfind('/')
        if last_slash_index != -1 and last_slash_index < len(url) - 1:
            link_type = url[:last_slash_index + 1]
            link_type_counts[link_type] += 1
    
    # Create the mapping from link type to numbered folder name
    folder_mapping = {}
    # .most_common() gives a list of (item, count) tuples, sorted by count
    for i, (link_type, count) in enumerate(link_type_counts.most_common(), 1):
        # Format number with leading zeros (e.g., 001, 012)
        prefix = f"{i:03d}"
        sanitized_type = sanitize_for_foldername(link_type)
        folder_name = f"{prefix}_{sanitized_type}"
        folder_mapping[link_type] = folder_name
        print(f"Mapped type '{link_type}' ({count} files) to folder '{folder_name}'")

    # --- Phase 2: Download and save articles ---
    print("\n--- Phase 2: Downloading and archiving articles ---")
    
    # Ensure the base archive directory exists
    os.makedirs(base_output_dir, exist_ok=True)
    
    session = requests.Session() # Use a session for connection pooling
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for i, url in enumerate(urls):
        try:
            last_slash_index = url.rfind('/')
            if last_slash_index == -1 or last_slash_index >= len(url) - 1:
                print(f"Skipping invalid URL format: {url}")
                continue

            link_type = url[:last_slash_index + 1]
            target_folder_name = folder_mapping.get(link_type)

            if not target_folder_name:
                print(f"Warning: Could not find folder mapping for URL: {url}")
                continue
                
            # Create the full path for the folder
            full_folder_path = os.path.join(base_output_dir, target_folder_name)
            os.makedirs(full_folder_path, exist_ok=True)

            # Create a clean filename from the last part of the URL
            url_slug = url[last_slash_index + 1:]
            filename = sanitize_for_filename(url_slug) + ".html"
            file_path = os.path.join(full_folder_path, filename)

            # Check if file already exists to avoid re-downloading
            if os.path.exists(file_path):
                print(f"({i+1}/{len(urls)}) Skipping already downloaded file: {file_path}")
                continue

            # Download the content
            print(f"({i+1}/{len(urls)}) Downloading {url} -> {file_path}")
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status() # Raise an exception for bad status codes

            # Save the raw HTML
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Be a good citizen and don't hammer the server
            time.sleep(0.25)

        except requests.exceptions.RequestException as e:
            print(f"Error downloading {url}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred for URL {url}: {e}")

    print("\n--- Archiving complete! ---")

if __name__ == "__main__":
    archive_articles()
