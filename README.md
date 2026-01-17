# TikTok_Comment_Analysis

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Complete-green)]()
[![Privacy](https://img.shields.io/badge/Data%20Privacy-Enforced-red)]()

For a content creator, feedbacks are one of the most crucial things. 

**Author:** exploding_rat  
**Tools Used:** JavaScript, Excel , Python  
**Date:** December 2025

As a TikTok creator (**@exploding_rat**) with **65k followers** and **2.6M likes**, my content relies on a specific persona: *"cringe / make others uncomfortable / no social anxiety"*

Standard analytics provided by TikTok track the quantity of comments, but they fail to track *meaning* behind (do they even get the joke?). Therefore, this project uses **NLP** and **Machine Learning** to analyze **10k+ comments** across 69 videos. 

## 🎯 Project Objective
To analyze comments under my own videos. The challenging part of this project is that many comments used Gen-z slangs and memes, thus traditional way of sentiment analysis may not work very well. In addition, the comments come in many different languages, so some processing also needs to be done. Sadly many comments include images or stickers, but I will not touch on that for now. 


## 🔒 Data Privacy & Schema
To respect the privacy of the commenters, **raw datasets are NOT included** in this repository. All analysis is performed locally. The dataset structure used for the models is described below:

### 1. Comment Data Schema (`TikTok_with_PCS_scores.csv`)
| Column | Description |
| :--- | :--- |
| `Video_ID` | Unique identifier for the video post |
| `Comment_Text` | The text content (sanitized) |
| `Comment_Likes` | Engagement on the specific comment |
| `Language` | Detected language (e.g., 'en', 'zh-cn', 'vi') |
| `PCS_Score` | **Persona Congruence Score** (0.0 - 1.0): My custom metric for "persona fit" |
| `Sentiment_Label`| "Ironic Positive", "Generic Positive", or "Neutral" |

### 2. User Behavior Schema (`user_behavior_summary.csv`)
| Column | Description |
| :--- | :--- |
| `Loyalty_Index` | Number of unique videos a user has commented on |
| `Authenticity` | Score based on comment variety (detects repetitive bots) |
| `Avg_Likes` | Average likes their comments receive (Community Status) |



## 🛠️ Methodology
I extracte data directly from the TikTok web interface using browser console scripts.

### 1. Data Collection
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

## Data cleaning: 
 1. Standardize dates, likes, views, likes.
 2. Deleted duplicate comments.
 3. Replaced empty comments with Nil. (Empty comment highly likely meant that it was an image, but the code I used above was not able to capture it ,and image analysis is another level of difficulty, thus I will ignore them for now, despite them being a quite important part of comments.)



## 🧩 The 5 Core Components

### Component 1: Meme Lifecycle Analysis (Stage 1)
Tracking the rise and fall of community-specific buzzwords to predict "content fatigue."
*   **Method:** TF-IDF extraction weighted by engagement.
*   **Key Insight:** The meme *"chanh noe"* shows a decline in engagement effectiveness once it exceeds **15%** of total comment volume [Source: meme_lifecycle_results.csv].

### Component 2: Cross-Cultural Resonance (Stage 2)
Analyzing how "Cringe" translates across **English, Chinese, Vietnamese, and Korean** audiences.
*   **Method:** Language detection + Correlation Matrix.
*   **Key Insight:** **Vietnamese (VI)** comments have the highest correlation with **Video Shares**, indicating a "Language Dividend" where specific sub-communities drive virality [Source: stage4_cross_cultural_report.md].

### Component 3: Persona Alignment Scoring (PCS)
A custom algorithm (0-1) to quantify if a user "gets the joke."
*   **Logic:** Distinguishes between genuine hate (Low PCS) and ironic compliments like *"Hard watch"* or *"Social anxiety is scared of her"* (High PCS).
*   **Result:** Comments traditionally flagged as "Negative" by VADER sentiment analysis actually correlate with higher engagement [Source: persona_alignment_analysis.csv].

### Component 4: Strategic Intent Filtering
Automated classification of user demands to drive content strategy.
*   **Tools:** Regex + Intent Classification.
*   **Output:** Separates **"Content Requests"** (e.g., *"Singing videos please"*) from **"Rhetorical Questions"** (e.g., *"Why is she like this?"*) [Source: fan_requests.csv].

### Component 5: Individual User Analysis (CRM)
Analyzing the *commenters* themselves to identify "Soul Fans" vs. "Bots."
*   **Loyalty Index:** Identifies users like *Mayurindere* (Commented on 29 videos) vs one-time passersby [Source: user_detailed_report.md].
*   **Authenticity Score:** Filters out users who span generic emojis (e.g., "😍😍😍") to find high-value interactions.
