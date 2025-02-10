import csv
import subprocess
import os
import re


def read_progress(progress_csv):
    """
    Reads the progress from the progress CSV file if it exists.

    Returns:
        dict: Dictionary containing progress info - {url: {status, last_page}}.
    """
    progress = {}
    if os.path.exists(progress_csv):
        with open(progress_csv, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                progress[row["url"]] = {
                    "status": row["status"],
                    "last_page": int(row["last_page"]),
                }
    return progress


def write_progress(progress_csv, progress):
    """
    Writes progress to the CSV file to track scraper status.

    Args:
        progress_csv (str): Path to the progress CSV file.
        progress (dict): Dictionary with scraping progress data.
    """
    with open(progress_csv, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["url", "status", "last_page"])
        writer.writeheader()
        for url, info in progress.items():
            writer.writerow({
                "url": url,
                "status": info["status"],
                "last_page": info["last_page"],
            })


def extract_last_page(output):
    """
    Extracts the last successfully scraped page number from the scraper output.

    Args:
        output (str): The console output from the scraper.

    Returns:
        int: The last scraped page number, or 1 if none is found.
    """
    # Match a line like "Scraping page X."
    match = re.search(r"Scraping page (\d+)\.", output)
    if match:
        return int(match.group(1))  # Return the captured page number
    return 1  # Default to page 1 if no page number is found


def manage_scraping(input_csv, progress_csv, retries=3):
    """
    Manages the scraping process and resumes from the page where it failed.

    Args:
        input_csv (str): Input CSV containing the base URLs to scrape.
        progress_csv (str): CSV to track scraping progress.
        retries (int): Number of retry attempts for each URL.
    """
    progress = read_progress(progress_csv)

    # Read input URLs from the CSV
    with open(input_csv, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            base_url = row["url"]

            # If progress already exists for this URL, resume or skip as needed
            if base_url in progress and progress[base_url]["status"] == "completed":
                print(f"Skipping {base_url}, already completed.")
                continue
            elif base_url in progress:
                start_page = progress[base_url]["last_page"] + 1
            else:
                start_page = 1

            current_url = base_url  # Start with the base URL
            attempts = 0
            success = False

            while attempts < retries and not success:
                # Modify URL to start from the appropriate page
                if start_page > 1:
                    current_url = f"{base_url}&page={start_page}"

                print(f"Starting scrape for {base_url} from page {start_page}...")

                try:
                    # Define the fixed output directory to be passed
                    fixed_output_directory = "C:\\Users\\roar2\\OneDrive - New Mexico State University\\output"

                    # Run the scraper via subprocess and pass the output directory as an argument
                    result = subprocess.run(
                        ["python", "reascraper2.py", current_url, fixed_output_directory],
                        capture_output=True,
                        text=True,
                        check=True
                    )

                    # Check the scraper's stdout for the last successfully scraped page
                    output = result.stdout
                    last_page = extract_last_page(output)
                    print(f"Scraper successfully ran for {base_url}. Last page: {last_page}.")

                    # Mark as completed in progress file
                    progress[base_url] = {"status": "completed", "last_page": last_page}
                    success = True

                except subprocess.CalledProcessError as e:
                    # Handle scraper errors and retry
                    output = e.stdout
                    print(f"Error while scraping {base_url}: {e.stderr}")

                    # Update the start page from the output for retry
                    last_page = extract_last_page(output)
                    start_page = last_page + 1
                    attempts += 1

                except Exception as e:
                    print(f"Unexpected error for {base_url}: {e}")
                    attempts += 1

            if not success:
                print(f"Failed to scrape {base_url} after {retries} attempts.")
                progress[base_url] = {"status": "failed", "last_page": start_page - 1}

            # Save progress after each URL is processed
            write_progress(progress_csv, progress)

    print("All URLs processed. Check the progress CSV for details.")


if __name__ == "__main__":
    # Paths to input and progress files
    input_csv = "C:\\Users\\roar2\\Documents\\REASCRAPER\\generated_urls.csv"  # Input CSV with URLs
    progress_csv = "scraping_progress.csv"  # Progress tracking CSV

    # Run the scraper manager
    manage_scraping(input_csv, progress_csv)
