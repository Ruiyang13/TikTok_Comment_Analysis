import pandas as pd
from langdetect import detect, DetectorFactory
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Set seed for reproducibility
DetectorFactory.seed = 0

def detect_language(text):
    """
    Detect the language of a text string.
    Returns the language code or 'unknown' if detection fails.
    """
    try:
        # Remove leading/trailing whitespace
        text = str(text).strip()
        
        # If text is too short or only emojis, return 'unknown'
        if len(text) < 2:
            return 'unknown'
        
        # Try to detect language
        lang = detect(text)
        return lang
    except:
        return 'unknown'

def clean_and_detect_language(input_file, output_file):
    """
    Clean the data by removing rows with 'Nil' or empty Comments,
    and add language detection for each comment.
    """
    print(f"Reading data from {input_file}...")
    df = pd.read_csv(input_file)
    
    print(f"Original data shape: {df.shape}")
    print(f"Original number of rows: {len(df)}")
    
    # Step 1: Data cleaning - Remove rows where Comments is 'Nil' or empty
    print("\nCleaning data: Removing rows with 'Nil' or empty Comments...")
    
    # Remove rows where Comments is 'Nil' (case-insensitive) or empty/NaN
    initial_count = len(df)
    df_cleaned = df[
        (df['Comments'].notna()) & 
        (df['Comments'].astype(str).str.strip() != '') & 
        (df['Comments'].astype(str).str.strip().str.lower() != 'nil')
    ].copy()
    
    removed_count = initial_count - len(df_cleaned)
    print(f"Removed {removed_count} rows with 'Nil' or empty Comments")
    print(f"Cleaned data shape: {df_cleaned.shape}")
    
    # Step 2: Language detection
    print("\nDetecting languages for comments...")
    print("This may take a while for large datasets...")
    
    # Apply language detection to each comment
    df_cleaned['Language'] = df_cleaned['Comments'].apply(detect_language)
    
    # Show language distribution
    print("\nLanguage distribution:")
    print(df_cleaned['Language'].value_counts())
    
    # Step 3: Save the cleaned data
    print(f"\nSaving cleaned data to {output_file}...")
    df_cleaned.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\nDone! Cleaned data saved to {output_file}")
    print(f"Final data shape: {df_cleaned.shape}")
    
    return df_cleaned

if __name__ == "__main__":
    input_file = "TikTok_cleaned_data_diff_languages - clean data.csv"
    output_file = "TikTok_cleaned_data_with_language.csv"
    
    df_result = clean_and_detect_language(input_file, output_file)
    
    # Display a sample of the results
    print("\nSample of cleaned data with language detection:")
    try:
        # Try to print with UTF-8 encoding
        sample = df_result[['Comments', 'Language']].head(20)
        for idx, row in sample.iterrows():
            comment = str(row['Comments'])[:50]  # Limit length for display
            print(f"Language: {row['Language']}, Comment: {comment}...")
    except UnicodeEncodeError:
        print("Sample data saved successfully (console encoding issue prevented display)")

