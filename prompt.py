def get_sales_summary_prompt(conversation, start_date, end_date):
    """Prompt for creating an executive summary from the conversation."""
    return f"""
You are analyzing a Slack conversation from the sales team channel. The participants are primarily Miles, Ben, Brent, and Busch, discussing sales activities for an AI company.

Your task is to provide an **executive summary** focused on identifying important **strategic initiatives** and any proposed **next steps**.

Create a summary in the following format exactly:

📅 *Executive Summary ({start_date} - {end_date})*
---

**Strategic Initiatives:**
- *Name of Initiative 1* (Involved: [Names], Context: [Brief context]) ([Link to message])
- *Name of Initiative 2* (Involved: [Names], Context: [Brief context]) ([Link to message])

**Next Steps:**
- *Name of Next Step 1* (Involved: [Names], Related to: [Strategic Initiative]) ([Link to message])
- *Name of Next Step 2* (Involved: [Names], Related to: [Strategic Initiative]) ([Link to message])

**Key Links:**
- [List of important links shared]

**Instructions:**
- Focus on important things happening in the sales channel.
- Identify any next steps proposed for those important things.
- Include **who is involved** and brief **context**.
- **Hyperlink** to the specific message(s) or thread(s) you are drawing your content from.
- Format hyperlinks in Slack markdown as `<URL|Display Text>`.
- Ensure the summary is clear, concise, and actionable.

**Conversation:**
{conversation}
"""