import re

SENTINEL_BEGIN = "<!-- AI-METADATA-BEGIN -->"
SENTINEL_END = "<!-- AI-METADATA-END -->"
BLOCK_REGEX = re.compile(
    r"<!-- AI-METADATA-BEGIN -->.*?<!-- AI-METADATA-END -->",
    re.DOTALL,
)
AI_PREFIX = "[AI] "

ALL_SCOPES = [
    "tests",
    "refactor scaffold",
    "draft implementation",
    "PR description",
]


def has_metadata_block(body: str) -> bool:
    return SENTINEL_BEGIN in (body or "")


def has_ai_prefix(title: str) -> bool:
    return (title or "").startswith(AI_PREFIX)


def add_ai_prefix(title: str) -> str:
    if has_ai_prefix(title):
        return title
    return AI_PREFIX + title


def remove_ai_prefix(title: str) -> str:
    if has_ai_prefix(title):
        return title[len(AI_PREFIX):]
    return title


def parse_metadata_fields(body: str) -> dict:
    defaults = {"model": "claude-sonnet-4-6", "scopes": list(ALL_SCOPES)}
    if not has_metadata_block(body or ""):
        return defaults

    model_match = re.search(r"\*\*Model:\*\*\s*(.+)", body)
    scope_match = re.search(r"\*\*AI-assisted scope:\*\*\s*(.+)", body)

    return {
        "model": model_match.group(1).strip() if model_match else defaults["model"],
        "scopes": (
            [s.strip() for s in scope_match.group(1).split(" / ")]
            if scope_match
            else defaults["scopes"]
        ),
    }


def render_metadata_block(model: str, scopes: list) -> str:
    scope_str = " / ".join(scopes) if scopes else "(none)"
    return (
        f"{SENTINEL_BEGIN}\n"
        f"**Tool:** Claude Code  \n"
        f"**Model:** {model}  \n"
        f"**AI-assisted scope:** {scope_str}  \n"
        f"**Human review note:** reviewed and validated by me\n"
        f"{SENTINEL_END}"
    )


def upsert_metadata_block(body: str, model: str, scopes: list) -> str:
    body = body or ""
    block = render_metadata_block(model, scopes)
    if has_metadata_block(body):
        return BLOCK_REGEX.sub(block, body)
    return body.rstrip() + "\n\n---\n\n" + block
