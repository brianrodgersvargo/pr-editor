from github import Github, GithubException

LABEL_NAME = "ai-assisted"
LABEL_COLOR = "7057ff"
LABEL_DESC = "Contains AI-assisted changes"


def get_client(token: str) -> tuple:
    """Returns (Github, username) on success or (None, error_message) on failure."""
    try:
        g = Github(token, per_page=100)
        user = g.get_user()
        login = user.login  # triggers the auth request
        return g, login
    except GithubException as e:
        msg = e.data.get("message", str(e)) if isinstance(e.data, dict) else str(e)
        return None, f"Authentication failed: {msg}"
    except Exception as e:
        return None, f"Connection error: {e}"


def ensure_label(repo) -> None:
    """Create the ai-assisted label if it doesn't already exist."""
    try:
        repo.create_label(LABEL_NAME, LABEL_COLOR, LABEL_DESC)
    except GithubException as e:
        if e.status != 422:  # 422 = already exists
            raise


def get_rate_limit_info(client: Github) -> dict:
    try:
        rl = client.get_rate_limit()
        return {
            "core": {"remaining": rl.core.remaining, "limit": rl.core.limit},
            "search": {"remaining": rl.search.remaining, "limit": rl.search.limit},
        }
    except Exception:
        return {}
