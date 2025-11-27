#!/usr/bin/env python3
"""
GitHub Pull Request Client for PR Review Resolution

Provides utilities for fetching PR details, review comments, check statuses,
and resolving review comment threads via the GitHub API.

Dependencies:
    - requests: For GitHub API communication

Environment Variables:
    - GITHUB_TOKEN: Personal access token with repo scope
    - GITHUB_REPO: Repository in format "owner/repo" (optional if PR URL provided)
"""

import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class CheckStatus(Enum):
    """Enumeration of possible check run statuses."""
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    NEUTRAL = "neutral"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"


@dataclass
class ReviewComment:
    """
    Represents a GitHub PR review comment.

    Attributes:
        id: Unique comment ID
        node_id: GraphQL node ID (required for resolving threads)
        body: Comment text content
        path: File path the comment is attached to
        line: Line number in the file (new version)
        original_line: Original line number (old version)
        diff_hunk: The diff hunk context
        user: Username of commenter
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
        in_reply_to_id: ID of parent comment if this is a reply
        pull_request_review_id: ID of the review this comment belongs to
        is_resolved: Whether the thread is resolved
        thread_id: The thread node_id for resolution
    """
    id: int
    node_id: str
    body: str
    path: str
    line: Optional[int]
    original_line: Optional[int]
    diff_hunk: str
    user: str
    created_at: str
    updated_at: str
    in_reply_to_id: Optional[int] = None
    pull_request_review_id: Optional[int] = None
    is_resolved: bool = False
    thread_id: Optional[str] = None


@dataclass
class CheckRun:
    """
    Represents a GitHub check run.

    Attributes:
        id: Unique check run ID
        name: Name of the check
        status: Current status (queued, in_progress, completed)
        conclusion: Final conclusion if completed
        details_url: URL to check details
        output_title: Title from check output
        output_summary: Summary from check output
        started_at: Timestamp when check started
        completed_at: Timestamp when check completed
    """
    id: int
    name: str
    status: str
    conclusion: Optional[str]
    details_url: Optional[str]
    output_title: Optional[str]
    output_summary: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]


@dataclass
class PullRequest:
    """
    Represents a GitHub Pull Request.

    Attributes:
        number: PR number
        title: PR title
        body: PR description
        state: PR state (open, closed)
        head_sha: SHA of the head commit
        head_ref: Branch name of the head
        base_ref: Branch name of the base
        user: PR author username
        html_url: Web URL to the PR
        diff_url: URL to the diff
        mergeable: Whether PR can be merged
        comments: List of review comments
        checks: List of check runs
    """
    number: int
    title: str
    body: str
    state: str
    head_sha: str
    head_ref: str
    base_ref: str
    user: str
    html_url: str
    diff_url: str
    mergeable: Optional[bool] = None
    comments: List[ReviewComment] = field(default_factory=list)
    checks: List[CheckRun] = field(default_factory=list)


class GitHubPRClient:
    """
    Client for interacting with GitHub Pull Request API.

    Provides methods for fetching PR details, review comments,
    check statuses, and resolving review threads.
    """

    def __init__(self, token: Optional[str] = None, repo: Optional[str] = None):
        """
        Initialize GitHub PR client.

        Args:
            token: GitHub personal access token (falls back to GITHUB_TOKEN env var)
            repo: Repository in format "owner/repo" (falls back to GITHUB_REPO env var)

        Raises:
            ValueError: If token cannot be determined
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.repo = repo or os.environ.get("GITHUB_REPO")

        if not self.token:
            raise ValueError(
                "GitHub token not provided. Set GITHUB_TOKEN environment variable "
                "or pass token parameter."
            )

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.graphql_headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _get_base_url(self, repo: Optional[str] = None) -> str:
        """Get the base API URL for the repository."""
        target_repo = repo or self.repo
        if not target_repo:
            raise ValueError("Repository not specified")
        return f"https://api.github.com/repos/{target_repo}"

    def parse_pr_url(self, url: str) -> Tuple[str, int]:
        """
        Parse a GitHub PR URL to extract owner/repo and PR number.

        Args:
            url: GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)

        Returns:
            Tuple of (owner/repo, pr_number)

        Raises:
            ValueError: If URL format is invalid
        """
        pattern = r"github\.com/([^/]+/[^/]+)/pull/(\d+)"
        match = re.search(pattern, url)
        if not match:
            raise ValueError(f"Invalid GitHub PR URL: {url}")
        return match.group(1), int(match.group(2))

    def get_pull_request(
        self, pr_number: int, repo: Optional[str] = None
    ) -> PullRequest:
        """
        Fetch pull request details.

        Args:
            pr_number: Pull request number
            repo: Repository in format "owner/repo" (optional)

        Returns:
            PullRequest object with PR details

        Raises:
            requests.HTTPError: If the API request fails
        """
        import requests

        base_url = self._get_base_url(repo)
        url = f"{base_url}/pulls/{pr_number}"

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()

        return PullRequest(
            number=data["number"],
            title=data["title"],
            body=data["body"] or "",
            state=data["state"],
            head_sha=data["head"]["sha"],
            head_ref=data["head"]["ref"],
            base_ref=data["base"]["ref"],
            user=data["user"]["login"],
            html_url=data["html_url"],
            diff_url=data["diff_url"],
            mergeable=data.get("mergeable"),
        )

    def get_review_comments(
        self, pr_number: int, repo: Optional[str] = None
    ) -> List[ReviewComment]:
        """
        Fetch all review comments on a pull request.

        Args:
            pr_number: Pull request number
            repo: Repository in format "owner/repo" (optional)

        Returns:
            List of ReviewComment objects

        Raises:
            requests.HTTPError: If the API request fails
        """
        import requests

        base_url = self._get_base_url(repo)
        url = f"{base_url}/pulls/{pr_number}/comments"

        comments = []
        page = 1
        per_page = 100

        while True:
            response = requests.get(
                url,
                headers=self.headers,
                params={"page": page, "per_page": per_page}
            )
            response.raise_for_status()
            data = response.json()

            if not data:
                break

            for item in data:
                comment = ReviewComment(
                    id=item["id"],
                    node_id=item["node_id"],
                    body=item["body"],
                    path=item["path"],
                    line=item.get("line"),
                    original_line=item.get("original_line"),
                    diff_hunk=item["diff_hunk"],
                    user=item["user"]["login"],
                    created_at=item["created_at"],
                    updated_at=item["updated_at"],
                    in_reply_to_id=item.get("in_reply_to_id"),
                    pull_request_review_id=item.get("pull_request_review_id"),
                )
                comments.append(comment)

            page += 1

        return comments

    def get_review_threads(
        self, pr_number: int, repo: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch review threads with resolution status using GraphQL.

        Args:
            pr_number: Pull request number
            repo: Repository in format "owner/repo" (optional)

        Returns:
            List of thread dictionaries with comments and resolution status

        Raises:
            requests.HTTPError: If the API request fails
        """
        import requests

        target_repo = repo or self.repo
        if not target_repo:
            raise ValueError("Repository not specified")

        owner, repo_name = target_repo.split("/")

        query = """
        query($owner: String!, $repo: String!, $prNumber: Int!, $cursor: String) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $prNumber) {
              reviewThreads(first: 100, after: $cursor) {
                pageInfo {
                  hasNextPage
                  endCursor
                }
                nodes {
                  id
                  isResolved
                  isOutdated
                  path
                  line
                  comments(first: 100) {
                    nodes {
                      id
                      databaseId
                      body
                      author {
                        login
                      }
                      createdAt
                      path
                      line
                      diffHunk
                    }
                  }
                }
              }
            }
          }
        }
        """

        threads = []
        cursor = None

        while True:
            variables = {
                "owner": owner,
                "repo": repo_name,
                "prNumber": pr_number,
                "cursor": cursor,
            }

            response = requests.post(
                "https://api.github.com/graphql",
                headers=self.graphql_headers,
                json={"query": query, "variables": variables},
            )
            response.raise_for_status()
            result = response.json()

            if "errors" in result:
                raise RuntimeError(f"GraphQL errors: {result['errors']}")

            review_threads = result["data"]["repository"]["pullRequest"]["reviewThreads"]

            for thread in review_threads["nodes"]:
                thread_data = {
                    "thread_id": thread["id"],
                    "is_resolved": thread["isResolved"],
                    "is_outdated": thread["isOutdated"],
                    "path": thread["path"],
                    "line": thread["line"],
                    "comments": [],
                }

                for comment in thread["comments"]["nodes"]:
                    thread_data["comments"].append({
                        "id": comment["id"],
                        "database_id": comment["databaseId"],
                        "body": comment["body"],
                        "author": comment["author"]["login"] if comment["author"] else "ghost",
                        "created_at": comment["createdAt"],
                        "path": comment["path"],
                        "line": comment["line"],
                        "diff_hunk": comment["diffHunk"],
                    })

                threads.append(thread_data)

            page_info = review_threads["pageInfo"]
            if not page_info["hasNextPage"]:
                break
            cursor = page_info["endCursor"]

        return threads

    def resolve_thread(self, thread_id: str) -> bool:
        """
        Resolve a review thread by its GraphQL node ID.

        Args:
            thread_id: GraphQL node ID of the thread

        Returns:
            True if resolution was successful

        Raises:
            requests.HTTPError: If the API request fails
        """
        import requests

        mutation = """
        mutation($threadId: ID!) {
          resolveReviewThread(input: {threadId: $threadId}) {
            thread {
              id
              isResolved
            }
          }
        }
        """

        response = requests.post(
            "https://api.github.com/graphql",
            headers=self.graphql_headers,
            json={
                "query": mutation,
                "variables": {"threadId": thread_id}
            },
        )
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            raise RuntimeError(f"GraphQL errors: {result['errors']}")

        return result["data"]["resolveReviewThread"]["thread"]["isResolved"]

    def get_check_runs(
        self, ref: str, repo: Optional[str] = None
    ) -> List[CheckRun]:
        """
        Fetch check runs for a commit reference.

        Args:
            ref: Git reference (SHA, branch name, or tag)
            repo: Repository in format "owner/repo" (optional)

        Returns:
            List of CheckRun objects

        Raises:
            requests.HTTPError: If the API request fails
        """
        import requests

        base_url = self._get_base_url(repo)
        url = f"{base_url}/commits/{ref}/check-runs"

        check_runs = []
        page = 1
        per_page = 100

        while True:
            response = requests.get(
                url,
                headers=self.headers,
                params={"page": page, "per_page": per_page}
            )
            response.raise_for_status()
            data = response.json()

            for item in data.get("check_runs", []):
                check_run = CheckRun(
                    id=item["id"],
                    name=item["name"],
                    status=item["status"],
                    conclusion=item.get("conclusion"),
                    details_url=item.get("details_url"),
                    output_title=item.get("output", {}).get("title"),
                    output_summary=item.get("output", {}).get("summary"),
                    started_at=item.get("started_at"),
                    completed_at=item.get("completed_at"),
                )
                check_runs.append(check_run)

            if len(data.get("check_runs", [])) < per_page:
                break
            page += 1

        return check_runs

    def get_check_suites(
        self, ref: str, repo: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch check suites for a commit reference.

        Args:
            ref: Git reference (SHA, branch name, or tag)
            repo: Repository in format "owner/repo" (optional)

        Returns:
            List of check suite dictionaries

        Raises:
            requests.HTTPError: If the API request fails
        """
        import requests

        base_url = self._get_base_url(repo)
        url = f"{base_url}/commits/{ref}/check-suites"

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get("check_suites", [])

    def get_combined_status(
        self, ref: str, repo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch combined commit status for a reference.

        Args:
            ref: Git reference (SHA, branch name, or tag)
            repo: Repository in format "owner/repo" (optional)

        Returns:
            Dictionary with combined status info

        Raises:
            requests.HTTPError: If the API request fails
        """
        import requests

        base_url = self._get_base_url(repo)
        url = f"{base_url}/commits/{ref}/status"

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_workflow_runs(
        self, branch: Optional[str] = None, repo: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent workflow runs.

        Args:
            branch: Branch name to filter by (optional)
            repo: Repository in format "owner/repo" (optional)

        Returns:
            List of workflow run dictionaries

        Raises:
            requests.HTTPError: If the API request fails
        """
        import requests

        base_url = self._get_base_url(repo)
        url = f"{base_url}/actions/runs"

        params = {"per_page": 30}
        if branch:
            params["branch"] = branch

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json().get("workflow_runs", [])

    def get_workflow_run_logs_url(
        self, run_id: int, repo: Optional[str] = None
    ) -> str:
        """
        Get the download URL for workflow run logs.

        Args:
            run_id: Workflow run ID
            repo: Repository in format "owner/repo" (optional)

        Returns:
            URL to download logs

        Raises:
            requests.HTTPError: If the API request fails
        """
        import requests

        base_url = self._get_base_url(repo)
        url = f"{base_url}/actions/runs/{run_id}/logs"

        response = requests.get(
            url,
            headers=self.headers,
            allow_redirects=False
        )

        if response.status_code == 302:
            return response.headers.get("Location", "")

        response.raise_for_status()
        return ""

    def get_file_content(
        self, path: str, ref: str, repo: Optional[str] = None
    ) -> str:
        """
        Fetch file content from repository.

        Args:
            path: File path in repository
            ref: Git reference (SHA, branch name)
            repo: Repository in format "owner/repo" (optional)

        Returns:
            File content as string

        Raises:
            requests.HTTPError: If the API request fails
        """
        import base64
        import requests

        base_url = self._get_base_url(repo)
        url = f"{base_url}/contents/{path}"

        response = requests.get(
            url,
            headers=self.headers,
            params={"ref": ref}
        )
        response.raise_for_status()
        data = response.json()

        if data.get("encoding") == "base64":
            return base64.b64decode(data["content"]).decode("utf-8")
        return data.get("content", "")

    def add_comment_reply(
        self, pr_number: int, comment_id: int, body: str, repo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a reply to a review comment.

        Args:
            pr_number: Pull request number
            comment_id: ID of the comment to reply to
            body: Reply text
            repo: Repository in format "owner/repo" (optional)

        Returns:
            Created comment data

        Raises:
            requests.HTTPError: If the API request fails
        """
        import requests

        base_url = self._get_base_url(repo)
        url = f"{base_url}/pulls/{pr_number}/comments/{comment_id}/replies"

        response = requests.post(
            url,
            headers=self.headers,
            json={"body": body}
        )
        response.raise_for_status()
        return response.json()


def get_full_pr_context(
    pr_url_or_number: str,
    token: Optional[str] = None,
    repo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch comprehensive PR context including details, threads, and checks.

    Args:
        pr_url_or_number: Either a full GitHub PR URL or a PR number (as string)
        token: GitHub token (optional, uses env var if not provided)
        repo: Repository name (optional, uses env var if not provided)

    Returns:
        Dictionary containing:
            - pr: PullRequest object
            - threads: List of review threads with resolution status
            - checks: List of check runs
            - failing_checks: List of failing check runs
            - unresolved_threads: List of unresolved threads

    Example:
        >>> context = get_full_pr_context("https://github.com/owner/repo/pull/123")
        >>> print(f"PR #{context['pr'].number}: {context['pr'].title}")
        >>> print(f"Unresolved threads: {len(context['unresolved_threads'])}")
        >>> print(f"Failing checks: {len(context['failing_checks'])}")
    """
    client = GitHubPRClient(token=token, repo=repo)

    # Parse URL or use number directly
    if pr_url_or_number.startswith("http"):
        target_repo, pr_number = client.parse_pr_url(pr_url_or_number)
    else:
        pr_number = int(pr_url_or_number)
        target_repo = repo

    # Fetch PR details
    pr = client.get_pull_request(pr_number, repo=target_repo)

    # Fetch review threads
    threads = client.get_review_threads(pr_number, repo=target_repo)

    # Fetch check runs
    checks = client.get_check_runs(pr.head_sha, repo=target_repo)

    # Filter unresolved threads
    unresolved_threads = [t for t in threads if not t["is_resolved"]]

    # Filter failing checks
    failing_checks = [
        c for c in checks
        if c.conclusion in ("failure", "cancelled", "timed_out", "action_required")
    ]

    return {
        "pr": pr,
        "threads": threads,
        "checks": checks,
        "failing_checks": failing_checks,
        "unresolved_threads": unresolved_threads,
        "client": client,
        "repo": target_repo,
    }


if __name__ == "__main__":
    print("GitHub PR Client for Review Resolution")
    print("=" * 60)
    print()
    print("This script is meant to be imported and used by Claude.")
    print()
    print("Example:")
    print("  from scripts.github_pr_client import get_full_pr_context")
    print('  context = get_full_pr_context("https://github.com/owner/repo/pull/123")')
    print("  print(f'Unresolved: {len(context[\"unresolved_threads\"])}')")
