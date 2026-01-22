import re
from pathlib import Path
import pandas as pd

def is_keyword_request(comment: str) -> bool:
    """
    Heuristic keyword-based detector for request-style questions,
    to complement the LLM Content_Request label.
    """
    text = str(comment).lower()
    patterns = [
        r"\bpls\b",
        r"\bplease\b",
        r"\bcan u\b",
        r"\bcan you\b",
        r"\bcould you\b",
        r"\bcollab\b",
        r"\bpart 2\b",
        r"\bpt 2\b",
        r"\bnext part\b",
        r"\bmore\b",
        r"\bsequel\b",
    ]
    return any(re.search(p, text) for p in patterns)


def analyze_content_requests(
    input_file: str = "question_intents.csv",
    markdown_output: str = "content_request_analysis.md",
    excel_output: str = "content_request_analysis.xlsx",
) -> None:
    """
    Analyze specific question types, excluding 'Other' and 'Rhetorical_Shock'.
    """
    path = Path(input_file)
    if not path.exists():
        print(f"Error: {input_file} not found.")
        return

    print(f"Reading data from {path}...")
    df = pd.read_csv(path)

    required_cols = {"Comments", "Comment Likes", "URL", "intent_label", "is_potential_question"}
    missing = required_cols - set(df.columns)
    if missing:
        raise KeyError(f"Missing required columns in {input_file}: {missing}")

    # --- DEBUGGING: Print all unique labels found ---
    found_labels = df["intent_label"].unique()
    print(f"\nUnique intent labels found in the CSV: {found_labels}")

    # --- ROBUST FILTERING LOGIC ---
    
    # 1. Clean the labels: Remove all spaces and convert to lowercase
    # This handles "Other ", "other", "Rhetorical_Shock ", "rhetorical shock", etc.
    def clean_label(val):
        return str(val).strip().lower().replace(" ", "_")

    cleaned_series = df["intent_label"].apply(clean_label)
    
    # 2. Define labels to exclude (cleaned format)
    # We include variations to be absolutely certain
    excluded_targets = ["other", "rhetorical_shock", "rhtorical_shock"]
    
    # 3. Create the validity mask
    is_valid_intent = ~cleaned_series.isin(excluded_targets)
    
    # 4. Basic question check
    is_question = df["is_potential_question"].fillna(False).astype(bool)
    
    # 5. Keyword request check
    is_keyword_req = df["Comments"].astype(str).apply(is_keyword_request) & is_question
    
    # 6. Final Filter: Must be (a question OR a keyword match) AND NOT in the excluded list
    final_mask = (is_question | is_keyword_req) & is_valid_intent
    
    req_df = df[final_mask].copy()

    # --- STATS REPORTING ---
    print(f"\nTotal question-like entries: {is_question.sum()}")
    print(f"Excluded (Other/Rhetorical_Shock) entries removed: {(is_question & ~is_valid_intent).sum()}")
    print(f"Final filtered count (valid intents only): {len(req_df)}")

    if req_df.empty:
        print("No questions found after applying the filters.")
        return

    # 1) Aggregation by URL
    by_url = (
        req_df.groupby("URL", dropna=False)
        .size()
        .sort_values(ascending=False)
        .rename("request_count")
    )

    # 2) Statistics
    filtered_likes = req_df["Comment Likes"]
    lang_counts = req_df["Language"].value_counts()
    intent_counts = req_df["intent_label"].value_counts()

    print("\nIntent distribution in result (Should be clean):")
    for intent, cnt in intent_counts.items():
        print(f"- {intent}: {cnt}")

    # 5) Sort and Prepare Output
    req_df_sorted = req_df.sort_values(by="Comment Likes", ascending=False).copy()

    output_cols = ["URL", "Comment Likes", "Comments", "intent_label", "Language"]
    for col in ["Video ID", "Caption"]:
        if col in req_df_sorted.columns:
            output_cols.append(col)
    
    output_df = req_df_sorted[output_cols].copy()

    # 6) Markdown table
    md_lines = ["| URL | Comment Likes | Comment | Intent Label |", "| --- | ------------- | ------- | ------------ |"]
    for _, row in req_df_sorted.iterrows():
        url = str(row["URL"])
        likes = row["Comment Likes"]
        comment = str(row["Comments"]).replace("\n", " ").strip().replace("|", "\\|")
        intent = str(row["intent_label"])
        md_lines.append(f"| {url} | {likes} | {comment} | {intent} |")

    md_path = Path(markdown_output)
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    # 7) Excel export
    excel_path = Path(excel_output)
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        output_df.to_excel(writer, sheet_name="Filtered Questions", index=False)
        
        summary_data = {
            "Metric": ["Total Questions", "Avg Likes", "Top Language", "Top Intent"],
            "Value": [
                len(req_df_sorted),
                f"{filtered_likes.mean():.3f}",
                lang_counts.index[0] if not lang_counts.empty else "N/A",
                intent_counts.index[0] if not intent_counts.empty else "N/A",
            ],
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)
        
        top_vids = pd.DataFrame({"URL": by_url.head(20).index, "Count": by_url.head(20).values})
        top_vids.to_excel(writer, sheet_name="Top Videos", index=False)

    print(f"\nAnalysis complete.")
    print(f"- Markdown table: {md_path}")
    print(f"- Excel file: {excel_path}")


if __name__ == "__main__":
    analyze_content_requests()