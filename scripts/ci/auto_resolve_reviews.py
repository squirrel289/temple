#!/usr/bin/env python3
"""Auto-resolve PR review threads that are covered by a commit and tests.

Conservative policy implemented:
- Only attempt to resolve threads for which the PR head's required checks are green.
- Require either: (A) a tests/ file was added/modified in the PR, or
  (B) an explicit marker `FixesReviewThread: <thread-id>` appears in the PR body or commit messages.

This script is intended to be run from a GitHub Action. It uses the
`GITHUB_PR_AUTORESOLVE_TOKEN` secret for GraphQL requests.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple

import requests

GITHUB_API = "https://api.github.com"
GITHUB_GRAPHQL = "https://api.github.com/graphql"


def _repo_owner_name(repo: str) -> Tuple[str, str]:
    owner, name = repo.split("/", 1)
    return owner, name


def _get_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def combined_status(repo: str, sha: str, token: str) -> str:
    owner, name = _repo_owner_name(repo)
    url = f"{GITHUB_API}/repos/{owner}/{name}/commits/{sha}/status"
    r = requests.get(url, headers=_get_headers(token))
    r.raise_for_status()
    return r.json().get("state", "")


def pr_files(repo: str, pr: int, token: str) -> List[str]:
    owner, name = _repo_owner_name(repo)
    url = f"{GITHUB_API}/repos/{owner}/{name}/pulls/{pr}/files"
    files: List[str] = []
    page = 1
    while True:
        r = requests.get(
            url, headers=_get_headers(token), params={"page": page, "per_page": 100}
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        files.extend([f["filename"] for f in data])
        page += 1
    return files


def pr_body_and_commits(repo: str, pr: int, token: str) -> Tuple[str, List[str]]:
    owner, name = _repo_owner_name(repo)
    r = requests.get(
        f"{GITHUB_API}/repos/{owner}/{name}/pulls/{pr}", headers=_get_headers(token)
    )
    r.raise_for_status()
    pr_body = r.json().get("body") or ""

    # commits
    commits: List[str] = []
    page = 1
    while True:
        r = requests.get(
            f"{GITHUB_API}/repos/{owner}/{name}/pulls/{pr}/commits",
            headers=_get_headers(token),
            params={"page": page, "per_page": 100},
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        commits.extend([c.get("commit", {}).get("message", "") for c in data])
        page += 1
    return pr_body, commits


def graphql_query(
    repo: str, query: str, variables: Dict[str, Any], token: str
) -> Dict[str, Any]:
    headers = {
        "Authorization": f"bearer {token}",
        "Accept": "application/vnd.github.shadow-cat-preview+json",
    }
    r = requests.post(
        GITHUB_GRAPHQL, json={"query": query, "variables": variables}, headers=headers
    )
    r.raise_for_status()
    result = r.json()
    if "errors" in result:
        raise RuntimeError(json.dumps(result["errors"]))
    return result["data"]


def list_review_threads(repo: str, pr: int, token: str) -> List[Dict[str, Any]]:
    owner, name = _repo_owner_name(repo)
    query = """
    query($owner:String!, $name:String!, $number:Int!) {
      repository(owner:$owner, name:$name) {
        pullRequest(number:$number) {
          reviewThreads(first: 200) {
            nodes {
              id
              isResolved
              isOutdated
              path
              start { line }
            }
          }
        }
      }
    }
    """
    vars: Dict[str, str | int] = {"owner": owner, "name": name, "number": pr}
    data = graphql_query(repo, query, vars, token)
    nodes = data["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    return nodes


def mark_thread_resolved(repo: str, thread_id: str, token: str) -> None:
    query = """
    mutation($threadId: ID!) {
      markPullRequestReviewThreadResolved(input: {threadId: $threadId}) {
        clientMutationId
      }
    }
    """
    graphql_query(repo, query, {"threadId": thread_id}, token)


def post_pr_comment(repo: str, pr: int, body: str, token: str) -> None:
    owner, name = _repo_owner_name(repo)
    url = f"{GITHUB_API}/repos/{owner}/{name}/issues/{pr}/comments"
    r = requests.post(url, headers=_get_headers(token), json={"body": body})
    r.raise_for_status()


def git_fetch_base(base_ref: str) -> None:
    # Fetch base ref so diffs against it work locally
    subprocess.run(["git", "fetch", "origin", f"{base_ref}:{base_ref}"], check=False)


def parse_unified_diff_hunks(diff_text: str) -> Dict[str, List[Tuple[int, int]]]:
    # Returns mapping file -> list of (start_line, end_line) for new-file ranges (+c,d)
    result: Dict[str, List[Tuple[int, int]]] = {}
    cur_file: Optional[str] = None
    for line in diff_text.splitlines():
        if line.startswith("+++"):
            # +++ b/path or +++ /dev/null
            parts = line.split()
            if len(parts) >= 2:
                path = parts[1]
                if path.startswith("b/"):
                    cur_file = path[2:]
                else:
                    cur_file = path
                result.setdefault(cur_file, [])
        elif line.startswith("@@"):
            # @@ -a,b +c,d @@
            m = re.search(r"\+([0-9]+)(?:,([0-9]+))?", line)
            if m and cur_file is not None:
                start = int(m.group(1))
                length = int(m.group(2)) if m.group(2) else 1
                result[cur_file].append((start, start + max(length, 1) - 1))
    return result


def main() -> int:
    repo = os.environ.get("REPOSITORY") or os.environ.get("GITHUB_REPOSITORY")
    pr = int(os.environ.get("PR_NUMBER", "0"))
    head_sha = os.environ.get("HEAD_SHA")
    base_ref = os.environ.get("BASE_REF")
    token = os.environ.get("GITHUB_PR_AUTORESOLVE_TOKEN")

    if not all([repo, pr, head_sha, base_ref, token]):
        print(
            "Missing required env vars (REPOSITORY, PR_NUMBER, HEAD_SHA, BASE_REF, GITHUB_PR_AUTORESOLVE_TOKEN)"
        )
        return 1

    # 1) check combined status
    state = combined_status(repo, head_sha, token)
    print(f"Commit {head_sha} combined status: {state}")
    if state != "success":
        print("Checks are not green; skipping auto-resolve")
        return 0

    # 2) list PR files and detect test changes
    files = pr_files(repo, pr, token)
    has_test_changes = any(f.startswith("tests/") for f in files)
    print(f"PR files: {len(files)}; test changes: {has_test_changes}")

    # 3) read PR body and commits for explicit markers
    pr_body, commit_messages = pr_body_and_commits(repo, pr, token)
    explicit_markers: List[str] = []
    marker_re = re.compile(r"FixesReviewThread:\s*([A-Za-z0-9:\/\-_.]+)")
    for m in marker_re.finditer(pr_body):
        explicit_markers.append(m.group(1))
    for msg in commit_messages:
        for m in marker_re.finditer(msg):
            explicit_markers.append(m.group(1))

    # 4) fetch base and compute diff hunks
    git_fetch_base(base_ref)
    # produce diff between base_ref and head_sha
    diff_cmd = ["git", "diff", "--unified=0", f"{base_ref}...{head_sha}"]
    diff = subprocess.run(diff_cmd, capture_output=True, text=True)
    hunks = parse_unified_diff_hunks(diff.stdout)

    # 5) list review threads
    try:
        threads = list_review_threads(repo, pr, token)
    except Exception as e:
        print("Failed to list review threads:", e)
        return 1

    resolved: List[str] = []
    skipped: List[str] = []

    for t in threads:
        tid = t.get("id")
        is_resolved = t.get("isResolved")
        path = t.get("path")
        start = None
        try:
            start = int(t.get("start", {}).get("line")) if t.get("start") else None
        except Exception:
            start = None

        if not tid or is_resolved:
            skipped.append(tid or "<no-id>")
            continue

        # match to hunks
        path_hunks = hunks.get(path, [])
        hit = False
        if start is not None:
            for s, e in path_hunks:
                if s <= start <= e:
                    hit = True
                    break

        # candidate if hit
        candidate = hit

        # apply heuristics: require test changes OR explicit marker
        marker_present = any(
            mid for mid in explicit_markers if str(tid).endswith(mid) or mid in tid
        )
        if candidate and (has_test_changes or marker_present):
            try:
                if os.environ.get("DRY_RUN", "0") == "1":
                    print(f"DRY RUN: would resolve {tid}")
                else:
                    mark_thread_resolved(repo, tid, token)
                    resolved.append(tid)
            except Exception as e:
                print(f"Failed to resolve {tid}: {e}")
        else:
            skipped.append(tid)

    # 6) post audit comment
    if resolved:
        body = (
            "Auto-resolve report:\n\n"
            + f"Resolved threads: {json.dumps(resolved, indent=2)}\n\n"
            + f"Skipped threads: {json.dumps(skipped, indent=2)}\n\n"
            + f"Commit: {head_sha}\n"
            + f"Tests changed: {has_test_changes}\n"
        )
        try:
            post_pr_comment(repo, pr, body, token)
        except Exception as e:
            print("Failed to post audit comment:", e)

    print(f"Done. Resolved: {len(resolved)}; Skipped: {len(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
