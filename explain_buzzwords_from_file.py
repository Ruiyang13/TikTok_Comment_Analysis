# -*- coding: utf-8 -*-
"""
Reads candidate words from 'autodetect_buzzword_candidates.txt' and uses GPT for batch explanation.
"""
import pandas as pd
from langdetect import detect
from tqdm import tqdm
import time
import os
import re
from openai import OpenAI

def detect_language_simple(text):
    """Simple language detection logic"""
    try:
        # Check if contains Chinese characters
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return 'zh'
        # Check if contains Vietnamese characters (handles diacritics)
        if any(char in 'àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ' for char in text.lower()):
            return 'vi'
        # Check if it is an emoji
        if re.match(r'^[\U0001F300-\U0010FFFF]+$', text):
            return 'emoji'
        # Default to English
        return 'en'
    except:
        return 'en'

def ai_explain_buzzword(keyword, language, dry_run=False):
    """Uses GPT to explain the cultural nuance of internet buzzwords"""
    if language == 'zh':
        prompt = f"""You are an expert in internet subculture. Please explain the term '{keyword}' in Chinese, including:
1. Common usage scenarios in online subculture.
2. Emotional sentiment (Note: some seemingly negative terms like 'last stage' or 'social death' can be positive or ironic).
3. The real meaning and origin of the meme.
4. Differences from traditional dictionary meanings.
5. Typical sample sentences.

Focus on explaining the actual emotional intent this term expresses in a TikTok comment context."""
    elif language == 'vi':
        prompt = f"""You are an expert in Vietnamese memes and internet slang. Explain the phrase '{keyword}' based on Vietnamese netizen culture, including:
1. Popular usage.
2. Positive/negative sentiment (Note: subculture reversals).
3. The true meaning of the meme.
4. Differences from traditional meanings.
5. Sample sentences."""
    elif language == 'emoji':
        prompt = f"""You're an expert in Internet subculture and emoji usage. Explain the emoji '{keyword}' in detail, including:
1. Common usage contexts in TikTok/internet culture.
2. Emotional meaning (positive/negative/subversive).
3. Cultural significance.
4. Typical usage examples."""
    else:  # Default English
        prompt = f"""You're an expert in Internet subculture. Explain in detail the term/phrase '{keyword}', including:
1. Common usage contexts in TikTok/internet culture.
2. Emotional sentiment (positive/negative/subversive - note that some seemingly negative terms may be positive in subculture, like "cringe", "dead", etc.)
3. The real meaning and origin of the meme.
4. How it differs from traditional sentiment.
5. Sample sentences.

Focus on explaining the actual emotional meaning this term might express in TikTok comment contexts."""
    
    if dry_run:
        return f"[DRY RUN] Explanation for {keyword}"
    
    global client
    if 'client' not in globals():
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=512
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def read_candidates_from_file(filename):
    """Reads candidate words from the structured txt file created by the detector"""
    keywords = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    current_section = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Detect English/Translated section headers from the previous script
        if 'Chinese Keywords' in line or '中文高频词' in line:
            current_section = 'zh'
            continue
        elif 'English Keywords' in line or '英文高频词' in line:
            current_section = 'en'
            continue
        elif 'Vietnamese Keywords' in line or '越南语高频词' in line:
            current_section = 'vi'
            continue
        elif 'Emoji' in line:
            current_section = 'emoji'
            continue
        elif 'Phrases' in line or '高频短语' in line:
            current_section = 'phrase'
            continue
        
        if current_section:
            if current_section == 'phrase':
                if line and not line.startswith('==='):
                    keywords.append(('auto', line))
            else:
                words = [w.strip() for w in line.split(',') if w.strip()]
                for word in words:
                    if word and not word.startswith('==='):
                        keywords.append((current_section, word))
    return keywords

if __name__ == "__main__":
    print("Reading candidates from autodetect_buzzword_candidates.txt, processing batch explanations with GPT...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found!")
        exit(1)
    
    client = OpenAI(api_key=api_key)
    keywords = read_candidates_from_file("autodetect_buzzword_candidates.txt")
    print(f"Successfully read {len(keywords)} candidate words/phrases.\n")
    
    records = []
    for lang_hint, keyword in tqdm(keywords, desc="Processing"):
        if lang_hint == 'auto':
            detected_lang = detect_language_simple(keyword)
        else:
            detected_lang = lang_hint
        
        explanation = ai_explain_buzzword(keyword, detected_lang, dry_run=False)
        
        records.append({
            "keyword": keyword,
            "lang": detected_lang,
            "explain": explanation
        })
        time.sleep(0.2)
    
    df = pd.DataFrame(records)
    output_file = "multilang_tiktok_buzzword_dict_auto.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\nDone! Results saved to {output_file}")