"""
Automation Service - Integrates Selenium automation with Flask backend
Handles CSV processing, browser automation, and database logging
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import pandas as pd
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.models import Listing, Mailing, Customer, Search
from app.database import db


class AutomationService:
    """Main automation service for property listing campaigns"""

    def __init__(self, customer_id: int, search_id: int):
        self.customer_id = customer_id
        self.search_id = search_id
        self.driver = None
        self.stats = {
            'processed': 0,
            'success': 0,
            'failed': 0,
            'errors': []
        }

    def setup_driver(self):
        """Initialize Chrome driver with anti-detection options"""
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Headless mode for production
        # options.add_argument('--headless')

        self.driver = webdriver.Chrome(options=options)
        print("✓ Browser initialized")

    def read_csv_and_save_listings(self, csv_path: str) -> Dict[str, List[str]]:
        """
        Read CSV file and save all listings to database
        Returns: Dictionary of column_name -> [urls]
        """
        print(f" Reading CSV: {csv_path}")

        df = pd.read_csv(csv_path, sep=';', on_bad_lines='skip', encoding='utf-8')

        # Columns AC to AT (index 28 to 45)
        start_col = 28
        end_col = 45

        if len(df.columns) <= end_col:
            raise ValueError("CSV does not contain expected columns")

        target_df = df.iloc[:, start_col:end_col + 1]
        column_urls = {}

        # Extract URLs from each column
        for col_name in target_df.columns:
            urls = []

            for idx, cell in enumerate(target_df[col_name]):
                if pd.notna(cell):
                    found_urls = re.findall(r'https?://[^\s;]+', str(cell))

                    for url in found_urls:
                        urls.append(url)

                        # Save to database
                        self._save_listing_to_db(
                            url=url,
                            platform=self._get_platform_from_column(col_name),
                            row_index=idx
                        )

            if urls:
                column_urls[col_name] = urls
                print(f"✓ {col_name}: {len(urls)} URLs saved to database")

        return column_urls

    def _get_platform_from_column(self, col_name: str) -> str:
        """Map column name to platform name"""
        platform_map = {
            'Link ImmoScout': 'immoscout',
            'Link Kleinanzeigen': 'kleinanzeigen',
            'Link immonet': 'immonet',
            'Link immowelt': 'immowelt',
            'Link Ohne Makler': 'ohne_makler',
        }
        return platform_map.get(col_name, 'unknown')

    def _save_listing_to_db(self, url: str, platform: str, row_index: int):
        """Save listing to database"""
        try:
            # Check if listing already exists
            existing = db.session.query(Listing).filter_by(
                external_id=url,
                customer_id=self.customer_id
            ).first()

            if existing:
                print(f"  Listing already exists: {url[:50]}...")
                return existing

            listing = Listing(
                customer_id=self.customer_id,
                search_id=self.search_id,
                external_id=url,
                platform=platform,
                status='pending'  # pending, contacted, responded, rejected
            )

            db.session.add(listing)
            db.session.commit()

            return listing

        except Exception as e:
            db.session.rollback()
            print(f"  ✗ Failed to save listing: {e}")
            return None

    def process_immoscout_campaign(self, urls: List[str], limit: Optional[int] = None):
        """
        Process ImmoScout listings with contact form automation
        """
        if limit:
            urls = urls[:limit]

        print(f"\n Starting ImmoScout campaign: {len(urls)} listings")

        for index, url in enumerate(urls, start=1):
            try:
                print(f"\n[{index}/{len(urls)}] Processing: {url}")

                # Get listing from database
                listing = db.session.query(Listing).filter_by(
                    external_id=url,
                    customer_id=self.customer_id
                ).first()

                if not listing:
                    print(f"  ✗ Listing not found in database")
                    continue

                # Open listing page
                self.driver.get(url)
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                # Click contact button
                if not self._click_contact_button(index):
                    self._log_failed_mailing(listing, "Failed to click contact button")
                    continue

                time.sleep(2)

                # Fill and submit form
                if self._fill_immoscout_form(index):
                    # Log successful mailing
                    self._log_successful_mailing(listing, url)

                    # Update listing status
                    listing.status = 'contacted'
                    listing.contacted_at = datetime.utcnow()
                    db.session.commit()

                    self.stats['success'] += 1
                    print(f"  Message sent successfully")
                else:
                    self._log_failed_mailing(listing, "Failed to submit form")
                    self.stats['failed'] += 1

                self.stats['processed'] += 1

                # Delay between requests
                print(f"  Waiting 30s before next listing...")
                time.sleep(30)

            except Exception as e:
                print(f"  Error processing listing: {e}")
                self.stats['failed'] += 1
                self.stats['errors'].append(f"URL {index}: {str(e)}")

                if listing:
                    self._log_failed_mailing(listing, str(e))

                continue

        print(f"\n Campaign completed!")
        print(f"   Processed: {self.stats['processed']}")
        print(f"   Success: {self.stats['success']}")
        print(f"   Failed: {self.stats['failed']}")

    def _click_contact_button(self, index: int) -> bool:
        """Click ImmoScout contact button (Nachricht)"""
        try:
            wait = WebDriverWait(self.driver, 20)

            # Switch to default content
            self.driver.switch_to.default_content()

            # Try main content and iframes
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")

            for i, iframe in enumerate([None] + iframes):
                try:
                    if iframe:
                        self.driver.switch_to.frame(iframe)

                    button = wait.until(
                        EC.presence_of_element_located((
                            By.XPATH,
                            "//button[@data-testid='contact-button']"
                        ))
                    )

                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", button
                    )
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", button)

                    return True

                except Exception:
                    self.driver.switch_to.default_content()
                    continue

            return False

        except Exception as e:
            print(f"  ✗ Click button error: {e}")
            return False

    def _fill_immoscout_form(self, index: int) -> bool:
        """Fill and submit ImmoScout contact form"""
        try:
            wait = WebDriverWait(self.driver, 20)

            # Get customer info from database
            customer = db.session.query(Customer).get(self.customer_id)

            if not customer:
                print(f"  ✗ Customer not found")
                return False

            # Message textarea
            message_box = wait.until(
                EC.presence_of_element_located((By.ID, "message"))
            )

            # Get message template from customer
            message_content = self._get_message_template(customer)

            message_box.clear()
            for c in message_content:
                message_box.send_keys(c)
                time.sleep(0.02)

            # Salutation
            salutation_select = wait.until(
                EC.presence_of_element_located((By.NAME, "salutation"))
            )
            Select(salutation_select).select_by_index(3)

            # First name
            first_name_input = wait.until(
                EC.presence_of_element_located((By.ID, "firstName"))
            )
            first_name_input.clear()
            first_name_input.send_keys(customer.first_name or "Nils")

            # Last name
            last_name_input = wait.until(
                EC.presence_of_element_located((By.ID, "lastName"))
            )
            last_name_input.clear()
            last_name_input.send_keys(customer.last_name or "van Tübbergen")

            # Email
            email_input = wait.until(
                EC.presence_of_element_located((By.ID, "emailAddress"))
            )
            self.driver.execute_script("""
                const input = arguments[0];
                const value = arguments[1];
                input.value = value;
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
            """, email_input, customer.immometrica_email or "info@immo-vt.de")

            # Phone
            phone_input = wait.until(
                EC.presence_of_element_located((By.ID, "phoneNumber"))
            )
            phone_input.clear()
            phone_input.send_keys(customer.phone or "+49 179 7272607")

            # Home owner radio button
            yes_radio = wait.until(
                EC.presence_of_element_located((By.ID, "homeOwner_TRUE"))
            )
            self.driver.execute_script("arguments[0].click();", yes_radio)

            # Submit button
            submit_btn = wait.until(
                EC.presence_of_element_located((By.XPATH, "//button[@type='submit']"))
            )

            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", submit_btn
            )
            time.sleep(0.5)
            self.driver.execute_script("""
                arguments[0].closest('form').requestSubmit();
            """, submit_btn)

            print(f"  ✓ Form submitted")
            return True

        except Exception as e:
            print(f"  ✗ Form fill error: {e}")
            return False

    def _get_message_template(self, customer: Customer) -> str:
        """Get message template for customer"""
        # You can store this in database or config
        return f"""Guten Tag,

Wir sind ein Immobilien Makler und Investor aus der Region und sind sehr an Ihrer Immobilie interessiert. Wir würden gerne mehr über diese erfahren. Sie passt zu mehreren unserer hinterlegten Suchprofile - welche wir bei Kunden aufgenommen haben, bei denen ein vorheriger Ankauf nicht geklappt hat. Daher würde ich mich sehr freuen, wenn Sie mir Ihre Telefonnummer und E-Mail zur Verfügung stellen könnten, damit wir uns kurz zu Ihrem Objekt austauschen können.

Mit freundlichen Grüßen

{customer.company_name or 'Immo-VT GmbH'}
{customer.street or 'Mittelstr. 11'} / {customer.postal_code or '40789'} {customer.city or 'Monheim am Rhein'}
T: {customer.phone or '+49 2173 2950501'}
{customer.immometrica_email or 'info@immo-vt.de'}"""

    def _log_successful_mailing(self, listing: Listing, url: str):
        """Log successful email send to database"""
        try:
            mailing = Mailing(
                listing_id=listing.id,
                customer_id=self.customer_id,
                type='initial',  # initial, followup
                subject='Interesse an Ihrer Immobilie',
                content=self._get_message_template(
                    db.session.query(Customer).get(self.customer_id)
                ),
                status='sent',
                sent_at=datetime.utcnow()
            )

            db.session.add(mailing)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print(f"  ✗ Failed to log mailing: {e}")

    def _log_failed_mailing(self, listing: Listing, error_message: str):
        """Log failed email attempt"""
        try:
            listing.status = 'failed'
            listing.notes = error_message
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print(f"  ✗ Failed to log error: {e}")

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            print("\n Browser closed")

    def get_stats(self) -> Dict:
        """Return campaign statistics"""
        return self.stats