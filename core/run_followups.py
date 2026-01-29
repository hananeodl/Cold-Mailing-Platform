from src.followup import send_followup
from core.followup_scheduler import get_followup_candidates
from core.lead_manager import mark_followup_sent
from selenium import webdriver


def get_driver():
    # Initialize and return a Selenium WebDriver instance
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    return driver


driver = get_driver()

for index, lead in enumerate(get_followup_candidates(), start=1):
    success = send_followup(driver, lead["url"], index)

    if success:
        mark_followup_sent(lead["url"], lead["follow_up_count"])

driver.quit()
