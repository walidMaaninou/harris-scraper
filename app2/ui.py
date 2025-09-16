import streamlit as st
import pandas as pd
import asyncio
from .logic import run_hcad_searches


def run_app2(df: pd.DataFrame):
    """
    Runs the HCAD Property Search on a DataFrame coming from App 1.
    Expects df with at least 'Grantees' and 'LegalDescription' columns.
    """
    st.title("HCAD Property Search")

    if df is None or df.empty:
        st.warning("No input data available. Please run the instrument scraper first.")
        return

    st.write("### Input Data (from Instrument Scraper)")
    st.dataframe(df)

    if st.button("Run HCAD Searches"):
        asyncio.run(run_hcad_searches(df))
