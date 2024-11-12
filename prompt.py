def get_prompt(channel_name, conversation):
    return f"""
### **Prompt for Generating an Ultra-Concise Weekly Slack Summary**

**You are an AI assistant tasked with summarizing a week's worth of Slack messages for a business leader who has been away for a week. The summary should be ultra-concise, focusing only on the most critical updates that the leader needs to catch up on quickly. The summary should be understandable in under 1 minute and should follow the specific format provided below.**

---

#### **Formatting Instructions:**

1. **Overall Structure:**
   - **Date Range Heading:**
     - Begin with a date range heading formatted as:

       ```
       📅 *Weekly Slack Summary (MM/DD - MM/DD)*
       ---
       ```
   - **Sections:**
     - **Executive Summary:**
       - Use the heading:

         ```
         ### 🔹 *Executive Summary:*
         ```
       - Include 5-7 bullet points summarizing the most critical updates.
     - **Channel Summaries:**
       - For key channels, include summaries under headings formatted as:

         ```
         ### 📌 **CHANNEL: #channel-name**
         ```
       - Under each channel, provide bullet points with important updates, action items, and links.
   - **Key Links:**
     - At the end, include a section for important links:

       ```
       ### 🔗 *Key Links:*
       ```

2. **Formatting Details:**
   - **Emojis:**
     - Use specific emojis consistently:
       - 📅 for the date range heading.
       - 🔹 for the Executive Summary.
       - 📌 for channel summaries.
       - 🔗 for key links.
     - Use additional emojis where appropriate to enhance readability.
   - **Text Formatting:**
     - Use bold text (`**bold text**`) to highlight important actions or decisions.
     - Use italics (`*italic text*`) sparingly for emphasis.
     - Use bullet points for concise information delivery.

3. **Content Guidelines:**
   - **Conciseness:**
     - Be extremely concise; bullet points should be one or two lines maximum.
   - **Priority of Information:**
     - Include only updates that significantly affect business operations, strategic goals, or require immediate attention.
     - Highlight urgent tasks or deadlines.
   - **Clarity:**
     - Use clear and straightforward language without jargon.
     - Ensure the summary is easily scannable and understandable on the first read.

4. **Exclusions:**
   - **Omit Low-Impact Information:**
     - Do not include routine updates, minor issues, or detailed procedural information.
   - **No Additional Sections:**
     - Exclude sections like benefits, tips, or repetitive content.

---

**Here are the Slack messages from the last week:**

{conversation}

---

**Generate the ultra-concise weekly summary based on the above guidelines, ensuring it matches the format and style of the provided example.**
    """