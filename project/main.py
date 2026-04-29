import os
import re
import asyncio
from playwright.async_api import async_playwright, TimeoutError

URL = "https://sound-effects.bbcrewind.co.uk/search?cat=Military"

KEYWORDS = {
    "weapons": ["gun", "rifle", "shoot", "fire"],
    "air vehicles": ["helicopter", "jet", "plane", "aircraft"],
    "tank": ["tank", "armour"]
}

BASE_DIR = "dataset"

def classify(text: str):
    text = text.lower()
    for category, words in KEYWORDS.items():
        if any(w in text for w in words):
            return category
    return "other"

def safe_filename(name):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)[:80]

async def main():
    os.makedirs(BASE_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto(URL)
        await page.wait_for_selector('button[title="Download file"]', timeout=15000)

        processed_count = 0  

        while True:
            await page.wait_for_timeout(2000)
            
            download_buttons = page.locator('button[title="Download file"]')
            current_count = await download_buttons.count()
            
            print(f"\nЗнайдено записів на сторінці: {current_count} (Оброблено раніше: {processed_count})")

            for i in range(processed_count, current_count):
                try:
                    btn = download_buttons.nth(i)
                    await btn.scroll_into_view_if_needed()
                    
                    title = await btn.evaluate('''el => {
                        const container = el.closest('.flex-row.items-center.justify-between');
                        if (container) {
                            const p = container.querySelector('p.text-gray-900');
                            return p ? p.innerText : 'Unknown_Title';
                        }
                        return 'Unknown_Title';
                    }''')
                    
                    category = classify(title)

                    if category == "other":
                        print(f"[{i+1}/{current_count}] не підходить по ключах: {title}")
                        continue
                    
                    print(f"[{i+1}/{current_count}] обробка ({category}): {title}")
                    category_path = os.path.join(BASE_DIR, category)
                    os.makedirs(category_path, exist_ok=True)
                    
                    await btn.click()
                    await page.wait_for_timeout(1000)
                    
                    async with page.expect_download(timeout=10000) as download_info:
                        await page.locator("button:text-is('mp3')").first.click(timeout=3000)
                        
                    download = await download_info.value
                    
                    safe_title = safe_filename(title)
                    extension = download.suggested_filename.split('.')[-1]
                    file_name = f"{safe_title}.{extension}"
                    final_path = os.path.join(category_path, file_name)

                    await download.save_as(final_path)
                    print(f" Збережено: {final_path}")

                    await page.keyboard.press("Escape")
                    
                except Exception as e:
                    print(f"[{i+1}/{current_count}] ПОМИЛКА: {e}")
                    await page.keyboard.press("Escape")

            processed_count = current_count

            try:
                load_more_btn = page.locator('button:has-text("Load more")').first
                if await load_more_btn.is_visible(timeout=3000):
                    print("\nНатискаю 'Load more' для завантаження наступної порції...")
                    await load_more_btn.click()
                else:
                    print("\nКнопку 'Load more' більше не знайдено. Всі файли оброблено.")
                    break
            except TimeoutError:
                print("\nСписок закінчився (таймаут кнопки Load more).")
                break

        await browser.close()
        print("Роботу завершено.")

if __name__ == "__main__":
    asyncio.run(main())