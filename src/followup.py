from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time


def send_followup(driver, url, index=None):
    """
    Sends a follow-up message on ImmoScout.
    Assumes user is already logged in.
    """

    print(f"[{index}] 🔁 ImmoScout follow-up → {url}")

    driver.get(url)
    wait = WebDriverWait(driver, 20)

    try:
        # 1️⃣ Click "Nachricht / Kontakt" button
        contact_btn = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(., 'Nachricht') or contains(., 'Kontakt')]"
            ))
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            contact_btn
        )
        time.sleep(0.5)
        contact_btn.click()

        # 2️⃣ Message textarea
        message_box = wait.until(
            EC.presence_of_element_located((By.ID, "message"))
        )

        followup_message = (
            "Guten Tag,\n\n"
            "ich wollte kurz nachfragen, ob meine vorherige Nachricht Sie erreicht hat.\n"
            "Bei Interesse freue ich mich über eine kurze Rückmeldung.\n\n"
            "Mit freundlichen Grüßen\n"
            "René Grote"
        )

        message_box.clear()
        for c in followup_message:
            message_box.send_keys(c)
            time.sleep(0.01)

        # 3️⃣ Submit button
        submit_btn = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[@type='submit' and contains(., 'Submit')]"
            ))
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            submit_btn
        )
        time.sleep(0.5)

        driver.execute_script("arguments[0].click();", submit_btn)

        print(f"[{index}] ✅ ImmoScout follow-up sent")

        # 4️⃣ Cooldown (important)
        time.sleep(30)

        return True

    except TimeoutException:
        print(f"[{index}] ❌ Follow-up failed (element timeout)")
        return False
