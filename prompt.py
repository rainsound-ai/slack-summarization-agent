def get_channel_prompt(channel_name, conversation):
    """Prompt for individual channel summaries."""
    return f"""
    Analyze this Slack conversation from the channel #{channel_name} and provide a concise summary.
    Include:
    1. Main topic(s) discussed
    2. Key decisions made (if any)
    3. Action items (if any)
    4. Important quotes (if relevant)
    5. Relevant files and links shared (include the URLs if they seem important)
    
    Keep the summary brief and focused on the most important points.
    If files or links were shared, include them only if they're relevant to the main discussion.
    
    Conversation:
    {conversation}
    """

def get_final_summary_prompt(channel_summaries, start_date, end_date):
    """Prompt for creating the final ultra-concise summary."""
    return f"""You are creating an executive summary of Slack conversations for busy business leaders.
    Be extremely selective - only include information that would be valuable at the executive level.
    
    Create a brief, scannable summary that can be read in under 1 minute.
    
    Format the response exactly like this:
    📅 *Weekly Slack Summary ({start_date} - {end_date})*
    ---

    🔹 *Executive Summary:*
    • [3-5 most critical updates or decisions that affect the business]

    [Only include channels with significant updates]
    📌 *CHANNEL: #channel-name*
    • [1-2 bullet points max per channel, focus on decisions and actions]

    🔗 *Key Links:*
    • [Only include links that executives must review]

    Channel Summaries to Process:
    {channel_summaries}
    """