import asyncio
from playwright.async_api import async_playwright

async def main(owner_name, legal_desc):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            extra_http_headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/139.0.0.0 Safari/537.36",
                "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8,fr;q=0.7",
                "Accept": "*/*",
                "X-Requested-With": "XMLHttpRequest",
            }
        )
        page = await context.new_page()
        await page.goto("https://hcad.org/property-search/property-search")

        # Wait for the iframe
        iframe_locator = page.locator("iframe#parentIframe")
        await iframe_locator.wait_for()
        iframe_el = await iframe_locator.element_handle()
        frame = await iframe_el.content_frame()

        # Click Advanced Search button
        advanced_btn = frame.locator("button.btn.btn-primary", has_text="Advanced Search").first
        await advanced_btn.wait_for(state="visible")
        await advanced_btn.click(force=True)

        # Wait for the modal inputs to appear
        await frame.wait_for_selector("#ownerName", timeout=10000)
        await frame.wait_for_selector("#LegalDscr", timeout=10000)

        # Fill Owner Name and Legal Description
        await frame.fill("#ownerName", owner_name)
        await frame.fill("#LegalDscr", legal_desc)

        # Click Submit
        submit_btn = frame.locator("button.btn.btn-primary:has-text('Submit')")
        await submit_btn.click()

        # Wait for the results table to load
        await frame.wait_for_selector("table.data-table tbody tr", timeout=15000)

        # Extract the first row address
        address = await frame.inner_text("table.data-table tbody tr td:nth-child(3)")
        print("First row address:", address)

        await browser.close()

# Example usage
asyncio.run(main("SALAZAR EDUARDO", "GLEANNLOCH FARMS"))
