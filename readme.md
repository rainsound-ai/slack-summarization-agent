# Slack Summarization Agent

The Slack Summarization Agent is a tool designed to fetch, process, and summarize conversations from Slack channels. It provides concise summaries of discussions, highlighting main topics, key decisions, action items, and more.

## Features

- **Fetch Conversations**: Automatically retrieves messages from specified Slack channels.
- **Summarize Discussions**: Uses OpenAI's API to generate concise summaries of conversations.
- **Ignore Non-Substantive Content**: Filters out non-substantive summaries to focus on meaningful content.
- **Customizable**: Easily configure which channels to include or ignore.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/slack-summarization-agent.git
   cd slack-summarization-agent
   ```

2. **Install Dependencies**:
   Ensure you have Python installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**:
   Create a `.env` file in the root directory and add your Slack and OpenAI API keys:
   ```
   SLACK_BOT_TOKEN=your-slack-bot-token
   OPENAI_API_KEY=your-openai-api-key
   ```

## Usage

1. **Run the Application**:
   ```bash
   python main.py
   ```

2. **Configuration**:
   - **Ignored Channels**: Modify the `IGNORED_CHANNELS` set in `config.py` to specify which channels to ignore.
   - **Substantive Summary Filtering**: Adjust the `non_substantive_phrases` in `main.py` to refine what constitutes a substantive summary.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.

## Troubleshooting

- **Permission Errors**: Ensure your Slack bot has the necessary permissions. Check the "OAuth & Permissions" section in your Slack app settings.
- **API Errors**: Verify that your API keys are correct and have the necessary scopes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

# Ngrok 
Run `ngrok http --url=whole-mastodon-top.ngrok-free.app 5000`

# New Stuff
Run `python main.py` to suggest new sub projects from slack and send them to notion marked as "Potential".
Run the webhook server and click the notion button to:
   ✅ Mark the sub project that's clicked as "Done"
   ✅ Mark the suggested subproject as "In progress"
   [] send a dm about the next step
   [] send a calendar invite