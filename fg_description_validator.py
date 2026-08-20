"""
FG Description Standards Validator
-----------------------------------
Batch-checks Finished Goods (FG) material descriptions against Bondville's
SAP material creation standard before they are submitted to SAP.

Standard:
    Material Type Indicator - Customer - Style - Color - Size
    Example: F-SLM-2000450951-BLACK-16MM

Rules enforced:
    1. Exactly 4 dashes (5 segments), in the fixed order above
    2. All letters uppercase
    3. Description length <= 40 characters
    4. No empty segments
    5. No duplicate descriptions within the uploaded batch

Run with:
    streamlit run fg_description_validator.py
"""

import io
import re
import pandas as pd
import streamlit as st

SEGMENT_LABELS = ["Material Type Indicator", "Customer", "Style", "Color", "Size"]
MAX_LENGTH = 40
REQUIRED_DASHES = 4

st.set_page_config(page_title="FG Description Validator", layout="wide")


def validate_description(raw_desc: str) -> dict:
    """Validate a single FG description string against the standard.

    Returns a dict with pass/fail status, a list of issues, and the
    segments (if the dash count allows them to be split).
    """
    desc = "" if pd.isna(raw_desc) else str(raw_desc)
    issues = []

    stripped = desc.strip()
    if stripped != desc:
        issues.append("Has leading/trailing whitespace")
    desc = stripped

    if desc == "":
        return {
            "status": "FAIL",
            "issues": ["Description is empty"],
            "segments": {},
            "length": 0,
        }

    # Rule: uppercase only (letters must not contain lowercase)
    if re.search(r"[a-z]", desc):
        issues.append("Contains lowercase letters (must be all uppercase)")

    # Rule: max length
    if len(desc) > MAX_LENGTH:
        issues.append(f"Exceeds {MAX_LENGTH} characters (length = {len(desc)})")

    # Rule: dash count / segment structure
    dash_count = desc.count("-")
    segments_dict = {}
    if dash_count != REQUIRED_DASHES:
        issues.append(
            f"Expected exactly {REQUIRED_DASHES} dashes (5 segments: "
            f"{'-'.join(SEGMENT_LABELS)}), found {dash_count}"
        )
    else:
        parts = desc.split("-")
        for label, part in zip(SEGMENT_LABELS, parts):
            segments_dict[label] = part
            if part.strip() == "":
                issues.append(f"'{label}' segment is empty")

    # Rule: no stray double-dashes / spaces around dashes (order integrity)
    if re.search(r"--", desc):
        issues.append("Contains consecutive dashes")
    if re.search(r"\s-|-\s", desc):
        issues.append("Contains spaces adjacent to a dash")

    status = "PASS" if not issues else "FAIL"
    return {
        "status": status,
        "issues": issues,
        "segments": segments_dict,
        "length": len(desc),
    }


def run_batch_validation(df: pd.DataFrame, col: str) -> pd.DataFrame:
    results = []
    for _, row in df.iterrows():
        desc = row[col]
        result = validate_description(desc)
        record = {
            "FG Description": desc,
            "Status": result["status"],
            "Length": result["length"],
            "Issues": "; ".join(result["issues"]) if result["issues"] else "",
        }
        for label in SEGMENT_LABELS:
            record[label] = result["segments"].get(label, "")
        results.append(record)

    result_df = pd.DataFrame(results)

    # Duplicate check within the batch (case-sensitive exact match, since
    # descriptions are expected to be uppercase already)
    dup_mask = result_df["FG Description"].astype(str).duplicated(keep=False)
    result_df.loc[dup_mask, "Status"] = "FAIL"
    result_df.loc[dup_mask, "Issues"] = result_df.loc[dup_mask, "Issues"].apply(
        lambda x: (x + "; " if x else "") + "Duplicate description within batch"
    )

    return result_df


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Validation Report")
        workbook = writer.book
        worksheet = writer.sheets["Validation Report"]
        for i, col in enumerate(df.columns):
            width = max(12, min(50, int(df[col].astype(str).map(len).max() * 1.1) + 2))
            worksheet.column_dimensions[chr(65 + i)].width = width
    return buffer.getvalue()


st.title("FG Description Standards Validator")
st.caption(
    "Checks proposed Finished Goods descriptions against the SAP material "
    "creation standard: Material Type Indicator-Customer-Style-Color-Size "
    "(e.g. F-SLM-2000450951-BLACK-16MM), all uppercase, max 40 characters, "
    "no duplicates within the batch."
)

uploaded_file = st.file_uploader(
    "Upload a list of proposed FG descriptions (CSV or Excel)",
    type=["csv", "xlsx", "xls"],
)

if uploaded_file is not None:
    if uploaded_file.name.lower().endswith(".csv"):
        input_df = pd.read_csv(uploaded_file)
    else:
        input_df = pd.read_excel(uploaded_file)

    st.write("Preview of uploaded file:")
    st.dataframe(input_df.head(), use_container_width=True)

    column = st.selectbox(
        "Which column holds the FG descriptions?", input_df.columns
    )

    if st.button("Run validation", type="primary"):
        report_df = run_batch_validation(input_df, column)

        total = len(report_df)
        passed = (report_df["Status"] == "PASS").sum()
        failed = total - passed

        c1, c2, c3 = st.columns(3)
        c1.metric("Total checked", total)
        c2.metric("Passed", passed)
        c3.metric("Failed", failed)

        # Sort so failures surface first, and prefix Status with an icon for
        # quick visual scanning (avoids fragile pandas Styler rendering).
        report_df = report_df.sort_values(
            by="Status", ascending=True
        ).reset_index(drop=True)
        display_df = report_df.copy()
        display_df["Status"] = display_df["Status"].map(
            {"PASS": "✅ PASS", "FAIL": "❌ FAIL"}
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            height=500,
            column_config={
                "Status": st.column_config.TextColumn("Status", width="small"),
            },
        )

        excel_bytes = to_excel_bytes(report_df)
        st.download_button(
            "Download validation report (Excel)",
            data=excel_bytes,
            file_name="fg_description_validation_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
else:
    st.info("Upload a CSV or Excel file with a column of proposed FG descriptions to begin.")
    with st.expander("Expected input format"):
        st.write(
            "A single column of proposed descriptions, one per row, e.g.:\n\n"
            "```\n"
            "FG_Description\n"
            "F-SLM-2000450951-BLACK-16MM\n"
            "R-abc-STYLE01-Red-M\n"
            "F-SLM-2000450951-BLACK-16MM\n"
            "```"
        )
