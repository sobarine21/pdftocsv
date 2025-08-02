import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import zipfile
from datetime import datetime

st.set_page_config(page_title="Structured Text PDF Extractor", layout="centered")

st.title("Structured Text PDF Extractor")
st.markdown("Extract LLP details from non-tabular, structured-text PDFs and download as zipped CSVs.")

uploaded_files = st.file_uploader(
    "Upload one or more PDF files", type=["pdf"], accept_multiple_files=True
)

# Regular expression to match lines like: 1 T05LL0746J CHRIS & VIC LLP
line_pattern = re.compile(r"^\s*(\d+)\s+([T0-9A-Z]+)\s+(.+)$")

def extract_structured_text(pdf_file):
    extracted_data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split("\n")
            for line in lines:
                match = line_pattern.match(line)
                if match:
                    no, uen, name = match.groups()
                    extracted_data.append({
                        "No": int(no),
                        "UEN": uen.strip(),
                        "Limited Liability Partnership Name": name.strip()
                    })
    return extracted_data

if uploaded_files:
    st.info("Extracting structured data from uploaded PDFs...")
    zip_buffer = io.BytesIO()
    master_df = pd.DataFrame()

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name.replace(".pdf", "")
            data = extract_structured_text(uploaded_file)
            if data:
                df = pd.DataFrame(data)
                master_df = pd.concat([master_df, df], ignore_index=True)
                csv_data = df.to_csv(index=False).encode("utf-8")
                zip_file.writestr(f"{file_name}.csv", csv_data)
            else:
                st.warning(f"No structured data found in {uploaded_file.name}")

        # Add master CSV
        if not master_df.empty:
            master_csv = master_df.to_csv(index=False).encode("utf-8")
            zip_file.writestr("master_combined.csv", master_csv)

    st.success("Extraction complete!")

    st.download_button(
        label="Download Zipped CSVs (Including Master File)",
        data=zip_buffer.getvalue(),
        file_name=f"llp_extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
        mime="application/zip"
    )

    if not master_df.empty:
        st.subheader("Preview of Master Combined Table")
        st.dataframe(master_df.head(100))
else:
    st.info("Please upload one or more structured-text PDFs to begin.")
