#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetches completed Jira tickets for the year and formats them for an LLM prompt.
"""
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
from datetime import datetime
from dotenv import load_dotenv



@dataclass(frozen=True)
class Config:
    """A dataclass to hold and validate config from environment variables."""

    jira_url: str
    jira_email: str
    jira_api_token: str
    ac_field_id: str
    assignee_account_id: str

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from .env file and validate its presence."""
        load_dotenv()
        required_vars = {
            "jira_url": os.getenv("JIRA_URL"),
            "jira_email": os.getenv("JIRA_EMAIL"),
            "jira_api_token": os.getenv("JIRA_API_TOKEN"),
            "ac_field_id": os.getenv("JIRA_AC_FIELD_ID"),
            "assignee_account_id": os.getenv("JIRA_ASSIGNEE_ACCOUNT_ID"),
        }

        missing = [key for key, value in required_vars.items() if not value]
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")

        # Ensure mypy knows that no values are None at this point
        return cls(**{k: v for k, v in required_vars.items() if v is not None})


class JiraService:
    """A service class to interact with the Jira API."""

    def __init__(self, config: Config):
        """Initialize the Jira Service."""
        self.config = config
        self.search_url = f"{config.jira_url}/rest/api/3/search/jql"
        self.auth = (config.jira_email, config.jira_api_token)
        self.jql_query = (
            f"assignee = '{config.assignee_account_id}' "
            "AND status in (Done, Closed, Resolved) "
            "AND resolutiondate >= startOfYear() ORDER BY created DESC"
        )

    def fetch_all_issues(self) -> List[Dict[str, Any]]:
        """
        Fetch all pages of issue data using token-based pagination.
        """
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        fields_to_request = [
            "key", "summary", "comment", "description", self.config.ac_field_id
        ]

        all_issues: List[Dict[str, Any]] = []
        next_page_token: Optional[str] = None
        max_results = 100

        print(f"Fetching completed Jira tickets for the year for {self.config.jira_email}...", file=sys.stderr)
        print("Using query:", self.jql_query, file=sys.stderr)
        with httpx.Client(auth=self.auth, headers=headers, timeout=30.0) as client:
            while True:
                payload: Dict[str, Any] = {
                    "jql": self.jql_query,
                    "fields": fields_to_request,
                    "maxResults": max_results,
                }
                if next_page_token:
                    payload["nextPageToken"] = next_page_token

                try:
                    response = client.post(self.search_url, json=payload)
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
                    raise
                except httpx.RequestError as e:
                    print(f"API Request Failed: {e}")
                    raise

                data = response.json()
                issues_on_page = data.get("issues", [])
                all_issues.extend(issues_on_page)

                print(f"\rFetched {len(all_issues)} tickets...", end="", file=sys.stderr)

                next_page_token = data.get("nextPageToken")
                if not next_page_token:
                    break  # No more pages

        print("\nAll tickets fetched. Now formatting for the LLM...", file=sys.stderr)
        return all_issues


def get_adf_text(adf_node: Optional[Dict[str, Any]]) -> str:
    """Recursively extract plain text from Atlassian Document Format (ADF)."""
    if not isinstance(adf_node, dict):
        return ""

    text_parts = []
    if adf_node.get("type") == "text" and "text" in adf_node:
        return adf_node.get("text", "")

    if "content" in adf_node and isinstance(adf_node["content"], list):
        for content_node in adf_node["content"]:
            text_parts.append(get_adf_text(content_node))

    return "".join(text_parts)


def format_issues_for_llm(issues: List[Dict[str, Any]], ac_field_id: str) -> str:
    """Format the fetched Jira issues into a single string for the LLM."""
    if not issues:
        print("No issues found. Check your JQL query or permissions.")
        return ""

    consolidated_data = []
    i = 1
    for issue in issues:
        fields = issue.get("fields", {})
        key = issue.get("key", "N/A")
        title = fields.get("summary", "N/A")

        description = get_adf_text(fields.get("description")) or "No description."

        ac_value = fields.get(ac_field_id)
        ac = get_adf_text(ac_value) if isinstance(ac_value, dict) else (ac_value or "N/A")

        entry = [
            f"--- jira {i} ---",
            f"Ticket: {key}",
            f"Title: {title}",
            f"Description:\n{description}\n",
            f"Acceptance Criteria:\n{ac}\n",
            "Comments:",
        ]
        i += 1
        comments = fields.get("comment", {}).get("comments", [])
        if comments:
            for comment in comments:
                author = comment.get("author", {}).get("displayName", "Unknown")
                body = get_adf_text(comment.get("body"))
                entry.append(f"- {author}: {body}")
        else:
            entry.append("- No comments found.")

        consolidated_data.append("\n".join(entry))

    return "\n\n".join(consolidated_data)


def main() -> int:
    """Run the main script logic."""
    try:
        config = Config.from_env()
        jira_service = JiraService(config)

        all_issues = jira_service.fetch_all_issues()
        jira_output = format_issues_for_llm(all_issues, config.ac_field_id)

        if jira_output:
            current_date = datetime.now().strftime('%Y-%m-%d')
            filename = f"jira_tickets_{current_date}.txt"

            with open(filename, "w", encoding="utf-8") as f:
                f.write(jira_output)
                print(f"\nSuccessfully wrote ticket data to '{filename}'", file=sys.stderr)

        return 0
    except (ValueError, httpx.RequestError) as e:
        print(f"\nAn error occurred: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())