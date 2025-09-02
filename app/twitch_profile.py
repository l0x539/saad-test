from playwright.sync_api import sync_playwright
import re

def scrape_profile(username: str):
    url = f"https://www.twitch.tv/{username}/about"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        
        page.wait_for_selector('.about-section__panel', timeout=10000)

        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        # Extract about
        about_text = "No about section found"
        emails = []
        try:
            page.wait_for_selector('p[dir="auto"]', timeout=5000)
            description = page.locator('p[dir="auto"]').text_content()
            if description and description.strip():
                about_text = description.strip()
                emails = re.findall(email_pattern, about_text)
        except Exception as e:
            print(f"Error extracting about section: {e}")
            try:
                about_text = page.locator('div.about-section__panel--content p:not(.bsLreE)').first.text_content()
                emails = re.findall(email_pattern, about_text)
            except:
                pass

        # Extract socials
        social_links = []
        try:
            page.wait_for_selector('div.social-media-link a', timeout=5000)
            for el in page.query_selector_all('div.social-media-link a'):
                href = el.get_attribute("href")
                label = el.inner_text().strip()
                label_el = el.query_selector('p.CoreText-sc-1txzju1-0.bsLreE')
                label = label_el.inner_text().strip() if label_el else "Unknown"
                if href and label:
                    social_links.append({"label": label, "url": href})
        except:
            pass

        # cleanup
        browser.close()

        return {
            "username": username,
            "about": about_text,
            "email": emails,
            "social_links": social_links,
        }
