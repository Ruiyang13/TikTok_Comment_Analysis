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
    // --- PART 1: Video Context (Parent Data) ---
    let url = window.location.href;
    let videoId = url.split('video/')[1]?.split('?')[0] || "Unknown ID";
    
    // Scrape Caption & Extract Hashtags
    let rawCaption = document.querySelector('[data-e2e="video-desc"]')?.innerText.replace(/[\n\r\t]+/g, " ") || "";
    let hashtags = rawCaption.match(/#[^\s#]+/g)?.join(', ') || "No Hashtags";
    
    // Scrape Video Metrics
    let vidLikes = document.querySelector('[data-e2e="like-count"]')?.innerText || "0";
    let vidShares = document.querySelector('[data-e2e="share-count"]')?.innerText || "0";

    // --- PART 2: Comment Mining (Child Data) ---
    // Targets the specific container class for TikTok's current DOM structure
    let commentItems = document.querySelectorAll('div[class*="DivCommentItemWrapper"]');

    if (commentItems.length === 0) {
        alert("No comments found! Scroll down first.");
        return;
    }

    let outputData = "";

    commentItems.forEach(item => {
        // Scrape User & Text
        let username = item.querySelector('[data-e2e="comment-username-1"]')?.innerText.replace(/[\n\r\t]+/g, " ") || "Unknown";
        let text = item.querySelector('[data-e2e="comment-level-1"]')?.innerText.replace(/[\n\r\t]+/g, " ") || "";
        
        // Scrape Engagement Metrics
        let likes = item.querySelector('div[class*="DivLikeContainer"] span')?.innerText || "0";
        let time = item.querySelector('div[class*="DivCommentSubContentWrapper"] span')?.innerText || "Unknown";

        // Logic to extract Reply Count from "View X replies" button
        let replyBtn = item.querySelector('[data-e2e="comment-reply-count"]'); 
        let replyCount = "0";
        if (replyBtn) {
            replyCount = replyBtn.innerText.match(/\d+/)?.[0] || "0";
        }

        // Format data with Tab separators for Excel
        outputData += `${videoId}\t${url}\t${rawCaption}\t${hashtags}\t${vidLikes}\t${vidShares}\t${username}\t${text}\t${likes}\t${replyCount}\t${time}\n`;
    });

    // --- PART 3: Export to Clipboard ---
    let dummy = document.createElement("textarea");
    document.body.appendChild(dummy);
    dummy.value = outputData;
    dummy.select();
    document.execCommand("copy");
    document.body.removeChild(dummy);

    console.log(`Success! Scraped ${commentItems.length} comments.`);
})();
