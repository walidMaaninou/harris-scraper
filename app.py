import streamlit as st
import pandas as pd
import json
from datetime import date
from table import get_table

# Load instrument types from JSON
with open("instrument_types.json", "r", encoding="utf-8") as f:
    instrument_types = json.load(f)

st.title("Instrument Scraper")

# --- User Inputs ---
instrument_keys = st.multiselect(
    "Select Instrument Types",
    sorted(set(instrument_types.keys()))  # show the keys for better UX
)

start_date = st.date_input("Start Date", value=date(2025, 9, 1))
end_date = st.date_input("End Date", value=date(2025, 9, 10))

# --- Run Button ---
if st.button("Start Scraping") and instrument_keys:
    status_placeholder = st.empty()
    all_results = []

    # Group keys by code (avoid scraping duplicates)
    code_to_keys = {}
    for key in instrument_keys:
        code = instrument_types[key]
        code_to_keys.setdefault(code, []).append(key)

    for i, (code, keys) in enumerate(code_to_keys.items(), start=1):
        status_placeholder.info(
            f"Scraping instrument type {i}/{len(code_to_keys)}: {', '.join(keys)}..."
        )

        # Call the scraping function once per unique code
        df = get_table(code, start_date, end_date)
        if not df.empty:
            df["Instrument Type"] = ", ".join(keys)  # annotate with all keys
            all_results.append(df)

    status_placeholder.success("✅ Scraping completed!")

    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        st.write("### Results")
        st.dataframe(final_df)
    else:
        st.info("No data found for selected instrument types.")
