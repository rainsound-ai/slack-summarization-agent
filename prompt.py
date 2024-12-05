import logging

logger = logging.getLogger(__name__)


def link_next_steps_to_notion_steps_prompt(
    channel_summary: str, notion_steps: str
) -> str:
    """Linking the next steps to the notion steps."""
    return f"""
    For each of the next steps in the channel summary, find the corresponding notion step and link them together.
    Your response should be in the following format:
    Next Steps:
    - [Action Item] (Assigned to: @[Name], Related to: [Strategic Initiative]) <message_url|View Thread> <notion_step_url|[notion step name]>
    - [Action Item] (Assigned to: @[Name], Related to: [Strategic Initiative]) <message_url|View Thread> <notion_step_url|[notion step name]>

    Channel Summary:
    {channel_summary}

Notion Steps:
{notion_steps}
"""


def get_sales_summary_prompt(conversation, start_date, end_date):
    """Prompt for creating an executive summary from the conversation."""
    return f"""
You are analyzing a Slack conversation from the sales team channel. Your task is to provide an executive summary focused on identifying important strategic initiatives, next steps, and brainstormed ideas.

Create a summary in exactly this format:

Executive Summary ({start_date} - {end_date})
---

Strategic Initiatives:
- [Initiative] (Owner: @[Name], Context: [Brief context]) <message_url|View Thread>
- [Initiative] (Owner: @[Name], Context: [Brief context]) <message_url|View Thread>

Next Steps:
- [Action Item] (Assigned to: @[Name], Related to: [Strategic Initiative]) <message_url|View Thread>
- [Action Item] (Assigned to: @[Name], Related to: [Strategic Initiative]) <message_url|View Thread>

Brainstorm Ideas:
- [Idea] (Proposed by: @[Name], Context: [Brief context]) <message_url|View Thread>
- [Idea] (Proposed by: @[Name], Context: [Brief context]) <message_url|View Thread>

Key Links:
- [Description] <url>
- [Description] <url>

Instructions:
1. Always use @ when mentioning team members (e.g., @Miles, @Busch)
2. Include hyperlinks to source messages using Slack's format: <url|View Thread>
3. Distinguish between:
   - Strategic Initiatives: Confirmed projects or major decisions
   - Next Steps: Specific action items assigned to team members
   - Brainstorm Ideas: Proposed concepts not yet actioned
4. Only include substantive items that provide value to leadership
5. If you list the wrong person who is repsonsible for something, or link the wrong message to a bullet point it could cost our business millions if dollars and will be very bad.

Conversation:
{conversation}
"""
