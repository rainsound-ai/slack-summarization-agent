def get_channel_prompt(channel_name, conversation):
    """Prompt for individual channel summaries."""
    return f"""
    Analyze this Slack conversation from the sales team channel. The participants are primarily Miles, Ben, and Brent, 
    who are discussing sales activities for an AI company. Provide a structured summary focused on sales insights.

    Include:
    1. Deal Pipeline Updates:
        • New opportunities identified
        • Deal stages and changes
        • Potential deal values (if mentioned)
    
    2. Customer Interactions:
        • Key meetings and outcomes
        • Customer feedback or concerns
        • Success stories or testimonials
    
    3. Sales Strategy:
        • Confirmed decisions ("Decision: [item]")
        • Active initiatives ("Action: [item] - Owner: [name]")
        • Ideas being explored ("Strategy Discussion: [items]")
    
    4. Product/Market Insights:
        • Competitive intelligence
        • Market feedback
        • Feature requests or product gaps
    
    5. Resources & Support:
        • Important files/links shared
        • Sales collateral needs
        • Cross-team support requests

    Keep the summary focused on actionable insights and clear distinctions between confirmed plans vs. discussions.
    
    Conversation:
    {conversation}
    """

def get_final_summary_prompt(channel_summaries, start_date, end_date):
    """Prompt for creating the final ultra-concise summary."""
    return f"""You are creating an executive sales summary for an AI company's leadership team.
    Focus on insights valuable to the CEO, Sales Manager, and Account Executives.
    
    Create a scannable summary that highlights key business impacts and action items.
    
    Format the response exactly like this:
    📅 *Sales Team Summary ({start_date} - {end_date})*
    ---

    💰 *Pipeline & Deals:*
    • [Key updates on deals, conversions, and revenue impact]

    👥 *Customer & Market Insights:*
    • [Critical feedback, patterns, or market intelligence]

    📈 *Strategic Initiatives:*
    • [Confirmed] [List confirmed decisions and actions]
    • [In Progress] [List active initiatives]
    • [Exploring] [List strategies under discussion]

    ⚠️ *Needs Attention:*
    • [Blockers, support needs, or immediate actions required]

    🔗 *Key Resources:*
    • [Only critical documents/links]

    Channel Summaries to Process:
    {channel_summaries}
    """