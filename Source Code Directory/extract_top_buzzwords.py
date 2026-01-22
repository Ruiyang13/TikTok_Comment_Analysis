# -*- coding: utf-8 -*-
import pandas as pd
from collections import Counter
import re
import jieba
from sklearn.feature_extraction.text import CountVectorizer

def merge_similar_words(word_counter):
    """
    Merges similar words and spelling variants
    - Merges repeated character variants (e.g., haha, hahah, hahahaha -> haha)
    - Merges spelling variants (e.g., kawai, kawaii -> kawaii)
    - Merges case variants
    """
    merged_counter = Counter()
    processed = set()
    
    # Sort by frequency, processing high-frequency words first
    sorted_words = sorted(word_counter.items(), key=lambda x: -x[1])
    
    # Step 1: Handle repeated character variants (e.g., haha, hahahaha)
    base_to_variants = {}
    for word, count in sorted_words:
        if word in processed:
            continue
        # Extract base pattern (removes character repetitions, keeps 2 chars as base)
        base_pattern = re.sub(r'(.)\1+', r'\1\1', word)
        if base_pattern not in base_to_variants:
            base_to_variants[base_pattern] = []
        base_to_variants[base_pattern].append((word, count))
    
    # Merge repeated variants
    for base, variants in base_to_variants.items():
        if len(variants) > 1:
            # Find the shortest reasonable version (usually 2 chars, like "haha")
            best_variant = min(variants, key=lambda x: (len(x[0]), -x[1]))[0]
            total_count = sum(c for _, c in variants)
            merged_counter[best_variant] = total_count
            processed.update([w for w, _ in variants])
    
    # Step 2: Handle spelling variants (e.g., kawai, kawaii, kawwai)
    remaining_words = [(w, c) for w, c in sorted_words if w not in processed]
    for word, count in remaining_words:
        if word in processed:
            continue
        
        # Check for variants with containment relationships (e.g., kawai inside kawaii)
        similar_variants = []
        for other_word, other_count in remaining_words:
            if other_word == word or other_word in processed:
                continue
            # Check if it is a variant (containment or similar spelling)
            is_variant = False
            if word in other_word or other_word in word:
                # Direct containment check
                if abs(len(word) - len(other_word)) <= 3:
                    is_variant = True
            elif abs(len(word) - len(other_word)) <= 2:
                # Check for spelling variations
                min_len = min(len(word), len(other_word))
                prefix_match = sum(1 for i in range(min_len) if word[i] == other_word[i])
                if prefix_match >= min_len - 1:  # Almost complete match
                    is_variant = True
            
            if is_variant:
                similar_variants.append((other_word, other_count))
        
        if similar_variants:
            # Merge into the longest or most common version
            all_variants = [(word, count)] + similar_variants
            best_variant = max(all_variants, key=lambda x: (x[1], len(x[0])))[0]
            total_count = sum(c for _, c in all_variants)
            merged_counter[best_variant] = total_count
            processed.add(word)
            processed.update([w for w, _ in similar_variants])
        else:
            # No variants found, add directly
            merged_counter[word] = count
            processed.add(word)
    
    return merged_counter

def merge_emoji_variants(emoji_counter):
    """Collapses emoji variants (e.g., 😂😂😂 -> 😂)"""
    merged = Counter()
    for emoji, count in emoji_counter.items():
        # Extract single emoji (remove duplicates)
        single_emoji = emoji[0] if emoji else emoji
        merged[single_emoji] += count
    return merged

# Load comment data
df = pd.read_csv('TikTok_cleaned_data_with_language.csv')
comments = df['Comments'].dropna().astype(str).tolist()
print(f"Total comments processed: {len(comments)}")

# Extended English Stopwords
en_stopwords = {
    'the', 'is', 'this', 'you', 'to', 'my', 'in', 'and', 'that', 'it', 'for', 'of', 'a', 'an',
    'on', 'at', 'with', 'from', 'as', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'was',
    'were', 'are', 'can', 'could', 'will', 'would', 'should', 'may', 'might', 'must', 'shall',
    'i', 'me', 'he', 'she', 'him', 'her', 'we', 'us', 'they', 'them', 'his', 'hers', 'our',
    'your', 'their', 'its', 'what', 'which', 'who', 'whom', 'whose', 'where', 'when', 'why',
    'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such',
    'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'now',
    'then', 'here', 'there', 'any', 's', 't', 'don'
}

# Chinese Stopwords
cn_stopwords = {
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'
}

# Vietnamese Stopwords
vi_stopwords = {
    'và', 'của', 'là', 'thì', 'mà', 'này', 'đó', 'cho', 'rằng', 'cái', 'nói', 'như', 'nhưng',
    'khi', 'một', 'được', 'không', 'với', 'đã', 'đang', 'nên', 'có', 'còn', 'ai', 'sao', 'tôi'
}

# Initialize lists for different languages
zh_words = []
en_words = []
vi_words = []
emoji_list = []

for idx, comment in enumerate(comments):
    if idx % 1000 == 0:
        print(f"Processing comment {idx}/{len(comments)}...")
    
    # Extract emojis
    emojis = re.findall(r'[\U0001F300-\U0001F9FF\U0001FA00-\U0001FAFF\U00002600-\U000027BF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF]', comment)
    emoji_list.extend(emojis)
    
    # Get language based on the DataFrame column
    lang = str(df.iloc[idx]['Language']) if idx < len(df) else 'unknown'
    
    # Chinese Processing
    if 'zh' in lang.lower() or any('\u4e00' <= char <= '\u9fff' for char in comment):
        segs = jieba.lcut(comment)
        for w in segs:
            w = w.strip()
            if len(w) > 1 and w not in cn_stopwords and not w.isdigit() and not re.match(r'^[a-zA-Z]+$', w):
                zh_words.append(w)
    
    # English Processing
    if lang.lower() in ['en', 'unknown'] or any(char.isascii() and char.isalpha() for char in comment):
        en_tokens = re.findall(r'\b[a-zA-Z]{2,}\b', comment.lower())
        for w in en_tokens:
            if w not in en_stopwords and len(w) > 2:
                en_words.append(w)
    
    # Vietnamese Processing
    if 'vi' in lang.lower():
        vi_tokens = re.findall(r'\b[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]{2,}\b', comment.lower())
        for w in vi_tokens:
            if w not in vi_stopwords and len(w) > 2:
                vi_words.append(w)

# Calculate frequencies
zh_counter = Counter(zh_words)
en_counter = Counter(en_words)
vi_counter = Counter(vi_words)
emoji_counter = Counter(emoji_list)

print("\nMerging similar words and variants...")

# Merge variants
zh_counter = merge_similar_words(zh_counter)
en_counter = merge_similar_words(en_counter)
vi_counter = merge_similar_words(vi_counter)
emoji_counter = merge_emoji_variants(emoji_counter)

def final_merge_variants(word_list):
    """Final pass to merge remaining variants (e.g., kawai, kawaii, kawwai -> kawaii)"""
    merged = []
    processed = set()
    
    # Sort by length and position, processing short words first as they might be parts of long ones
    sorted_words = sorted(word_list, key=lambda w: (len(w), word_list.index(w)))
    
    for word in sorted_words:
        if word in processed:
            continue
        
        # Find all variants
        variants = [word]
        for w in word_list:
            if w in processed or w == word:
                continue
            
            is_variant = False
            # 1. Direct containment
            if word in w or w in word:
                if abs(len(word) - len(w)) <= 3:
                    is_variant = True
            
            # 2. Similar spelling
            if not is_variant and abs(len(word) - len(w)) <= 2:
                min_len = min(len(word), len(w))
                if min_len >= 3:
                    # Check prefix match (at least 2 of first 3 chars match)
                    prefix_match = sum(1 for i in range(min(3, min_len)) if word[i] == w[i])
                    if prefix_match >= 2:
                        # Check overall char similarity
                        common_chars = sum(1 for c in set(word) if c in w)
                        if common_chars >= min(len(word), len(w)) - 1:
                            is_variant = True
        
            if is_variant:
                variants.append(w)
        
        if len(variants) > 1:
            # Keep longest/most common version
            best = max(variants, key=lambda w: (len(w), -variants.index(w)))
            merged.append(best)
            processed.update(variants)
        else:
            merged.append(word)
            processed.add(word)
    
    return merged

# Get top words (filtering low frequency)
top_zh_raw = [w for w, cnt in zh_counter.most_common(200) if cnt >= 3]
top_en_raw = [w for w, cnt in en_counter.most_common(200) if cnt >= 5]
top_vi_raw = [w for w, cnt in vi_counter.most_common(200) if cnt >= 3]

# Execute final merge
top_zh = final_merge_variants(top_zh_raw)
top_en = final_merge_variants(top_en_raw)
top_vi = final_merge_variants(top_vi_raw)
top_emoji = [e for e, cnt in emoji_counter.most_common(50) if cnt >= 2]

# N-gram analysis (long phrases)
print("Extracting n-grams (2-5 words)...")
vect = CountVectorizer(
    analyzer='word',
    ngram_range=(2, 5),
    min_df=2,
    max_features=500,
    stop_words=list(en_stopwords)
)
X = vect.fit_transform(comments)
ngram_freq = sorted(zip(vect.get_feature_names_out(), X.sum(axis=0).A1), key=lambda x: -x[1])
top_ngrams = [k for k, v in ngram_freq[:200] if len(k.strip().replace(' ', '')) > 2]

def merge_semantically_similar_phrases(phrase_list):
    """
    Merges semantically related phrases
    Example: "face card" + "saving" -> "face card saving"
    """
    merged = []
    processed = set()
    
    # Define semantic mapping (Keywords -> Target Phrase)
    semantic_patterns = {
        ('face', 'card', 'saving'): 'face card saving',
        ('face', 'card'): 'face card saving',
        ('card', 'saving'): 'face card saving',
        ('second', 'hand', 'embarrassment'): 'second hand embarrassment',
        ('second', 'hand'): 'second hand embarrassment',
        ('hand', 'embarrassment'): 'second hand embarrassment',
        ('social', 'anxiety'): 'social anxiety is anxious of her',
        ('pushing', '30'): 'pushing 30s btw',
    }
    
    phrase_words_dict = {p: set(p.lower().split()) for p in phrase_list}
    
    for pattern_keywords, target_phrase in semantic_patterns.items():
        pattern_set = set(pattern_keywords)
        found_variants = []
        
        for phrase in phrase_list:
            if phrase in processed:
                continue
            phrase_words = phrase_words_dict[phrase]
            overlap = len(pattern_set & phrase_words)
            if (overlap >= len(pattern_set) * 0.5 or pattern_set.issubset(phrase_words)):
                found_variants.append(phrase)
        
        if found_variants:
            best = target_phrase if target_phrase in phrase_list else max(found_variants, key=lambda p: (len(p), phrase_list.index(p)))
            if best not in merged:
                merged.append(best)
            processed.update(found_variants)
    
    # Handle remaining phrases
    remaining = [p for p in phrase_list if p not in processed]
    remaining_sorted = sorted(remaining, key=lambda p: (len(p.split()), remaining.index(p)))
    
    for phrase in remaining_sorted:
        if phrase in processed:
            continue
        similar = []
        phrase_words = set(phrase.lower().split())
        for p in remaining:
            if p == phrase or p in processed:
                continue
            p_words = set(p.lower().split())
            overlap_ratio = len(phrase_words & p_words) / max(len(phrase_words), len(p_words))
            if (phrase in p or p in phrase or overlap_ratio >= 0.6):
                similar.append(p)
        
        if similar:
            all_phrases = [phrase] + similar
            best = max(all_phrases, key=lambda p: (len(p.split()), remaining.index(p)))
            if best not in merged:
                merged.append(best)
            processed.update(all_phrases)
        else:
            merged.append(phrase)
            processed.add(phrase)
    
    return merged

print("Merging semantically similar phrases...")
merged_ngrams = merge_semantically_similar_phrases(top_ngrams)

# Output results to file
with open('autodetect_buzzword_candidates.txt', 'w', encoding='utf-8') as fout:
    fout.write('=== Chinese Keywords (Top 100, Merged) ===\n')
    fout.write(','.join(top_zh[:100]))
    fout.write('\n\n=== English Keywords (Top 100, Merged) ===\n')
    fout.write(','.join(top_en[:100]))
    fout.write('\n\n=== Vietnamese Keywords (Top 50, Merged) ===\n')
    fout.write(','.join(top_vi[:50]))
    fout.write('\n\n=== Top Emojis (Top 30, Merged) ===\n')
    fout.write(','.join(top_emoji[:30]))
    fout.write('\n\n=== Top Phrases n-grams (Top 100, Semantically Merged) ===\n')
    fout.write('\n'.join(merged_ngrams[:100]))

print(f"\nExtraction complete!")
print(f"Chinese words: {len(top_zh)}")
print(f"English words: {len(top_en)}")
print(f"Vietnamese words: {len(top_vi)}")
print(f"Emojis: {len(top_emoji)}")
print(f"Phrases: {len(merged_ngrams)}")
print("\nResults saved to autodetect_buzzword_candidates.txt")
