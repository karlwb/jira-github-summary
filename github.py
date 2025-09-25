#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetches a user's merged GitHub Pull Requests for the year and formats
them for an LLM prompt.
"""
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """A dataclass to hold and validate config from environment variables."""
    github_token: str
    github_username: str

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from .env file and validate its presence."""
        load_dotenv()
        required_vars = {
            "github_token": os.getenv("GITHUB_TOKEN"),
            "github_username": os.getenv("GITHUB_USERNAME"),
        }

        missing = [key for key, value in required_vars.items() if not value]
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")
        return cls(**{k: v for k, v in required_vars.items() if v is not None})


class GitHubService:
    """A service class to interact with the GitHub API."""
    BASE_URL = "https://api.github.com"

    def __init__(self, config: Config):
        """Initialize the GitHub Service."""
        self.config = config
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {self.config.github_token}",
        }

    def fetch_merged_prs_for_year(self) -> List[Dict[str, Any]]:
        """Fetch all pages of merged Pull Requests for the current year."""
        current_year = datetime.now().year
        query = (
            f"is:pr author:{self.config.github_username} is:merged "
            f"merged:{current_year}-01-01..{current_year}-12-31"
        )
        search_url = f"{self.BASE_URL}/search/issues"
        all_prs: List[Dict[str, Any]] = []
        page = 1
        per_page = 100  # Max is 100

        print("Fetching your merged GitHub pull requests for the year...", file=sys.stderr)
        with httpx.Client(headers=self.headers, timeout=30.0) as client:
            while True:
                params = {"q": query, "per_page": per_page, "page": page}
                try:
                    response = client.get(search_url, params=params)
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
                    raise
                except httpx.RequestError as e:
                    print(f"API Request Failed: {e}")
                    raise

                data = response.json()
                prs_on_page = data.get("items", [])
                if not prs_on_page:
                    break  # No more results

                all_prs.extend(prs_on_page)
                total_count = data.get("total_count", 0)
                print(f"\rFetched {len(all_prs)} of {total_count} PRs...", end="", file=sys.stderr)

                # GitHub Search API caps results at 1000, so we stop if we have them all
                if len(all_prs) >= total_count:
                    break
                page += 1

        print("\nAll PRs fetched. Now formatting...", file=sys.stderr)
        return all_prs


def format_prs_for_llm(prs: List[Dict[str, Any]]) -> str:
    """Format the fetched GitHub PRs into a single string for the LLM."""
    if not prs:
        print("No merged PRs found for the year.")
        return ""

    consolidated_data = []
    for pr in sorted(prs, key=lambda x: x["closed_at"], reverse=True):
        # if it 's not for a centurylink (case-insensitive) repo, skip it
        repo_name = pr["repository_url"].split("/")[-2] + "/" + pr["repository_url"].split("/")[-1]
        if "centurylink" not in repo_name.lower():
            continue
        i=1
        entry = [
            f"--- github {i} ---",
            f"Repo: {repo_name}",
            f"PR #{pr['number']}: {pr['title']}",
            f"Merged On: {pr['closed_at'][:10]}",
            f"URL: {pr['html_url']}\n",
            "Description:",
            pr["body"] or "No description provided.",
        ]
        i += 1
        consolidated_data.append("\n".join(entry))

    return "\n\n".join(consolidated_data)


def main() -> int:
    """Run the main script logic."""
    try:
        # NOTE: Your .env file should now have GITHUB_TOKEN and GITHUB_USERNAME
        config = Config.from_env()
        github_service = GitHubService(config)

        all_prs = github_service.fetch_merged_prs_for_year()
        github_output = format_prs_for_llm(all_prs)

        if github_output:
            current_date = datetime.now().strftime('%Y-%m-%d')
            filename = f"github_contributions_{current_date}.txt"

            with open(filename, "w", encoding="utf-8") as f:
                f.write(github_output)

            print(f"\nSuccessfully wrote contribution data to '{filename}'", file=sys.stderr)
        return 0
    except (ValueError, httpx.RequestError) as e:
        print(f"\nAn error occurred: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())