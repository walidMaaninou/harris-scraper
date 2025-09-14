import re
import pandas as pd

def extract_description(desc: str) -> str:
    if pd.isna(desc):
        return ""

    text = str(desc)

    # Get everything after "Desc:"
    match = re.search(r"Desc:\s*(.*)", text, re.IGNORECASE)
    if not match:
        return text.strip()

    cleaned = match.group(1).strip()

    # Stop at keywords (Sec, Lot, Block, Addition, Subdivision)
    stop_words = ["SEC", "LOT", "BLOCK", "ADDITION", "SUBDIVISION"]
    for word in stop_words:
        idx = cleaned.upper().find(word)
        if idx != -1:
            cleaned = cleaned[:idx].strip()
            break

    return cleaned

def read_excel_to_list(input_file="output.xlsx"):
    df = pd.read_excel(input_file)

    if df.shape[1] < 6:
        raise ValueError("The file does not have at least 6 columns (A-F).")

    result = []
    for _, row in df.iterrows():
        col_e = row.iloc[4]  # Column E
        col_f = extract_description(row.iloc[5])  # Column F (cleaned)
        result.append([col_e, col_f])

    return result

if __name__ == "__main__":
    data = read_excel_to_list()
    for row in data:
        print(row)
