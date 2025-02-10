from playwright.sync_api import sync_playwright
import time
import random
import csv
import os
import sys
from datetime import datetime

def extract_numeric(text):
    """Helper function to extract the numeric value from text."""
    try:
        return int(text.split()[0])
    except (ValueError, IndexError):
        return 0


def random_scroll(page):
    """Perform a random vertical scroll on the page."""
    scroll_height = random.randint(300, 1000)
    print(f"Scrolling down {scroll_height} pixels.")
    page.evaluate(f"window.scrollBy(0, {scroll_height});")
    time.sleep(random.uniform(1, 3))


def random_mouse_movement(page):
    """Randomly move the mouse across the page."""
    x = random.randint(0, page.viewport_size["width"])
    y = random.randint(0, page.viewport_size["height"])
    print(f"Moving mouse to coordinates: ({x}, {y})")
    page.mouse.move(x, y)
    time.sleep(random.uniform(1, 2))


def scrape_listings(base_url, output_file):
    """Scrape listings data by sequentially navigating through URLs."""
    with sync_playwright() as p:
        try:
            # Launch the browser with proxy settings
            browser = p.chromium.launch(
                headless=False,  # Set to True for headless mode if needed
                )

            # Create a new browser context for cookies and session management
            context = browser.new_context(
                extra_http_headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                    "Referer": "https://www.domain.com.au",  # Set a realistic referer
                    "Accept-Language": "en-US,en;q=0.9",  # Optionally, mimic language preferences
                },
                ignore_https_errors=True,  # Ignore SSL certificate issues (useful for some proxies)
            )

            page = context.new_page()

            # Results list to store scraped data
            results = []

            # Session cookies storage
            cookies = []
            page_number = 1  # Start page number
            pages_scraped = 0  # Counter for pages scraped so far

            while True:
                # Stop scraping after 10 pages
                if pages_scraped >= 10:
                    print(f"Scraped 10 pages. Stopping pagination.")
                    break

                # Construct URL for the current page
                current_url = f"{base_url}&page={page_number}"
                print(f"Navigating to: {current_url}")

                # Load previously stored cookies for maintaining the session
                if cookies:
                    context.add_cookies(cookies)

                # Navigate to the current page
                try:
                    page.goto(current_url, timeout=120000)  # Adjust timeout to handle slow responses
                except Exception as e:
                    print(f"Error navigating to page {page_number}: {e}")
                    break  # End scraping if navigation fails

                # Save cookies after navigating to this page
                cookies = context.cookies()

                # Random delay to mimic human behavior
                delay = random.uniform(5, 10)  # Long delays for avoiding detection
                print(f"Waiting for {delay:.2f} seconds...")
                time.sleep(delay)

                # Add scrolling for randomized behavior
                random_scroll(page)

                # Add mouse movement for randomized behavior
                random_mouse_movement(page)

                print(f"Scraping page {page_number}.")

                # Find listings on the current page
                listings = page.query_selector_all('[data-testid^="listing-card-wrapper"]')

                # If no listings are found, break the loop (end of results)
                if not listings:
                    print(f"No listings found on page {page_number}. Stopping pagination.")
                    break

                # Stop scraping if there are fewer than 4 listings on this page
                if len(listings) < 4:
                    print(f"Less than 4 listings found on page {page_number}. Stopping pagination.")
                    break

                # Scrape details for each listing
                for listing in listings:
                    # Safely check if address-line1 exists
                    address_line1_element = listing.query_selector('[data-testid="address-line1"]')
                    if not address_line1_element:
                        continue

                    # Extract fields (agent name, prices, etc.)
                    address_line1 = address_line1_element.inner_text().strip()

                    agent_name_element = listing.query_selector(
                        '[data-testid="listing-card-branding"] span:nth-child(1)')
                    agent_name = agent_name_element.inner_text() if agent_name_element else ""

                    agency_name_element = listing.query_selector(
                        '[data-testid="listing-card-branding"] span:nth-child(2)')
                    agency_name = agency_name_element.inner_text() if agency_name_element else ""

                    price_element = listing.query_selector('[data-testid="listing-card-price"]')
                    price = price_element.inner_text().strip() if price_element else ""

                    # Safely handle address-line2
                    address_line2_element = listing.query_selector('[data-testid="address-line2"]')
                    address_line2 = address_line2_element.inner_text().strip() if address_line2_element else None

                    if address_line2:
                        # Parse suburb, state, and postcode
                        address_parts = address_line2.split()
                        suburb = " ".join(address_parts[:-2])
                        state = address_parts[-2]
                        postcode = address_parts[-1]
                    else:
                        suburb, state, postcode = None, None, None

                    # Property features
                    features_wrapper = listing.query_selector('[data-testid="property-features-wrapper"]')
                    features_texts = features_wrapper.query_selector_all(
                        '[data-testid="property-features-text-container"]'
                    ) if features_wrapper else []

                    bedrooms = extract_numeric(features_texts[0].inner_text()) if len(features_texts) > 0 else 0
                    bathrooms = extract_numeric(features_texts[1].inner_text()) if len(features_texts) > 1 else 0
                    car_spaces = extract_numeric(features_texts[2].inner_text()) if len(features_texts) > 2 else 0
                    sqm = features_texts[3].inner_text() if len(features_texts) > 3 else 0

                    # Other details
                    tag_element = listing.query_selector('[data-testid="listing-card-tag"]')
                    listing_card_tag = tag_element.inner_text().strip() if tag_element else None

                    lazy_image_element = listing.query_selector('[data-testid="listing-card-lazy-image"] img')
                    alt_image = lazy_image_element.get_attribute('alt') if lazy_image_element else None
                    if alt_image and 'Logo for' in alt_image:
                        alt_image = alt_image.replace('Logo for ', '').strip()

                    property_type_element = listing.query_selector(
                        '[data-testid="listing-card-features-wrapper"] .css-11n8uyu span'
                    )
                    property_type = property_type_element.inner_text().strip() if property_type_element else None

                    # Append results
                    results.append({
                        "agent_name": agent_name,
                        "agency_name": agency_name,
                        "price": price,
                        "address_line1": address_line1,
                        "suburb": suburb,
                        "state": state,
                        "postcode": postcode,
                        "bedrooms": bedrooms,
                        "bathrooms": bathrooms,
                        "car_spaces": car_spaces,
                        "SQM": sqm,
                        "listing_card_tag": listing_card_tag,
                        "alt_image": alt_image,
                        "property_type": property_type,
                    })

                # Print progress
                print(f"Scraped {len(listings)} listings from page {page_number}.")

                # Increment page counters for the next iteration
                page_number += 1
                pages_scraped += 1  # Track pages scraped

            # Close the browser after scraping completes
            browser.close()

        except Exception as e:
            print(f"An error occurred during scraping: {e}")
            # Save partial results to CSV in case of failure
            export_to_csv(results, output_file)
        finally:
            # Ensure results are saved even if program terminates unexpectedly
            if results:
                export_to_csv(results, output_file)
                print(f"Partial data saved to {output_file}.")

        print(f"Scraping completed. Total listings scraped: {len(results)}")
        return results


def export_to_csv(data, file_path):
    """Export the scraped data to a CSV file."""
    if not data:
        print("\nNo data to export.")
        return

    # Extract headers from the first dictionary in the results
    headers = data[0].keys()

    # Write to a CSV file
    with open(file_path, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()  # Write the column names
        writer.writerows(data)  # Write each row from the data list

    print(f"\nScraped data has been exported to: {file_path}")


if __name__ == "__main__":
    # Take base URL and output directory from arguments or prompt user input
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        output_directory = sys.argv[2]
    else:
        base_url = input("Enter the base URL to scrape: ").strip()
        output_directory = input("Enter the output directory for the CSV file: ").strip()

    # Generate timestamp for the output file
    timestamp = datetime.now().strftime("%H-%M_%d-%m-%Y")
    output_file = os.path.join(output_directory, f"{timestamp}_scraped_listing_VM1.csv")

    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)

    # Run the scraper
    scrape_listings(base_url, output_file)




