import requests
import time

def scrape_dr_urls():
    """
    Scrapes all search result URLs for a given query from the DR.dk API
    and saves them to a file.
    """
    base_url = "https://www.dr.dk/mu-online/api/1.0/search/programcard/page/search/"
    query = "israel"
    sort_by = "PublishTime"
    limit = 24  # The number of results per page, as observed in the API call
    offset = 0
    all_urls = []
    
    print(f"Starting scrape for query: '{query}'...")

    while True:
        # --- Set up parameters for the API request ---
        params = {
            "query": query,
            "sort": sort_by,
            "limit": limit,
            "offset": offset
        }

        try:
            # --- Make the GET request to the API ---
            response = requests.get(base_url, params=params)
            # Raise an exception for bad status codes (4xx or 5xx)
            response.raise_for_status() 

            # --- Parse the JSON response ---
            data = response.json()
            items = data.get("Items", [])

            # --- Check if we have reached the end of the results ---
            if not items:
                print("No more items found. Ending scrape.")
                break
            
            # --- Extract URLs and add them to our list ---
            page_urls = []
            for item in items:
                if "ProgramUrl" in item:
                    # The API returns a relative URL, so we construct the full URL
                    full_url = f"https://www.dr.dk{item['ProgramUrl']}"
                    page_urls.append(full_url)
            
            all_urls.extend(page_urls)
            print(f"Found {len(page_urls)} URLs on this page. Total found: {len(all_urls)}")

            # --- Prepare for the next page ---
            offset += limit
            
            # --- Be a good internet citizen and wait a bit before the next request ---
            time.sleep(0.5) 

        except requests.exceptions.RequestException as e:
            print(f"An error occurred with the request: {e}")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break

    # --- Save the collected URLs to a file ---
    if all_urls:
        file_path = "dr_urls.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            for url in all_urls:
                f.write(f"{url}\n")
        print(f"\nSuccessfully saved {len(all_urls)} URLs to {file_path}")
    else:
        print("\nNo URLs were found to save.")


if __name__ == "__main__":
    scrape_dr_urls()
