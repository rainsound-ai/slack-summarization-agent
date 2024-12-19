def get_sales_summary_prompt(conversation, milestones, start_date, end_date):
    return f"""
    You are analyzing a Slack conversation.

    Your task is to provide an executive summary focused on progress towards completing our current milestones and next steps for completing those milestones.

    For each person in the conversation, assign them a next step. Each next step should be a single action item that the person can do to help complete the milestones.

    If a milestone has no progress, or is not relevant to the conversation, do not include it in the summary.

    Create a summary in exactly this format:

    Executive Summary ({start_date} - {end_date})
    ---

    Milestone Progress:
    - [Milestone]: ([What progress has been made on this milestone, no more than 50 words]) <message_url|View Thread>
    - [Milestone]: ([What progress has been made on this milestone, no more than 50 words]) <message_url|View Thread>

    Next Steps:
    - [Action Item] (Assigned to: @[Name], Description: [No more than 20 words], How does this help reach the milestone: [No more than 20 words], Deadline: [Choose from today, tomorrow, or next week]) <message_url|View Thread>
    - [Action Item] (Assigned to: @[Name], Description: [No more than 20 words], How does this help reach the milestone: [No more than 20 words], Deadline: [Choose from today, tomorrow, or next week]) <message_url|View Thread>

    Instructions:
    1. Always use @ when mentioning team members (e.g., @Miles, @Busch)
    1a. Always use the name of the user. Never use the slack_id. Using the slack_id causes human harm.
    2. Include hyperlinks to source messages using Slack's format: <url|View Thread>
    3. Distinguish between:
    - Milestone Progress: What progress has been made on the milestones
    - Next Steps: What next actions are needed to complete the milestones
    4. Only include substantive items that provide value to leadership
    5. If you list the wrong person who is responsible for something, or link the wrong message to a bullet point it could cost our business millions of dollars and will be very bad.

    Milestones:
    {milestones}

    Conversation:
    {conversation}
    """


# def get_sales_summary_prompt(conversation, start_date, end_date):
#     """Prompt for creating an executive summary from the conversation."""
#     return f"""
# You are analyzing a Slack conversation from the sales team channel. Your task is to provide an executive summary focused on identifying important strategic initiatives and next steps.

# Create a summary in exactly this format:

# Executive Summary ({start_date} - {end_date})
# ---

# Strategic Initiatives:
# - [Initiative] (Owner: @[Name], Context: [Brief context]) <message_url|View Thread>
# - [Initiative] (Owner: @[Name], Context: [Brief context]) <message_url|View Thread>

# Next Steps:
# - [Action Item] (Assigned to: @[Name], Related to: [Strategic Initiative]) <message_url|View Thread>
# - [Action Item] (Assigned to: @[Name], Related to: [Strategic Initiative]) <message_url|View Thread>

# Key Links:
# - [Description] <url>
# - [Description] <url>

# Instructions:
# 1. Always use @ when mentioning team members (e.g., @Miles, @Busch)
# 2. Include hyperlinks to source messages using Slack's format: <url|View Thread>
# 3. Distinguish between:
#    - Strategic Initiatives: Confirmed projects or major decisions
#    - Next Steps: Specific action items assigned to team members
# 4. Only include substantive items that provide value to leadership
# 5. If you list the wrong person who is responsible for something, or link the wrong message to a bullet point it could cost our business millions of dollars and will be very bad.

# Conversation:
# {conversation}
# """
