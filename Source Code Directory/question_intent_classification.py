import os
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore

from question_and_fan_requests_extraction import add_question_flags


INTENT_LABELS = [
    "Content_Request",
    "Information_Inquiry",
    "Rhetorical_Shock",
    "Instructional",
    "Other",
]


def build_intent_prompt(comment: str) -> str:
    """
    Build a concise, English-only instruction for intent classification.
    """
    return (
        "You are classifying the intent of a TikTok comment addressed to a creator.\n"
        "Assign exactly ONE label from the following categories:\n"
        "1. Content_Request: The commenter clearly asks the creator to make or continue content "
        "(e.g., asking for more videos, next part, more singing, or specific scenarios).\n"
        "2. Information_Inquiry: The commenter asks for factual or contextual information "
        "about the video or the creator (e.g., where something is from, who someone is).\n"
        "3. Rhetorical_Shock: The commenter uses a rhetorical question mainly to express shock, "
        "surprise, disbelief, or emotional reaction, not to get an actual answer.\n"
        "4. Instructional: The commenter is giving suggestions or guidance to the creator "
        "about what to do, how to improve, or how to behave.\n"
        "5. Other: The comment does not fit any of the above.\n\n"
        "Return ONLY the label name (Content_Request, Information_Inquiry, Rhetorical_Shock, "
        "Instructional, or Other).\n\n"
        f"Comment: {comment}"
    )


def classify_intents_with_openai(
    comments: List[str],
    model: str = "gpt-4o-mini",
    api_key: str | None = None,
) -> List[str]:
    """
    Use an OpenAI-compatible client to classify a list of comments.
    Returns a list of intent labels aligned with INTENT_LABELS.
    """
    if OpenAI is None:
        raise ImportError(
            "openai package is not installed. Install it with 'pip install openai'."
        )

    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)

    labels: List[str] = []
    for comment in comments:
        prompt = build_intent_prompt(comment)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8,
            temperature=0.0,
        )
        raw_content = response.choices[0].message.content or ""
        label = raw_content.strip().split()[0]
        if label not in INTENT_LABELS:
            label = "Other"
        labels.append(label)

    return labels


def classify_question_intents(
    input_file: str = "TikTok_comments_with_sentiment.csv",
    output_file: str = "question_intents.csv",
    model: str = "gpt-4o-mini",
) -> pd.DataFrame:
    """
    Pipeline:
    1. Load dataset.
    2. Add question flags using regex/keyword rules.
    3. Filter to question-like comments.
    4. Call LLM to classify each question into one intent label.
    5. Save a CSV sorted by Comment Likes (descending).
    """
    input_path = Path(input_file)
    output_path = Path(output_file)

    print(f"Reading data from {input_path}...")
    df = pd.read_csv(input_path)

    if "Comments" not in df.columns:
        raise KeyError("Expected a 'Comments' column in the input dataset.")
    if "Comment Likes" not in df.columns:
        raise KeyError("Expected a 'Comment Likes' column in the input dataset.")

    print("Adding question flags...")
    df = add_question_flags(df, comment_col="Comments")

    # Use potential questions (broader definition)
    question_mask = df["is_potential_question"].fillna(False)
    questions_df = df.loc[question_mask].copy()

    print(f"Total comments: {len(df)}")
    print(f"Question-like comments detected: {len(questions_df)}")

    if questions_df.empty:
        print("No questions found. Nothing to classify.")
        return df

    comments_list = questions_df["Comments"].astype(str).tolist()
    print("Classifying question intents with the LLM...")
    intent_labels = classify_intents_with_openai(
        comments_list,
        model=model,
    )

    questions_df["intent_label"] = intent_labels

    # Sort by Comment Likes descending to surface the most engaged questions
    questions_df_sorted = questions_df.sort_values(
        by="Comment Likes", ascending=False
    )

    # Select useful columns for inspection
    columns_to_keep: List[str] = [
        "Video ID",
        "URL",
        "Caption",
        "Comments",
        "Comment Likes",
        "Language",
        "is_question",
        "is_potential_question",
        "intent_label",
    ]
    existing_columns = [c for c in columns_to_keep if c in questions_df_sorted.columns]
    export_df = questions_df_sorted[existing_columns].copy()

    print(f"Saving question intents to {output_path}...")
    export_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print("Done.")

    return df


if __name__ == "__main__":
    classify_question_intents()


