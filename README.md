# TikTok_Comment_Analysis

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Complete-green)]()
[![Privacy](https://img.shields.io/badge/Data%20Privacy-Enforced-red)]()

For a content creator, feedbacks are one of the most crucial things. 

**Author:** exploding_rat  
**Tools Used:** JavaScript, Excel , Python  
**Date:** December 2025

As a TikTok creator (**@exploding_rat**) with **65k followers** and **2.6M likes**, my content relies on a specific persona: *"cringe / make others uncomfortable / no social anxiety"*

Standard analytics provided by TikTok track the quantity of comments, but they fail to track *meaning* behind (do they even get the joke?). Therefore, this project uses **NLP** to analyze **10k+ comments** across 69 videos. 

## 🎯 Project Objective
To move beyong the quantitative statistics already provided by TikTok, and extract actionable insights from unstructured comments. 

### File Organization & Purpose
| Location | File | Logic Purpose |
| :--- | :--- | :--- |
| **src/** | `clean_and_detect_language.py`| **Preprocessing:** Sanitizes text and classifies linguistic origins. |
| **src/** | `extract_top_buzzwords.py` | **Frequency Detection:** Identifies top 100 high-frequency words. |
| **src/** | `explain_buzzwords_from_file.py`| **LLM Intelligence:** Uses GPT-4o-mini to define buzzwords. |
| **src/** | `question_and_fan_requests_extraction.py`| **Heuristics:** Regex-based detection for questions and requests. |
| **src/** | `question_intent_classification.py`| **Intent Analysis:** Categorizes inquiries (e.g., Rhetorical/Content Request). |
| **src/** | `content_request_analysis.py`| **Reporting:** filters out rhetorical noise from labeled data, to produce actionable fan requests in both Markdown and Excel formats. |
| **src/** | `user_behavior_analysis.py` | **Behavioral Modeling:** Calculates Loyalty and Authenticity scores. |
| **Root** | `app.py` | **Streamlit Dashboard:** The primary UI for data visualization. |
## 🛠️ Methodology

### Data Collection
I used a JavaScript script to scrape the DOM and extract the following features:
* **Video Metadata:** Video ID, Caption, Hashtags, Creator Likes.
* **Engagement Metrics:** Comment Likes, Reply Counts.
* **User Data:** Usernames, Timestamps.
<details>
<summary><b>Click to view the full JavaScript Scraper code</b></summary>

```javascript
(function() {
    // --- PART 1: Define Scope ---
    // Finds the active video container by looking for any comment (level 1 or 2)
    let anchor = document.querySelector('[data-e2e="comment-level-1"], [data-e2e="comment-level-2"]');
    let scope = document.body;
    if (anchor) {
        scope = anchor.closest('article') || 
                anchor.closest('div[class*="DivVideoDetailContainer"]') || 
                document.body;
    }

    // --- PART 2: Extract Video Metadata ---
    let url = window.location.href;
    let videoId = url.split('video/')[1]?.split('?')[0] || "Unknown";
    
    // Caption & Hashtags
    let rawCaption = "No Caption";
    let hashtags = "No Hashtags";
    let descEl = scope.querySelector('[data-e2e="video-desc"]');
    if (descEl) {
        rawCaption = descEl.innerText.replace(/[\n\r\t]+/g, " ");
        hashtags = rawCaption.match(/#[^\s#]+/g)?.join(', ') || "No Hashtags";
    }

    // Post Date (From Creator Info Container)
    let postDate = "Unknown Date";
    let infoContainer = scope.querySelector('div[class*="DivCreatorInfoContainer"]');
    if (infoContainer) {
        let textNodes = infoContainer.innerText.split('·');
        if (textNodes.length > 1) {
            postDate = textNodes[textNodes.length - 1].trim();
        }
    }

    // Video Stats
    let vidLikes = scope.querySelector('[data-e2e="like-count"]')?.innerText || "0";
    let vidShares = scope.querySelector('[data-e2e="share-count"]')?.innerText || "0";
    let vidViews = ""; // Blank for manual entry

    // --- PART 3: Extract Comments (Level 1 & Level 2) ---
    // Targets both main comments AND manually expanded replies
    let commentItems = scope.querySelectorAll('[data-e2e="comment-level-1"], [data-e2e="comment-level-2"]');

    if (commentItems.length === 0) {
        alert("No comments found! Please scroll down or open some replies first.");
        return;
    }

    let outputData = "";

    commentItems.forEach(textEl => {
        // Find the parent container for this specific comment/reply
        let row = textEl.closest('div[class*="CommentItem"]') || 
                  textEl.closest('div[class*="ContentWrapper"]') || 
                  textEl.parentElement.parentElement;

        if (!row) return;

        // Grab username (works for both level-1 and level-2)
        let username = row.querySelector('[data-e2e^="comment-username"]')?.innerText.replace(/[\n\r\t]+/g, " ") || "Unknown";
        let commentText = textEl.innerText.replace(/[\n\r\t]+/g, " ");
        
        // Grab comment-specific likes
        let comLikes = row.querySelector('[data-e2e="comment-like-count"]')?.innerText || 
                       row.querySelector('div[class*="DivLikeContainer"] span')?.innerText || "0";

        // Output row structure:
        // VideoID | URL | PostDate | Caption | Hashtags | Views | VidLikes | VidShares | User | Comment | ComLikes
        outputData += `${videoId}\t${url}\t${postDate}\t${rawCaption}\t${hashtags}\t${vidViews}\t${vidLikes}\t${vidShares}\t${username}\t${commentText}\t${comLikes}\n`;
    });

    // --- PART 4: Copy to Clipboard ---
    let dummy = document.createElement("textarea");
    document.body.appendChild(dummy);
    dummy.value = outputData;
    dummy.select();
    document.execCommand("copy");
    document.body.removeChild(dummy);

    console.log(`Success! Scraped ${commentItems.length} total rows.`);
    alert(`Success!\n\nCaptured ${commentItems.length} comments & replies.\n\nVideo: ${videoId}\nLikes: ${vidLikes}\n\nPaste into Excel (Ctrl+V).`);
})();
```
</details>

## The original dataset
### This dataset contains 11 columns and 10,880 rows of data (excluding the header row). Each row records a comment for a specific video, meaning the same Video ID appears multiple times.

| Column | Description |
| :--- | :--- |
| `Video_ID` | Unique identifier for the video post |
| `URL`| Direct web link to the specific TikTok video |
| `Post Date`| The date the video was originally uploaded |
| `Caption` | The text description accompanying the video |
| `Hashtags` | List of tags used in the post |
| `Vid Likes` | Total like count for the video post itself |
| `Vid Views`| Total view count for the video as of Decemember 27th |
| `Vid Shares` | Total number of times the video was shared |
| `Comment_Text` | The text content (sanitized) |
| `Comment_Likes` | Engagement on the specific comment |
| `Username` | Display name of the user who commented |

## 🔒 Data Privacy & Schema
To respect the privacy of the commenters, **raw datasets are NOT included** in this repository. All analysis is performed locally. 

## Data cleaning: 
 1. Standardize dates, likes, views, likes.
 2. Deleted duplicate comments. (Identical comments from the same user under the same video)
 3. Replaced empty comments with Nil. (Empty comment highly likely meant that it was an image, but the code I used above was not able to capture it ,and image analysis is another level of difficulty, thus I will ignore them for now, despite them being a quite important part of comments.)


## 🧩 The 4 Core Components

### Component 1: Meme Lifecycle Analysis 
**Trying to see *when* a meme dies.**

*   **Methodology:**
    *   **Weighted TF-IDF(Term Frequency - Inverse Document Frequency) Extraction:** I used `Comment Likes` as a weight. A meme with high comment likes count (e.g., *"hard watch"*) is assigned a higher weight than frequent but low-engagement terms.
    *   **Non-linear Fatigue Analysis:** Moving beyond linear regression to identify "inflection points." Analysis shows that when a specific meme (e.g., *"chanh noe"*) exceeds **15-20%** of total comment volume, user engagement rates exhibit a non-linear decline .
    *   **ML Feature Enhancement:** "Lifecycle Stage" (Rising, Mature, Stale) was engineered as a feature for the **Random Forest** model, improving the engagement prediction accuracy ($R^2$ Score) by **4.65%** .

*   **Key Insights:**
    *   **Meme Vitality:** *"chanh noe"* is the absolute core driver, with 552 occurrences and a high confidence interval.
    *   **Early Warning System:** The code detects "aesthetic fatigue." While *"hard watch"* has high interaction rates, marginal returns diminish when its frequency becomes too high within a single video.

### Component 2: Cross-Cultural Resonance 
**Trying to see the differences between commenters using different language.**

*   **Methodology:**
    *   **Mann-Whitney U Test:** Used to statistically verify engagement differences between Singlish and Standard English comments ($P\text{-Value} = 0.0991$, indicating no significant difference, but qualitative analysis suggests strong identity resonance) .
    *   **Cultural Isolation Ratio:** Calculated via the metric: $(\text{Avg Likes in Hot Lang}) / (\text{Avg Likes in Cold Lang})$.
    *   **Correlation Matrix:** Analyzed the correlation between language composition and `Vid Shares`.

*   **Key Insights:**
    *   **The Language Dividend:** While English is the dominant language (34% of comments), Vietnamese comments show a high correlation of **0.793** with video shares, far exceeding English and Chinese. This identifies my Vietnamese audiences are a primary engine for improving the virality of my videos.
    *   **Cultural Isolation: The meme *"chanh noe"* averages **17.94** likes in Vietnamese contexts but only **0.09** in English. This **197x difference** proves it is a community-specific "cultural code" rather than a global meme.
    *    **Echo Chambers:** Specific hashtags induce specific linguistic behaviors. Using #bostickchen (a reference to a Chinese creator) increased teasing behavior in Chinese comments by 33%, whereas #slay induced performative praise in English comments. The meme *"chanh noe"* (a reference to a Chinese creator) averages **17.94** likes in Vietnamese contexts but only **0.09** in English. This **197x difference** proves it is a community-specific "cultural code" rather than a global meme.


### Component 3: Strategic Intent Filtering (NLP Classification)
**Helping me more effectively identify the comments to reply to.**

*   **Methodology:**
  
1. Broad Capture (is_potential_question): The system first flags comments containing interrogative keywords (Who, What, Where, How) or auxiliary verbs (Can, Is, Do), identifying questions even if the user omitted punctuation (e.g., "where did you get that shirt").
2. Intent Classification: The algorithm then sorts these potential questions into different intents.
   
    *   **Intent Classifier:** Using Regex and keyword logic to categorize comments into four distinct intents:
        1.  **Content_Request:** Specific demands (e.g., *"Piano and singing"*).
        2.  **Information_Inquiry:** Genuine questions (e.g., *"is this NTU?"*) 
        3.  **Rhetorical_Shock:** Reactions of disbelief (e.g., *"why is the video an hour long?!"*) — usually not requiring a reply.
        4.  **Identity_Verification:** Confirmation of background. 

*   **Key Insights:**
    *   **High-Value Interactions:** The code successfully filtered valuable inquiries from noise.
    *   **Content Roadmap:** Filtered specific demand signals for *"Singing"* and *"Hard watch"* series, providing data-driven direction for future video topics.

### Component 4: Individual User Analysis (CRM & Bot Detection)
**Identifying Hardcore Fans**

*   **Methodology:**
    *   **Loyalty Index:** Calculated based on the number of **unique videos** a user has commented on.
    *   **Authenticity Score:** Based on the **variance** of text diversity. Logic: If a user posts 10 comments containing only "😂😂😂", variance is 0, resulting in a low authenticity score.

*   **Key Insights:**
*   The "Hardcore Fans" : The top 1% of loyal users (commenting on >20 videos) tend to leave comments with high lexical diversity. They reference past videos, indicating deep engagement.
*   The "Bot" Detection: The algorithm flagged a specific cohort of users who commented on 10+ videos with identical strings (e.g., "😍😍😍"). These users had an Authenticity Score near 0.0, allowing them to be filtered out of strategic sentiment analysis to prevent data skewing.

---
