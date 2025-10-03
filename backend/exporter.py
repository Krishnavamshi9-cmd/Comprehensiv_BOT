from typing import Dict, List
import os
import pandas as pd
from datetime import datetime


def export_to_excel(items: List[Dict[str, str]], output_path: str, url: str = "") -> str:
    if not items:
        raise ValueError("No items to export")
    rows = []
    for i, it in enumerate(items, start=1):
        rows.append({
            "S.No": i,
            "Expected Golden Question": it.get("question", "").strip(),
            "Expected Result": it.get("expected_response", "").strip(),
            "URL": url,
        })
    df = pd.DataFrame(rows, columns=["S.No", "Expected Golden Question", "Expected Result", "URL"])
    # Ensure directory exists
    out_dir = os.path.dirname(output_path) or "."
    os.makedirs(out_dir, exist_ok=True)
    try:
        df.to_excel(output_path, index=False)
        return output_path
    except PermissionError:
        # If the target file is open/locked, save to a timestamped alternative
        base, ext = os.path.splitext(output_path)
        alt_path = f"{base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        df.to_excel(alt_path, index=False)
        print(f"⚠ Permission denied for '{output_path}'. Saved to '{alt_path}' instead.")
        return alt_path


def export_to_excel_with_testcases(
    items: List[Dict[str, str]],
    testcases: List[Dict[str, str]],
    output_path: str,
    url: str = "",
) -> str:
    if not items:
        raise ValueError("No items to export")
    # Sheet 1: Golden QnA (same structure as export_to_excel)
    # Build a quick lookup from Question -> testcase dict
    tc_lookup = {}
    for tc in (testcases or []):
        q = tc.get("Question", "").strip()
        if q:
            tc_lookup[q] = tc

    def _compose_testcase_cell(tc: Dict[str, str] | None) -> str:
        if not tc:
            return ""
        variations = str(tc.get("Variations", "")).strip()
        negative = str(tc.get("Negative Case", "")).strip()
        parts = []
        if variations:
            parts.append(f"Variations:\n{variations}")
        if negative:
            parts.append(f"Negative Case:\n{negative}")
        return "\n\n".join(parts)

    qna_rows = []
    for i, it in enumerate(items, start=1):
        q_text = it.get("question", "").strip()
        tc = tc_lookup.get(q_text)
        qna_rows.append({
            "S.No": i,
            "Expected Golden Question": q_text,
            "Test case": _compose_testcase_cell(tc),
            "Expected Result": it.get("expected_response", "").strip(),
            "URL": url,
        })
    df_qna = pd.DataFrame(qna_rows, columns=["S.No", "Expected Golden Question", "Test case", "Expected Result", "URL"])

    # Sheet 2: TestCases
    # Preserve column order if available
    if testcases:
        tc_columns = [
            "ID",
            "Question",
            "Expected Response",
            "Test Steps",
            "Variations",
            "Negative Case",
            "Entities/Slots",
            "Notes",
        ]
        df_tc = pd.DataFrame(testcases)
        # Reindex columns if possible
        try:
            df_tc = df_tc.reindex(columns=tc_columns)
        except Exception:
            pass
    else:
        df_tc = pd.DataFrame(columns=[
            "ID",
            "Question",
            "Expected Response",
            "Test Steps",
            "Variations",
            "Negative Case",
            "Entities/Slots",
            "Notes",
        ])

    # Ensure directory exists
    out_dir = os.path.dirname(output_path) or "."
    os.makedirs(out_dir, exist_ok=True)

    # Write multi-sheet workbook
    try:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df_qna.to_excel(writer, index=False, sheet_name="Golden QnA")
            df_tc.to_excel(writer, index=False, sheet_name="TestCases")
        return output_path
    except PermissionError:
        base, ext = os.path.splitext(output_path)
        alt_path = f"{base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        with pd.ExcelWriter(alt_path, engine="openpyxl") as writer:
            df_qna.to_excel(writer, index=False, sheet_name="Golden QnA")
            df_tc.to_excel(writer, index=False, sheet_name="TestCases")
        print(f"⚠ Permission denied for '{output_path}'. Saved to '{alt_path}' instead.")
        return alt_path
