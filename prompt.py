def get_sales_summary_prompt(conversation, start_date, end_date):
    """Prompt for creating a concise sales summary from the conversation."""
    return f"""
You are analyzing a Slack conversation from the sales team channel. The participants are primarily Miles, Ben, and Brent, who are discussing sales activities for an AI company.

Your task is to provide an executive sales summary focused on actionable insights valuable to the CEO, Sales Manager, and Account Executives.

Create a scannable summary that highlights key business impacts and action items.

Format the response exactly like this:
📅 *Sales Team Summary ({start_date} - {end_date})*
---

👥 *Customer & Market Insights:*
• [Critical feedback, patterns, or market intelligence]

📈 *Strategic Initiatives:*
• [Confirmed] [List confirmed decisions and actions]
• [In Progress] [List active initiatives, blockers, support needs, or immediate actions required]

🔗 *Key Resources:*
• [Only critical documents/links]

Include:

1. **Customer Interactions & Market Insights**:
    • Key meetings and outcomes
    • Customer feedback or concerns
    • Success stories or testimonials
    • Competitive intelligence
    • Market feedback
    • Feature requests or product gaps

2. **Strategic Initiatives**:
    • Confirmed decisions ("Decision: [item]")
    • Active initiatives ("Action: [item] - Owner: [name]")

3. **Resources & Support**:
    • Important files/links shared
    • Sales collateral needs
    • Cross-team support requests

Keep the summary focused on actionable insights and clear distinctions between confirmed plans and discussions.

Conversation:
{conversation}
"""