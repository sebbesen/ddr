import requests
import time
import json

def scrape_dr_urls_graphql():
    """
    Scrapes all search result URLs for a given query from the DR.dk GraphQL API
    and saves them to a file.
    """
    graphql_url = "https://www.dr.dk/tjenester/steffi/graphql"

    # This is the complex GraphQL query required by the API.
    graphql_query = """
    fragment ArticleResultFields on Article { type: __typename urn urlPathId title format publications { ...on ArticlePublication { breaking live serviceChannel { urn } } } summary startDate teaserImage { default { url managedUrl width height } } head { type: __typename ... on MediaComponent { resource { type: __typename ... on LiveMedia { urn mediaType } ... on Clip { urn mediaType durationInMilliseconds } ... on ClipBundle { items(limit: 1) { __typename urn durationInMilliseconds } } } } ... on ImageCollectionComponent { images { default: image(key: "default") { type: __typename url width height managedUrl } } } ... on RatingComponent { rating } } contributions(limit: 1) { agent { ... on Person { name } } role } site { url urn title presentation { isShortFormat colors teaserImage { default: image(key: "default") { url managedUrl width height } } } } } fragment RecipeResultFields on Recipe { title url image { url } startDate } fragment UnknownSearchResultFields on UnknownSearchResult { title url label image { url width height managedUrl } } fragment MusicArtistResultFields on MusicArtist { url name image { url width height managedUrl } } query SearchPageDRDK($query: String! $limit: Int! $offset: Int! $sort: SearchSort) { drdk: search(query: $query logQuery: $query limit: $limit offset: $offset products: ["drdk"] sort: $sort) { totalCount results: nodes { type: __typename ... on Article { ...ArticleResultFields } ... on Recipe { ...RecipeResultFields } ... on MusicArtist { ...MusicArtistResultFields } ... on UnknownSearchResult { ...UnknownSearchResultFields } } spellCheck } }
    """
    
    # Mimic browser headers to ensure the request is accepted.
    headers = {
        'accept': '*/*',
        'accept-language': 'en,da;q=0.9,de;q=0.8',
        'referer': 'https://www.dr.dk/soeg?query=israel&sort=PublishTime',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'if-none-match': 'W/"2c99-kyZZ2hsVP8B3nRcfjxdEMQzEevs"',
    }

    # --- Scraper settings ---
    query_term = "israel"
    sort_by = "PublishTime"
    limit = 10
    offset = 0
    all_urls = []
    
    # Use a session object to persist cookies across requests
    session = requests.Session()
    session.headers.update(headers)
    
    print(f"Starting GraphQL scrape for query: '{query_term}'...")

    while True:
        variables = {
            "query": query_term,
            "sort": sort_by,
            "limit": limit,
            "offset": offset
        }

        params = {
            'query': graphql_query,
            'variables': json.dumps(variables)
        }

        try:
            # Use the session object to make the request
            response = session.get(graphql_url, params=params)
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                print(f"API returned an error at offset {offset}: {data['errors']}")
                break

            search_data = data.get("data", {}).get("drdk")

            if not search_data:
                print(f"Could not find 'data' or 'drdk' in API response at offset {offset}. Ending scrape.")
                print(f"Problematic response content: {response.text}")
                break

            results = search_data.get("results", [])

            if not results:
                print("No more items found. Ending scrape.")
                break
            
            page_urls = []
            for item in results:
                # --- FIX: Check if the item is None (null) before processing ---
                if not item:
                    continue # Skip this iteration if the item is null

                url = item.get('url')
                if not url and item.get('urlPathId'):
                    url = f"https://www.dr.dk/{item.get('urlPathId')}"

                if url:
                    if not url.startswith('http'):
                        url = f"https://www.dr.dk{url}"
                    page_urls.append(url)
            
            all_urls.extend(page_urls)
            print(f"Found {len(page_urls)} URLs on this page. Total found: {len(all_urls)}")

            offset += limit
            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"A network error occurred: {e}")
            break
        except json.JSONDecodeError:
            print(f"Failed to decode JSON. Response text: {response.text}")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            if 'response' in locals():
                print(f"Content that caused the error: {response.text}")
            break

    if all_urls:
        file_path = "dr_urls.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            for url in all_urls:
                f.write(f"{url}\n")
        print(f"\nSuccessfully saved {len(all_urls)} URLs to {file_path}")
    else:
        print("\nNo URLs were found to save.")


if __name__ == "__main__":
    scrape_dr_urls_graphql()
