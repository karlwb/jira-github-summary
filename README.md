# Jira & GitHub Summary Tools

A collection of Python scripts to fetch and format data from Jira and GitHub for creating summaries and reports. These tools help generate formatted output of completed Jira tickets and merged GitHub Pull Requests for a given year.

## Features

- **`jira.py`**: Fetches completed Jira tickets for the current year with acceptance criteria
- **`github.py`**: Fetches merged GitHub Pull Requests for the current year
- Both scripts output formatted data suitable for LLM prompts or reporting

## Prerequisites

- Python 3.11 or higher
- Poetry (for dependency management)
- Jira account with API access
- GitHub account with Personal Access Token

## Installation

1. **Clone or navigate to the project directory**

2. **Install Poetry** (if not already installed):

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Initialize the Poetry environment and install dependencies**:

   ```bash
   poetry install
   ```

## Configuration

1. **Copy the environment template**:

   ```bash
   cp .env.example .env
   ```

2. **Fill out the `.env` file with your credentials**:

   ### Jira Configuration

   - `JIRA_URL`: Your Jira instance URL (e.g., `https://yourcompany.atlassian.net`)
   - `JIRA_EMAIL`: Your Jira email address
   - `JIRA_API_TOKEN`: Your Jira API token (create one in your Atlassian account settings)
   - `JIRA_ASSIGNEE_ACCOUNT_ID`: Your Jira account ID (get from `https://yourcompany.atlassian.net/rest/api/3/myself`)
   - `JIRA_AC_FIELD_ID`: Custom field ID for acceptance criteria (find by inspecting a ticket with acceptance criteria at `https://yourcompany.atlassian.net/rest/api/3/issue/TICKET-ID`)

   ### GitHub Configuration

   - `GITHUB_TOKEN`: Your GitHub Personal Access Token (create one in GitHub Settings > Developer settings > Personal access tokens)
   - `GITHUB_USERNAME`: Your GitHub username

## Usage

### Running the Jira Script

```bash
poetry run python jira.py
```

This will:

- Fetch all completed Jira tickets assigned to you for the current year
- Output formatted ticket information including titles, descriptions, and acceptance criteria
- Save the output to a file named `jira_tickets_YYYY-MM-DD.txt`

### Running the GitHub Script

```bash
poetry run python github.py
```

This will:

- Fetch all merged Pull Requests you created for the current year
- Output formatted PR information including titles, descriptions, and URLs
- Save the output to a file named `github_contributions_YYYY-MM-DD.txt`

### Running Both Scripts

You can run both scripts in sequence to generate comprehensive summaries:

```bash
poetry run python jira.py
poetry run python github.py
```

## Output Files

Both scripts generate timestamped output files in the project directory:

- `jira_tickets_YYYY-MM-DD.txt`: Contains formatted Jira ticket summaries
- `github_contributions_YYYY-MM-DD.txt`: Contains formatted GitHub PR summaries
- `prompt-YYYY-MM-DD.txt`: Combined output suitable for LLM prompts (if generated)

## Troubleshooting

### Common Issues

1. **Environment variables not found**: Ensure your `.env` file is properly configured with all required values

2. **Jira API authentication errors**:
   - Verify your API token is correct and hasn't expired
   - Check that your email address matches your Jira account

3. **GitHub API rate limiting**:
   - Ensure your Personal Access Token has appropriate permissions
   - The scripts respect GitHub's rate limits automatically

4. **Python version errors**: Ensure you're using Python 3.11 or higher

### Getting Help

- Check that all environment variables in `.env` match the format shown in `.env.example`
- Verify your API tokens and credentials are valid
- Ensure you have the necessary permissions to access the Jira projects and GitHub repositories

## Development

To work on these scripts:

1. **Activate the Poetry shell**:

   ```bash
   poetry shell
   ```

2. **Run scripts directly**:

   ```bash
   python jira.py
   python github.py
   ```

3. **Add new dependencies**:

   ```bash
   poetry add package-name
   ```
