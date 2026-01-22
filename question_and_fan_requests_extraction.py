import re
from pathlib import Path

import pandas as pd


def add_question_flags(df: pd.DataFrame, comment_col: str = "Comments") -> pd.DataFrame:
    """
    Add boolean columns for question detection:
    - is_question: strict punctuation-based questions (ending with ? or ？)
    - is_potential_question: broader pattern-based questions using particles and wh-words
    """
    text = df[comment_col].astype(str).fillna("")
    text_lower = text.str.lower()

    # 1. Strict question mark based detection
    df["is_question"] = text.str.contains(r"[?？]\s*$", regex=True)

    # 2. Chinese sentence-final particles that often indicate questions
    cn_particle_pattern = r"(吗|呢|吧|不)$"
    has_cn_particle_question = text.str.contains(cn_particle_pattern, regex=True)

    # 3. Question-leading words in English
    en_wh_pattern = r"\b(where|how|why|when|what)\b"
    has_en_wh = text_lower.str.contains(en_wh_pattern, regex=True)

    # 4. Question-leading words in Chinese
    cn_wh_pattern = r"(为什么|怎么|哪儿|谁|是不是)"
    has_cn_wh = text.str.contains(cn_wh_pattern, regex=True)

    df["is_potential_question"] = (
        df["is_question"] | has_cn_particle_question | has_en_wh | has_cn_wh
    )

    return df


def add_fan_request_flags(
    df: pd.DataFrame,
    comment_col: str = "Comments",
    use_potential_question_col: str = "is_potential_question",
) -> pd.DataFrame:
    """
    Add flags for "Cringe & Cute" style fan request comments.

    Only non-question comments are considered for fan requests.

    Adds:
    - is_singing_request
    - is_hard_watch_request
    - is_general_request
    - is_fan_request (union of the above)
    """
    text = df[comment_col].astype(str).fillna("")
    text_lower = text.str.lower()

    # Ensure we have the potential-question flag
    if use_potential_question_col not in df.columns:
        raise ValueError(
            f"Column '{use_potential_question_col}' not found. "
            f"Run add_question_flags() before add_fan_request_flags()."
        )

    # Non-question mask (fan wishlist should be from non-questions)
    non_question_mask = ~df[use_potential_question_col].fillna(False)

    # 1) Singing-related requests
    singing_pattern = r"(singing|vocals|唱歌|翻唱|再唱一首)"
    is_singing_request = non_question_mask & (
        text_lower.str.contains(r"(singing|vocals)", regex=True)
        | text.str.contains(r"(唱歌|翻唱|再唱一首)", regex=True)
    )

    # 2) Hard watch / cringe challenge requests
    hard_watch_pattern_en = r"(hard watch|cringe|cringe video)"
    hard_watch_pattern_cn = r"(更尴尬|挑战|不适)"
    is_hard_watch_request = non_question_mask & (
        text_lower.str.contains(hard_watch_pattern_en, regex=True)
        | text.str.contains(hard_watch_pattern_cn, regex=True)
    )

    # 3) General request phrases
    general_pattern_en = r"(more|next|part 2|pt 2|sequel|want|request)"
    general_pattern_cn = r"(再来|续集|下次|拍个|想要看)"
    is_general_request = non_question_mask & (
        text_lower.str.contains(general_pattern_en, regex=True)
        | text.str.contains(general_pattern_cn, regex=True)
    )

    df["is_singing_request"] = is_singing_request
    df["is_hard_watch_request"] = is_hard_watch_request
    df["is_general_request"] = is_general_request
    df["is_fan_request"] = (
        df["is_singing_request"]
        | df["is_hard_watch_request"]
        | df["is_general_request"]
    )

    return df


def extract_fan_requests(
    input_file: str = "TikTok_comments_with_sentiment.csv",
    output_file: str = "fan_requests.csv",
) -> pd.DataFrame:
    """
    Main entry point:
    1. Load the TikTok comments dataset.
    2. Add question-related flags.
    3. Add fan-request-related flags for non-question comments.
    4. Export a subset of rows that represent fan requests.
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

    print("Adding fan request flags for non-question comments...")
    df = add_fan_request_flags(df, comment_col="Comments")

    # Create fan request subset with key fields
    fan_mask = df["is_fan_request"].fillna(False)
    fan_requests = df.loc[
        fan_mask,
        [
            "Video ID",
            "URL",
            "Caption",
            "Comments",
            "Comment Likes",
            "Language",
            "is_singing_request",
            "is_hard_watch_request",
            "is_general_request",
        ],
    ].copy()

    print(f"Total comments: {len(df)}")
    print(f"Fan request comments detected: {len(fan_requests)}")

    print(f"Saving fan requests to {output_path}...")
    fan_requests.to_csv(output_path, index=False, encoding="utf-8-sig")
    print("Done.")

    return df


if __name__ == "__main__":
    extract_fan_requests()


