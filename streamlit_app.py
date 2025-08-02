import streamlit as st
import pandas as pd
import pdfplumber
import io
import zipfile
from datetime import datetime

st.set_page_config(page_title="Bulk PDF to CSV Extractor")

st.title("Bulk PDF Table Extractor and Zipped CSV Downloader")

uploaded_files = st.file_uploader("Upload one or more PDF files", type=["pdf"], accept_multiple_files=True)

def make_unique_columns(columns):
    seen = {}
    new_cols = []
    for idx, col in enumerate(columns):
        if not col or str(col).strip() == "":
            col = f"Column_{idx+1}"
        if col in seen:
            seen[col] += 1
            col = f"{col}_{seen[col]}"
        else:
            seen[col] = 1
        new_cols.append(col)
    return new_cols

def normalize_row(row, num_cols):
    if len(row) < num_cols:
        return row + [None] * (num_cols - len(row))
    else:
        return row[:num_cols]

def extract_and_combine_tables_from_pdf(pdf_file):
    all_rows = []
    header = None
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            for table in page_tables:
                cleaned_table = [
                    [cell.strip() if isinstance(cell, str) else cell for cell in row]
                    for row in table if any(cell is not None and str(cell).strip() != "" for cell in row)
                ]
                if cleaned_table:
                    if header is None:
                        header = cleaned_table[0]
                        all_rows.extend(cleaned_table[1:])
                    else:
                        all_rows.extend(cleaned_table[1:])
    return header, all_rows

if uploaded_files:
    st.info("Processing uploaded PDFs...")
    zip_buffer = io.BytesIO()
    master_df = pd.DataFrame()

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name.replace(".pdf", "")
            header, all_rows = extract_and_combine_tables_from_pdf(uploaded_file)
            if header and all_rows:
                header = make_unique_columns(header)
                num_cols = len(header)
                normalized_rows = [normalize_row(row, num_cols) for row in all_rows]
                df = pd.DataFrame(normalized_rows, columns=header)
                master_df = pd.concat([master_df, df], ignore_index=True)

                csv_data = df.to_csv(index=False).encode('utf-8')
                zip_file.writestr(f"{file_name}.csv", csv_data)
            else:
                st.warning(f"No tables found in {uploaded_file.name}")

        # Add master CSV
        master_csv = master_df.to_csv(index=False).encode('utf-8')
        zip_file.writestr("master_combined.csv", master_csv)

    st.success("Extraction complete!")

    st.download_button(
        label="Download Zipped CSVs (Including Master File)",
        data=zip_buffer.getvalue(),
        file_name=f"pdf_tables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
        mime="application/zip"
    )

    if not master_df.empty:
        st.subheader("Preview of Master Combined Table")
        st.dataframe(master_df.head(100))
else:
    st.info("Please upload one or more PDF files to begin.")
