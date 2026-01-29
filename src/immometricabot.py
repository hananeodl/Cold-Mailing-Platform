"""
ImmoMetrica CSV Automation Script
Reads CSV file with property listings and opens each detail link
to contact sellers/agents directly.
"""

from operator import index
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select 
import pandas as pd
import time
import os
import re
import csv
import json
from pathlib import Path

TEST_IMMOSCOUT_LIMIT = 11


# Configuration
CSV_FILE_PATH = "/home/rania/Downloads/Immo-vt.csv"  # Change this to your CSV file path

def setup_driver():
    """Initialize Chrome driver with options"""
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    return driver


def read_csv_by_columns(csv_path):
    print(f"Reading CSV file: {csv_path}")

    df = pd.read_csv(csv_path, sep=';', on_bad_lines='skip', encoding='utf-8')

    start_col = 28  # AC
    end_col = 45    # AT

    if len(df.columns) <= end_col:
        raise ValueError("CSV does not contain columns up to AT")

    target_df = df.iloc[:, start_col:end_col + 1]

    column_urls = {}

    for col_name in target_df.columns:
        urls = []

        for cell in target_df[col_name]:
            if pd.notna(cell):
                found = re.findall(r'https?://[^\s;]+', str(cell))
                urls.extend(found)

        if urls:
            column_urls[col_name] = urls
            print(f"✓ {col_name}: {len(urls)} URLs")

    return column_urls



def open_detail_page(driver, url, index):
    """Open a detail page URL"""
    try:
        print(f"\n[{index}] Opening detail page...")
        print(f"[{index}] URL: {url}")
        
        driver.get(url)
        
        # Wait for page to load (wait for body element)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        print(f"[{index}] ✓ Page opened!")
        time.sleep(2)
        
        return True
        
    except Exception as e:
        print(f"[{index}] ✗ Failed to open page: {str(e)}")
        return False

def click_news_button(driver, index):
    print(f"[{index}] Looking for contact button...")
    wait = WebDriverWait(driver, 20)

    # 1. Wait for page to stabilize
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # 2. Try default content first
    driver.switch_to.default_content()

    # 3. Collect all iframes (ImmoScout uses them)
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"[{index}] Found {len(iframes)} iframe(s)")

    for i, iframe in enumerate([None] + iframes):
        try:
            if iframe:
                driver.switch_to.frame(iframe)
                print(f"[{index}] → Switched to iframe {i}")

            # 4. Locate button via test id (BEST selector)
            button = wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//button[@data-testid='contact-button']"
                ))
            )

            # 5. Force-click (React-safe)
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", button
            )
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", button)

            print(f"[{index}] ✓ Contact button clicked")
            return True

        except Exception:
            driver.switch_to.default_content()
            continue

    print(f"[{index}] ❌ Contact button not found in any iframe")
    driver.save_screenshot(f"contact_button_fail_{index}.png")
    return False

def fill_and_submit_immoscout_message(driver, index):
    wait = WebDriverWait(driver, 20)

    print(f"[{index}] Filling ImmoScout contact form")

    # 1. MESSAGE TEXTAREA
    message_box = wait.until(
        EC.presence_of_element_located((By.ID, "message"))
    )

    test_message = """Guten Tag,
 
Wir sind ein Immobilien Makler und Investor aus der Region und sind sehr an Ihrer Immobilie interessiert. Wir würden gerne mehr über diese erfahren. Sie passt zu mehreren unserer hinterlegten Suchprofile - welche wir bei Kunden aufgenommen haben, bei denen ein vorheriger Ankauf nicht geklappt hat. Daher würde ich mich
sehr freuen, wenn Sie mir Ihre Telefonnummer und E-Mail
zur Verfügung stellen könnten, damit wir uns kurz zu Ihrem Objekt austauschen können.
 
Mit freundlichen Grüßen
 
René Grote
 
Immo-VT GmbH / Mittelstr. 11 / 40789 Monheim am Rhein
T: +49 2173 2950501
F: +49 2173 8984977
Interessent@immo-vt.de
info@immo-vt.de"""

    message_box.clear()
    for c in test_message:
        message_box.send_keys(c)
        time.sleep(0.02)

    print(f"[{index}] ✓ Message filled")

    
    # 2. SALUTATION (select FIRST non-empty option)
    salutation_select = wait.until(
        EC.presence_of_element_located((By.NAME, "salutation"))
    )

    select = Select(salutation_select)

    # select first valid option (index 1, index 0 is empty)
    select.select_by_index(3)

    print(f"[{index}] ✓ Salutation selected")

    # 3. FIRST NAME
    first_name_input = wait.until(
        EC.presence_of_element_located((By.ID, "firstName"))
    )
    first_name_input.clear()
    first_name_input.send_keys("Nils")

    print(f"[{index}] ✓ First name entered")

    # 4. LAST NAME
    last_name_input = wait.until(
        EC.presence_of_element_located((By.ID, "lastName"))
    )
    last_name_input.clear()
    last_name_input.send_keys("van Tübbergen")

    print(f"[{index}] ✓ Last name entered")

        # 5. EMAIL ADDRESS
    email_input = wait.until(
        EC.presence_of_element_located((By.ID, "emailAddress"))
    )

    # even if disabled in HTML, JS can still set value
    driver.execute_script("""
    const input = arguments[0];
    const value = arguments[1];

    input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
""", email_input, "interessent@immo-vt.de")


    print(f"[{index}] ✓ Email entered")


    # 6. PHONE NUMBER
    phone_input = wait.until(
        EC.presence_of_element_located((By.ID, "phoneNumber"))
    )
    phone_input.clear()
    phone_input.send_keys("+49 179 7272607")

    print(f"[{index}] ✓ Phone number entered")

     # 3. RADIO BUTTON: Home owner = YES
    yes_radio = wait.until(
        EC.presence_of_element_located((By.ID, "homeOwner_TRUE"))
    )

    driver.execute_script("arguments[0].click();", yes_radio)

    print(f"[{index}] ✓ Radio button 'Yes' selected")
    
    # 6. SUBMIT BUTTON
    submit_btn = wait.until(
    EC.presence_of_element_located((By.XPATH, "//button[@type='submit']"))
)

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});", submit_btn
    )
    time.sleep(0.5)
    driver.execute_script("""
    arguments[0].closest('form').requestSubmit();
""", submit_btn)
    print(f"[{index}] ✅ ImmoScout form submitted")

    print(f"[{index}] ⏳ Waiting 30s before next URL...")
    time.sleep(30)  # wait after submit to avoid issues


def handle_immoscout(driver, index):
    """
    Full ImmoScout flow:
    - Click Nachricht
    - Fill message form
    - Submit
    """

    print(f"[{index}] Handling ImmoScout flow")

    # Step 1: Click Nachricht
    if not click_news_button(driver, index):
        raise Exception("Failed to click Nachricht button")

    time.sleep(2)  # small human pause

    # Step 2: Fill + submit message
    fill_and_submit_immoscout_message(driver, index)


def handle_kleinanzeigen(driver, index):
    wait = WebDriverWait(driver, 20)

    print(f"[{index}] Kleinanzeigen: clicking contact")

    contact_btn = wait.until(
        EC.presence_of_element_located((By.ID, "viewad-contact-button"))
    )

    driver.execute_script("arguments[0].click();", contact_btn)

    textarea = wait.until(
        EC.presence_of_element_located((By.ID, "viewad-contact-message"))
    )

    message = "hi i inquire you for this test"

    textarea.clear()
    for c in message:
        textarea.send_keys(c)
        time.sleep(0.02)

    print(f"[{index}] ✓ Kleinanzeigen message filled")

"""
def process_columns_sequentially(driver, column_urls, delay=3):

    for col_name, urls in column_urls.items():

        print("\n" + "="*60)
        print(f"PROCESSING COLUMN {col_name}")
        print("="*60)

        handler = COLUMN_HANDLERS.get(col_name)

        if not handler:
            print(f"⚠ No handler for column {col_name}, skipping")
            continue

        for index, url in enumerate(urls, start=1):
            try:
                print(f"\n[{col_name} | {index}/{len(urls)}] {url}")

                driver.get(url)
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                handler(driver, index)

                time.sleep(delay)

            except Exception as e:
                print(f"✗ Failed: {e}")
                driver.save_screenshot(f"error_{col_name}_{index}.png")
                continue

        print(f"✓ Finished column {col_name}")
"""

def process_columns_sequentially(driver, column_urls, delay=3):

    for col_name, urls in column_urls.items():

        # 🔒 ONLY ImmoScout for this test
        if col_name != "Link ImmoScout":
            continue

        print("\n" + "="*60)
        print(f"PROCESSING COLUMN {col_name} (TEST MODE)")
        print("="*60)

        handler = COLUMN_HANDLERS.get(col_name)

        if not handler:
            print(f"⚠ No handler for column {col_name}, skipping")
            return

        # 🔢 LIMIT TO FIRST 10 URLS
        urls = urls[:TEST_IMMOSCOUT_LIMIT]

        print(f"→ Processing {len(urls)} ImmoScout URLs")

        for index, url in enumerate(urls, start=1):
            try:
                print(f"\n[{index}/{len(urls)}] {url}")

                driver.get(url)

                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                handler(driver, index)

                time.sleep(delay)

            except Exception as e:
                print(f"✗ Failed on URL {index}: {e}")
                driver.save_screenshot(f"immoscout_error_{index}.png")
                continue

        print("\n✅ MESSAGES SENT (TEST COMPLETE)")
        return  # 🔴 STOP ENTIRE SCRIPT AFTER ImmoScout


def print_summary(results):
    """Print summary of processed listings"""
    print("\n" + "="*60)
    print("PROCESSING COMPLETE - SUMMARY")
    print("="*60)
    
    total = len(results)
    success = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'failed')
    
    print(f"Total listings processed: {total}")
    print(f"✓ Successfully opened: {success}")
    print(f"✗ Failed to open: {failed}")
    print(f"Success rate: {(success/total*100):.1f}%")
    
    if failed > 0:
        print("\nFailed listings:")
        for r in results:
            if r['status'] == 'failed':
                print(f"  - Listing {r['index']}: {r['url']}")
    
    print("="*60)
"""
from core.lead_manager import (
    can_send_message,
    mark_message_sent,
    mark_followup_sent
)
"""


COLUMN_HANDLERS = {
    "Link ImmoScout": handle_immoscout,        # ImmoMetrica / ImmoScout
    "Link Kleinanzeigen": handle_kleinanzeigen,
    #"Link immonet": handle_immonet,          # stub for now
    #"Link immowelt": handle_immowelt,         # stub for now
    #"Link Ohne Makler": handle_ohne_makler,   # stub
    #"Link Wohnung Jetzt": handle_wohnung_jetzt,
    #"Link Regionalimmobilien": handle_regional,
    #"Link Zeitungen und sonstige": handle_misc,
}

def preview_scraped_urls(column_urls, max_per_column=10):
    """
    Print scraped URLs grouped by column.
    Useful for debugging before running Selenium.
    """

    print("\n" + "="*70)
    print("SCRAPED URL PREVIEW (BY COLUMN)")
    print("="*70)

    for col, urls in column_urls.items():
        print(f"\nCOLUMN {col} — {len(urls)} URL(s)")

        for i, url in enumerate(urls[:max_per_column], start=1):
            print(f"  {i:02d}. {url}")

        if len(urls) > max_per_column:
            print(f"  ... ({len(urls) - max_per_column} more)")

    print("\n" + "="*70)

def csv_to_json(csv_path, json_path=None, encoding="utf-8"):
    """
    Convert CSV file to JSON file.

    :param csv_path: Path to CSV file
    :param json_path: Optional output JSON path
    :param encoding: File encoding
    :return: List of dicts (JSON data)
    """

    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    if json_path is None:
        json_path = csv_path.with_suffix(".json")
    else:
        json_path = Path(json_path)

    data = []

    with csv_path.open(mode="r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Normalize empty strings to None
            cleaned_row = {
                key: (value.strip() if value and value.strip() else None)
                for key, value in row.items()
            }
            data.append(cleaned_row)

    with json_path.open(mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"✓ CSV converted to JSON → {json_path}")

    return data

def main():
    """Main automation flow"""
    driver = None
    
    try:
        print("="*60)
        print("ImmoMetrica CSV Automation Started")
        print("="*60)
        
        # Check if CSV file exists
        if not os.path.exists(CSV_FILE_PATH):
            print(f"\n✗ ERROR: CSV file not found at: {CSV_FILE_PATH}")
            print("\nPlease update the CSV_FILE_PATH in the script with your file location.")
            print("Example: CSV_FILE_PATH = 'C:/Users/YourName/Downloads/offers(2).csv'")
            return
        
        # Read CSV file
        column_urls = read_csv_by_columns(CSV_FILE_PATH)

        # 👀 PREVIEW URLs BEFORE RUNNING BROWSER
        preview_scraped_urls(column_urls, max_per_column=5)

        
        # Setup browser
        print("\nInitializing browser...")
        driver = setup_driver()
        print("✓ Browser ready")
        
        # Process all listings
        process_columns_sequentially(driver, column_urls, delay=3)
        
        # Print summary
        #print_summary(results)
        
        # Keep browser open
        print("\n✓ Process completed!")
        input("\nPress Enter to close the browser...")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Process interrupted by user")
    except Exception as e:
        print(f"\n✗ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
            print("\nBrowser closed.")

if __name__ == "__main__":
    main()