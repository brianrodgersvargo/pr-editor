from github import Github, GithubException
from core.metadata import has_metadata_block, has_ai_prefix
from core.github_client import LABEL_NAME


def fetch_user_prs(
    client: Github,
    username: str,
    state: str = "all",
    max_prs: int = 100,
    repo_filter: str = "",
) -> list:
    """
    Search GitHub for PRs authored by username and return a list of serialized dicts.
    Uses the Search API so it crosses all repos in a single call.
    """
    query = f"is:pr author:{username}"
    if state != "all":
        query += f" is:{state}"
    if repo_filter.strip():
        query += f" repo:{repo_filter.strip()}"

    results = []
    try:
        issues = client.search_issues(query, sort="updated", order="desc")
        for issue in issues:
            if len(results) >= max_prs:
                break
            pr_dict = _serialize(issue)
            if pr_dict:
                results.append(pr_dict)
    except GithubException as e:
        msg = e.data.get("message", str(e)) if isinstance(e.data, dict) else str(e)
        raise RuntimeError(f"Search failed: {msg}")

    return results


def _serialize(issue) -> dict | None:
    try:
        repo_full_name = issue.repository.full_name
        label_names = [lbl.name for lbl in issue.labels]
        body = issue.body or ""
        title = issue.title or ""

        return {
            "id": f"{repo_full_name}#{issue.number}",
            "number": issue.number,
            "title": title,
            "body": body,
            "state": issue.state,
            "repo_full_name": repo_full_name,
            "url": issue.html_url,
            "created_at": issue.created_at.isoformat() if issue.created_at else "",
            "updated_at": issue.updated_at.isoformat() if issue.updated_at else "",
            "labels": label_names,
            "has_ai_prefix": has_ai_prefix(title),
            "has_ai_label": LABEL_NAME in label_names,
            "has_ai_metadata": has_metadata_block(body),
        }
    except Exception:
        return None
