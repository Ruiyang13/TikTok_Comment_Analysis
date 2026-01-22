# -*- coding: utf-8 -*-
"""
Multi-language TikTok Internet Slang/Meme Archiving & Collection Script (CN, EN, VI, etc.)
Outputs a structured reverse-sentiment dictionary (.csv) for downstream NLP analysis.
"""
import requests
from bs4 import BeautifulSoup
from langdetect import detect
from tqdm import tqdm
import pandas as pd
import time
import os

# --- 1. CONFIGURATION & KEYWORDS ---
# Multi-language buzzword list (expandable)
keywords_dict = {
    'zh': ["医生怎么说", "晚期", "雷人", "裂开", "乐", "救命", "笑死", "社死", "神经", "逆天"],
    'en': ["social anxiety is anxious of her", "pushing 30s btw", "face card is saving", "🥀", "dead", "cringe", "hard watch", "tough watch", "unexpected", "plz", "slay", "based", "kys", "💀", "🤡", "rizz", "mid", "ratio"],
    'vi': ["mlem mlem", "khum", "đu trend", "ếch", "xin vía", "chill phết", "tấu hài", "nghiện", "đỉnh cao", "bồ", "xịn sò"]
}
all_keywords = [(lang, kw) for lang, klist in keywords_dict.items() for kw in klist]

def google_search_examples(query, lang='en', limit=2):
    """Fetches real-world usage snippets from Google search results."""
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://www.google.com/search?q={query}&hl={lang}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        return [f"[ERROR/timeout] {e}"]
    
    result_snips = []
    # Extract snippets from meta descriptions or headers
    for div in soup.select('div[data-content-feature="1"] span'):
        result_snips.append(div.text.strip())
    for h3 in soup.find_all('h3'):
        result_snips.append(h3.get_text().strip())
    
    return list(set(result_snips))[:limit]

def ai_explain_buzzword(keyword, language, context_list, dry_run=False):
    """Uses LLM to analyze cultural nuances and sentiment reversals of memes."""
    # Prompts optimized for cultural reversal and subculture usage
    if language == 'zh':
        prompt = (f"You are an expert in Chinese Internet subculture. Please explain the term '{keyword}' in detail. "
                  f"Include its common TikTok/social media scenarios, positive/negative nuances, true meme meaning, "
                  f"difference from traditional semantics, and modern sample sentences. Reference: {context_list}")
    elif language == 'vi':
        prompt = (f"You are an expert in Vietnamese memes and internet slang. Explain the term '{keyword}' thoroughly "
                  f"based on Vietnamese netizen culture (usage, contrast with traditional sentiment, real-world examples). "
                  f"Context: {context_list}")
    else:
        prompt = (f"You are an expert in Internet subculture. Explain in detail the term '{keyword}' "
                  f"(usage, typical context, subversive sentiment, how it is used differently than traditional sentiment, "
                  f"and sample sentences). Context: {context_list}")

    if dry_run:
        return {"explanation": f"Dry Run Explanation for: {keyword}", "usage": context_list}

    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=512
    )
    return response.choices[0].message.content.strip()

def buzzword_collector(all_keywords, dry_run=True):
    """Orchestrates the collection, search, and AI analysis process."""
    records = []
    for lan, kw in tqdm(all_keywords, desc="Processing Keywords"):
        # Step 1: Search for real context
        examples = google_search_examples(kw, lang=lan, limit=3)
        time.sleep(1.5)  # Rate limiting to prevent IP blocks
        
        # Step 2: AI-driven cultural analysis
        try:
            explanation = ai_explain_buzzword(kw, lan, examples, dry_run=dry_run)
        except Exception as e:
            explanation = f"Failed: {e}\nContext Snippets: {examples}"
        
        records.append({
            "keyword": kw,
            "lang": lan,
            "examples": "; ".join(examples),
            "explain": explanation
        })
    return pd.DataFrame(records)

if __name__ == "__main__":
    print("--- Batch Multi-language Meme Collection & AI Analysis ---")
    print("Ensure internet connectivity and a valid OPENAI_API_KEY environment variable.\n")
    
    # Run the collector (dry_run=False executes actual API calls)
    df = buzzword_collector(all_keywords, dry_run=False)
    
    # Save results for NLP sentiment analysis
    df.to_csv("multilang_tiktok_buzzword_dict.csv", index=False, encoding='utf-8-sig')
    
    print("\nTask Complete! Results saved to: multilang_tiktok_buzzword_dict.csv")
    print(df.head())