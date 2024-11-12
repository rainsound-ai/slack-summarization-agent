def get_gold_standard_prompt(channel_name, conversation):
    return """
📅 *Weekly Slack Summary (11/05 - 11/12)*

---

### 🔹 *Executive Summary:*
- **Team Expansion:** Onboarded Ben Ortega as the new Account Executive.
- **Event Planning:** Approved a $10K budget for three team members to attend AWS re:Invent in Las Vegas.
- **Financial Adjustments:** Addressed delayed payments and allocated funds for upcoming salaries.
- **Process Enhancements:** Optimized workflows and updated dashboards for better data tracking.
- **Technical Updates:** Addressed CUDA support issues on new M4 chips and advanced Docker configurations.

---

### 📌 **CHANNEL: #rainsound-ai**
- **Process Optimization:**
  - Implemented a 5-step approach to streamline workflows.
  - [Design a New Process](https://www.notion.so/rainsound-ai/Design-A-New-Process-4b49caf08fd7479c8841458ab47947f8?pvs=4)
- **Team Onboarding:**
  - Ben added to Slack, Google Workspace, Notion, and 1Password.
  - Completed NDA via [Common Paper](https://commonpaper.com/).
- **Metrics & Dashboards:**
  - Reminders sent to log major accomplishments and R&D hours.
  - Dashboard changes: Integrated "Processes I'm Supplier On" into Stakeholder roles; only Goalkeepers can mark processes as completed.

---

### 📌 **CHANNEL: #sales**
- **Re:Invent Planning:**
  - Approved $9,250 budget for event tickets, hotel, airfare, and meals for three attendees.
  - **Action Items:**
    - **Submit Purchase Proposal Form.**
    - **Finalize travel arrangements.**
  - [Detailed Breakdown](https://www.expedia.com/Las-Vegas-Hotels-Ellis-Island-Hotel.h18443.Hotel-Information)
- **Microsoft Project:**
  - Project nearing completion with positive renewal prospects.
  - **Action Item:** *Upload Microsoft case study post-demo.*
- **AlixPartners Case Study:**
  - First iteration completed: [View Study](https://www.notion.so/rainsound-ai/Building-A-Keystone-Product-For-A-Global-Consulting-Leader-af77b8e68933461bbaf8e97c978bd9c2?pvs=4)
  - **Action Item:** *Incorporate feedback into the final case study.*
- **Enterprise Client Strategies:**
  - Developing strategies to mitigate culture mismatches.
  - **Action Item:** *Integrate solutions into the onboarding process design.*

---

### 📌 **CHANNEL: #finance**
- **New Hire:**
  - Ben Ortega onboarded with a compensation of $10K/month plus 10% commission.
  - [Contract Details](https://www.notion.so/rainsound-ai/rainsound-ai-Ben-Ortega-Contractor-Agreement-6825833c45f14e76a7392dae202052ae?pvs=4)
- **Payment Adjustments:**
  - Allocated $7,500 for Brent’s December payment.
  - Implemented monthly fund reservation to prevent future delays.
  - Prorated November payment for Ben at $4,761.90.
- **Operational Improvements:**
  - Transitioned to weekly screenshot submissions for time logging.
  - [Example Screenshot](https://files.slack.com/files-pri/T067TJ1EE15-F07VC9NMHJB/screenshot_2024-11-11_at_10.09.02__am.png)

---

### 📌 **CHANNEL: #projects**
- **Automation Enhancements:**
  - Deployed scripts on Render for phone call tracking. [GitHub Repo](https://github.com/rainsound-ai/trigger-jumpshare-on-huddle)
- **Website Case Studies:**
  - Prioritized adding case studies; using text-only images due to NDA.
  - **Action Items:**
    - **Deploy cron job scripts for recording processing.**
    - **Prioritize website case studies before deployment.**
- **OpenAI Credits:**
  - Nearly exhausted; urgent action needed to prevent disruption.
- **Revenue Analysis:**
  - Estimated Deedi project contribution to AlixPartners ~$7M.

---

### 📌 **CHANNEL: #shitposts**
- **Real Estate Tool Development:**
  - Developing a scoring system to assist realtors and enhance house search efficiency.
  - **Action Item:** *Collaborate with a realtor willing to adopt the scoring system.*
  - [Watch Project Overview](https://www.loom.com/share/6648d63066c547fbba87a1da6f4cf2bf)
- **Claude Artifacts Integration:**
  - Exploring the use of Claude Artifacts to build a mini-app for Zillow link processing.
  - Decision to focus on core Rainsound projects over side initiatives during this business phase.
  - [Simon Willison on Claude Artifacts](https://simonwillison.net/2024/Oct/21/claude-artifacts/)
  - [Anthropic Support Article](https://support.anthropic.com/en/articles/9487310-what-are-artifacts-and-how-do-i-use-them)
- **Decentralization Discussion:**
  - Debated pros and cons of decentralized systems vs. centralized social media.
  - Highlighted issue: Centralized platforms causing more problems than decentralized alternatives.
- **Multimedia Sharing:**
  - Shared screenshots and TikTok links related to AI and game development concepts.

---

### 📌 **CHANNEL: #processes**
- **Process Forms Development:**
  - Finalized roles for managing process forms with Aubrey.
  - **Action Item:** *Translate ongoing work into the new process proposal form.*
  - [Process Design Form](https://www.notion.so/rainsound-ai/Process-Design-Form-71d97fb7ab264cf38a736aebb24bd8a8?pvs=4)
- **CAC & Delivery Cost Tracking:**
  - Metrics system supports CAC and delivery cost tracking; data collection methods discussed.
  - **Action Item:** *Document hours spent on delivery and sales in the system.*
- **Naming Conventions:**
  - Debated names for new process forms (e.g., Process Template, Process Guide).
  - **Action Item:** *Finalize intuitive and descriptive names for forms to ensure clarity.*

---

### 📌 **CHANNEL: #brent-and-jeffrey**
- **Contracts and Agreements:**
  - Signed NDA and contracts with Ben and Rainsound.
  - **Action Item:** *Miles and Luca to review and sign Ben's contract by Monday.*
- **Team Acknowledgments:**
  - Praised team for exceptional project performance.
  - **New Member:** @Slack Summarization Agent joined the channel.

---

### 📌 **CHANNEL: #microsoft-stage-one**
- **Deployment Launch:**
  - Work is now live for 10% of Microsoft Learn users.
  - [View Deployment Details](https://learn.microsoft.com/en-us/training/?at_preview_token=4FhxMZZq5RXQNNpOOuFqCPd2laRtWeazQ4xu5baytBM&at_preview_index=1_2&at_preview_listed_activities_only=true)
- **New Member:** @Slack Summarization Agent joined the channel.

---

### 📌 **CHANNEL: #keye**
- **New Member:** @Slack Summarization Agent joined the channel.

---

### 🔗 *Key Links:*
- [CommonPaper](https://commonpaper.com/)
- [Design a New Process – Notion](https://www.notion.so/rainsound-ai/Design-A-New-Process-4b49caf08fd7479c8841458ab47947f8?pvs=4)
- [Purchase Proposal Form](https://www.notion.so/rainsound-ai/Purchase-Proposal-Form-301dd1246e004810b6e3e577c89393b3?pvs=4)
- [AlixPartners Case Study Draft](https://www.notion.so/rainsound-ai/Building-A-Keystone-Product-For-A-Global-Consulting-Leader-af77b8e68933461bbaf8e97c978bd9c2?pvs=4)
- [Automated Link Summary Agent Repository](https://github.com/rainsound-ai/automated-link-summary-agent)
- [Trigger Jumpshare on Huddle GitHub Repo](https://github.com/rainsound-ai/trigger-jumpshare-on-huddle)
- [Simon Willison on Claude Artifacts](https://simonwillison.net/2024/Oct/21/claude-artifacts/)
- [Anthropic Support Article](https://support.anthropic.com/en/articles/9487310-what-are-artifacts-and-how-do-i-use-them)
- [Process Design Form](https://www.notion.so/rainsound-ai/Process-Design-Form-71d97fb7ab264cf38a736aebb24bd8a8?pvs=4)
- [Tribe Payment Details](https://rainsound-ai.slack.com/archives/C06DN942V53/p1730499098777779)

---

✅ *Please address the highlighted action items promptly to maintain project momentum.*
    """
