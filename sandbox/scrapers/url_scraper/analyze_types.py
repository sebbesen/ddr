import collections

def analyze_link_types(input_filename="dr_urls.txt"):
    """
    Reads a file of URLs, categorizes them based on the path before the
    final part, and prints a count of each category.

    Args:
        input_filename (str): The name of the file containing URLs,
                              one per line.
    """
    # A Counter is a special dictionary for counting hashable objects.
    link_type_counts = collections.Counter()

    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            urls = f.readlines()
    except FileNotFoundError:
        print(f"Error: The input file '{input_filename}' was not found.")
        print("Please make sure the file from the previous script is in the same directory.")
        return

    print(f"Analyzing URLs from '{input_filename}'...")

    # Process each URL from the file
    for url in urls:
        # .strip() removes leading/trailing whitespace, including the newline character
        clean_url = url.strip()
        
        # Ensure the line is not empty
        if not clean_url:
            continue

        # Find the position of the last '/' in the URL
        last_slash_index = clean_url.rfind('/')

        # Check if a '/' was found and it's not the last character
        if last_slash_index != -1 and last_slash_index < len(clean_url) - 1:
            # The "type" is the part of the string up to and including the last '/'
            link_type = clean_url[:last_slash_index + 1]
            
            # Increment the count for this type in our counter
            link_type_counts[link_type] += 1

    # --- Print the results ---
    if not link_type_counts:
        print("No valid URLs were found to analyze.")
        return

    print("\n--- Link Type Analysis Complete ---")
    print("The following link types were found:\n")

    # .most_common() sorts the items from most common to least common
    for link_type, count in link_type_counts.most_common():
        print(f"{link_type}: {count} times")

if __name__ == "__main__":
    analyze_link_types()
