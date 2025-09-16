import re
import asyncio
import pandas as pd
from playwright.async_api import async_playwright

NUM_TABS = 5


def clean_legal_desc(text: str) -> str:
    """Clean up legal description text."""
    if not isinstance(text, str):
        return ""
    if not text.strip().lower().startswith("desc:"):
        return ""
    desc = text.split("Desc:", 1)[1].strip()
    desc = re.sub(r"\b(ADDITION|SUBDIVISION)\b", "", desc, flags=re.IGNORECASE)
    stop_keywords = ["Sec:", "Lot:", "Block:", "Unit:", "Abstract:"]
    for kw in stop_keywords:
        idx = desc.lower().find(kw.lower())
        if idx != -1:
            desc = desc[:idx]
            break
    return desc.strip()


async def run_search(page, owner_name, legal_desc_clean, legal_desc_full, first_run=False):
    """Run a single HCAD property search."""
    if first_run:
        await page.goto("https://hcad.org/property-search/property-search")
        await asyncio.sleep(1)

    iframe_locator = page.locator("iframe#parentIframe")
    await iframe_locator.wait_for()
    frame = await (await iframe_locator.element_handle()).content_frame()

    if first_run:
        advanced_btn = frame.locator("button.btn.btn-primary", has_text="Advanced Search").first
        await advanced_btn.wait_for(state="visible")
        await advanced_btn.click(force=True)

    await frame.wait_for_selector("#ownerName", timeout=10000)
    await frame.wait_for_selector("#LegalDscr", timeout=10000)

    # Fill inputs
    await frame.fill("#ownerName", "")
    await frame.fill("#LegalDscr", "")
    await frame.fill("#ownerName", owner_name)
    await frame.fill("#LegalDscr", legal_desc_clean)

    await asyncio.sleep(1)
    submit_btn = frame.locator("button.btn.btn-primary:has-text('Submit')")
    await submit_btn.click()

    try:
        await frame.wait_for_selector("table.data-table tbody tr", timeout=30000)
        address = await frame.inner_text("table.data-table tbody tr td:nth-child(3)")
    except Exception:
        address = None

    # Reset for next search
    try:
        await frame.locator("input[type='reset'][value='Reset']").click()
        await asyncio.sleep(1)
    except Exception:
        pass

    return {
        "owner": owner_name,
        "desc_clean": legal_desc_clean,
        "desc_full": legal_desc_full,
        "address": address,
    }


async def worker(page, queue, results, results_placeholder):
    first_run = True
    while not queue.empty():
        row = await queue.get()
        owner = str(row.get("Grantees", "")).split(",")[0].strip()
        legal_desc_full = str(row.get("LegalDescription", "")).strip()
        legal_desc_clean = clean_legal_desc(legal_desc_full)

        result = await run_search(page, owner, legal_desc_clean, legal_desc_full, first_run=first_run)

        # Copy original row and add Address
        row_with_address = row.copy()
        row_with_address["Address"] = result["address"]

        results.append(row_with_address)
        results_placeholder.dataframe(pd.DataFrame(results))

        first_run = False
        queue.task_done()


async def main_async(df, results_placeholder):
    # Fill queue with full rows
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
        tabs = [await context.new_page() for _ in range(NUM_TABS)]
        queue = asyncio.Queue()
        for _, row in df.iterrows():
            await queue.put(row.to_dict())  # put full row as dict

        results = []
        tasks = [asyncio.create_task(worker(tab, queue, results, results_placeholder)) for tab in tabs]
        await queue.join()
        await asyncio.gather(*tasks)
        await asyncio.sleep(2)



async def run_hcad_searches(df: pd.DataFrame):
    """Entry point for running HCAD searches from UI."""
    import streamlit as st
    results_placeholder = st.empty()
    await main_async(df, results_placeholder)
