import os
import requests
import collections
import time
import re
import random

# --- Robustness Features ---

# A list of common User-Agents to rotate through. This makes our requests look
# like they are coming from different browsers, not a single script.
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
]

# File to store the index of the last successfully downloaded URL
PROGRESS_FILE = "archive_progress.txt"
# File to log all URLs that result in a 404 error
ERROR_404_FILE = "404_errors.txt"
# File to log all URLs that cause a redirect loop
REDIRECT_ERROR_FILE = "redirect_errors.txt"

def sanitize_for_filename(text):
    """
    Removes or replaces characters from a string to make it a valid filename.
    """
    text = re.sub(r'https?://[^/]+/', '', text)
    return re.sub(r'[^a-zA-Z0-9_-]', '_', text)

def sanitize_for_foldername(text):
    """
    Removes or replaces characters from a string to make it a valid folder name.
    """
    text = text.replace("https://", "").replace("http://", "")
    text = re.sub(r'[^a-zA-Z0-9_-]', '_', text)
    return text.strip('_')

def archive_articles(input_filename="dr_urls.txt", base_output_dir="archive"):
    """
    Downloads the raw HTML of URLs from a file and saves them into
    organized folders. Includes features for robustness and resuming
    an interrupted session.

    Args:
        input_filename (str): The file containing URLs.
        base_output_dir (str): The root directory to save the archive.
    """
    start_index = 0
    # --- Resume Logic ---
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            try:
                last_completed_index = int(f.read().strip())
                start_index = last_completed_index + 1
                
                resume_choice = input(
                    f"A previous session was interrupted. "
                    f"Resume from line {start_index}? (y/n): "
                ).lower()
                
                if resume_choice != 'y':
                    print("Starting from the beginning.")
                    start_index = 0
                else:
                    print(f"Resuming download from line {start_index}.")

            except (ValueError, IndexError):
                print("Could not read progress file. Starting from the beginning.")
    
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

    link_type_counts = collections.Counter()
    for url in urls:
        last_slash_index = url.rfind('/')
        if last_slash_index != -1 and last_slash_index < len(url) - 1:
            link_type = url[:last_slash_index + 1]
            link_type_counts[link_type] += 1
    
    folder_mapping = {}
    for i, (link_type, count) in enumerate(link_type_counts.most_common(), 1):
        prefix = f"{i:03d}"
        sanitized_type = sanitize_for_foldername(link_type)
        folder_name = f"{prefix}_{sanitized_type}"
        folder_mapping[link_type] = folder_name
        print(f"Mapped type '{link_type}' ({count} files) to folder '{folder_name}'")

    # --- Phase 2: Download and save articles ---
    print("\n--- Phase 2: Downloading and archiving articles ---")
    
    os.makedirs(base_output_dir, exist_ok=True)
    
    session = requests.Session()
    total_urls = len(urls)
    max_retries = 3

    for i in range(start_index, total_urls):
        url = urls[i]
        
        url_processed_successfully = False

        try:
            last_slash_index = url.rfind('/')
            if last_slash_index == -1 or last_slash_index >= len(url) - 1:
                print(f"({i+1}/{total_urls}) Skipping invalid URL format: {url}")
                url_processed_successfully = True
                continue

            link_type = url[:last_slash_index + 1]
            target_folder_name = folder_mapping.get(link_type)

            if not target_folder_name:
                print(f"({i+1}/{total_urls}) Warning: Could not find folder mapping for URL: {url}")
                url_processed_successfully = True
                continue
                
            full_folder_path = os.path.join(base_output_dir, target_folder_name)
            os.makedirs(full_folder_path, exist_ok=True)

            url_slug = url[last_slash_index + 1:]
            filename = sanitize_for_filename(url_slug) + ".html"
            file_path = os.path.join(full_folder_path, filename)

            if os.path.exists(file_path):
                print(f"({i+1}/{total_urls}) Skipping already downloaded file: {file_path}")
                url_processed_successfully = True
                continue

            for attempt in range(max_retries):
                try:
                    headers = {'User-Agent': random.choice(USER_AGENTS)}
                    print(f"({i+1}/{total_urls}) Downloading {url} (Attempt {attempt+1})")
                    response = session.get(url, headers=headers, timeout=20)
                    response.raise_for_status()

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    
                    url_processed_successfully = True
                    break 
                
                except requests.exceptions.TooManyRedirects as e:
                    print(f"  -> Too many redirects. Skipping and logging.")
                    with open(REDIRECT_ERROR_FILE, 'a', encoding='utf-8') as error_f:
                        error_f.write(f"{url}\n")
                    url_processed_successfully = True
                    break

                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 404:
                        print(f"  -> URL not found (404). Skipping and logging.")
                        with open(ERROR_404_FILE, 'a', encoding='utf-8') as error_f:
                            error_f.write(f"{url}\n")
                        
                        url_processed_successfully = True
                        break
                    else:
                        print(f"  -> HTTP error on attempt {attempt+1}: {e}")
                        if attempt < max_retries - 1:
                            time.sleep(2 ** attempt)
                
                except requests.exceptions.RequestException as e:
                    print(f"  -> Network error on attempt {attempt+1}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
            
        finally:
            if url_processed_successfully:
                with open(PROGRESS_FILE, 'w') as f:
                    f.write(str(i))
                time.sleep(random.uniform(0.5, 1.5))
            else:
                print(f"Failed to download {url} after multiple attempts. Exiting.")
                break 

    else: 
        print("\n--- Archiving complete! ---")
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)

if __name__ == "__main__":
    archive_articles()
