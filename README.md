# TikTok_Comment_Analysis
As a content creator, feedbacks are one of the most crucial things. 


**Author:** exploding_rat  
**Tools Used:** JavaScript, Excel , Python  
**Date:** December 2025

## 🎯 Project Objective
To analyze comments under my own videos.

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
## Data cleaning: 
### 1. Standardize dates, likes, views, likes.
### 2. Deleted duplicate comments.
### 3. Replaced empty comments with Nil. (Empty comment highly likely meant that it was an image, but the code I used above was not able to capture it ,and image analysis is another level of difficulty, thus I will ignore them for now, despite them being a quite important part of comments.)


