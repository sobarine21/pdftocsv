import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO

st.set_page_config(page_title="PDF to Structured Data (CSV)")

st.title("PDF Table Extractor and CSV Downloader")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

def make_unique_columns(columns):
    """Make column names unique and fill empty or duplicate headers."""
    seen = {}
    new_cols = []
    for idx, col in enumerate(columns):
        # Replace empty or whitespace-only header with a generic name
        if not col or str(col).strip() == "":
            col = f"Column_{idx+1}"
        # Make duplicate columns unique
        if col in seen:
            seen[col] += 1
            col = f"{col}_{seen[col]}"
        else:
            seen[col] = 1
        new_cols.append(col)
    return new_cols

def extract_tables_from_pdf(pdf_file):
    tables = []
    with pdfplumber.open(pdf_file) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            page_tables = page.extract_tables()
            for table in page_tables:
                # Clean up table: remove empty rows/columns
                cleaned_table = [
                    [cell.strip() if isinstance(cell, str) else cell for cell in row]
                    for row in table if any(cell is not None and str(cell).strip() != "" for cell in row)
                ]
                if cleaned_table:
                    tables.append({'page': page_number, 'data': cleaned_table})
    return tables

if uploaded_file is not None:
    st.info("Extracting tables from your PDF...")
    tables = extract_tables_from_pdf(uploaded_file)
    if tables:
        for idx, table in enumerate(tables):
            st.write(f"**Table {idx+1} (Page {table['page']})**")
            # Handle unique column names
            header_row = table['data'][0]
            header = make_unique_columns(header_row)
            df = pd.DataFrame(table['data'][1:], columns=header)
            st.dataframe(df)
            # CSV download for each table
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"Download Table {idx+1} as CSV",
                data=csv,
                file_name=f'pdf_table_{table["page"]}_{idx+1}.csv',
                mime='text/csv'
            )
    else:
        st.warning("No tables were found in the uploaded PDF.")

st.markdown("---")
st.markdown("Created with ❤️ using Streamlit and pdfplumber.")
