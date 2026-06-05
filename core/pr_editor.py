import time
from github import Github, GithubException
from core.metadata import has_metadata_block, has_ai_prefix
from core.github_client import ensure_label, LABEL_NAME


def save_pr(
    client: Github,
    repo_full_name: str,
    pr_number: int,
    new_title: str | None = None,
    new_body: str | None = None,
    add_label: bool = False,
) -> dict:
    """
    Apply changes to a GitHub PR and return the updated serialized dict.
    Raises RuntimeError on API failure.
    """
    try:
        repo = client.get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)

        edit_kwargs = {}
        if new_title is not None and new_title != pr.title:
            edit_kwargs["title"] = new_title
        if new_body is not None and new_body != (pr.body or ""):
            edit_kwargs["body"] = new_body

        if edit_kwargs:
            pr.edit(**edit_kwargs)

        if add_label:
            ensure_label(repo)
            existing_labels = [lbl.name for lbl in pr.labels]
            if LABEL_NAME not in existing_labels:
                pr.add_to_labels(LABEL_NAME)

        # Brief pause then re-fetch for a consistent return value
        time.sleep(0.4)
        pr = repo.get_pull(pr_number)

        labels = [lbl.name for lbl in pr.labels]
        body = pr.body or ""
        title = pr.title or ""

        return {
            "id": f"{repo_full_name}#{pr_number}",
            "number": pr_number,
            "title": title,
            "body": body,
            "state": pr.state,
            "repo_full_name": repo_full_name,
            "url": pr.html_url,
            "created_at": pr.created_at.isoformat() if pr.created_at else "",
            "updated_at": pr.updated_at.isoformat() if pr.updated_at else "",
            "labels": labels,
            "has_ai_prefix": has_ai_prefix(title),
            "has_ai_label": LABEL_NAME in labels,
            "has_ai_metadata": has_metadata_block(body),
        }
    except GithubException as e:
        msg = e.data.get("message", str(e)) if isinstance(e.data, dict) else str(e)
        raise RuntimeError(f"GitHub API error ({e.status}): {msg}")
