# PR Editor

A Streamlit app to retroactively apply AI attribution metadata to your GitHub pull requests.

## Features

- Browse all your PRs across repos with live status badges
- Per-PR editing:
  - Add `[AI]` prefix to the title
  - Add an `ai-assisted` label (created in the repo automatically if missing)
  - Append or update a structured AI metadata block in the PR body
- Bulk-select PRs and apply a standard template to all of them at once

The metadata block written to each PR body looks like this:

```markdown
---

**Tool:** Claude Code
**Model:** claude-sonnet-4-6
**AI-assisted scope:** tests / draft implementation / PR description
**Human review note:** reviewed and validated by me
```

The block is delimited by HTML comments so re-applying it updates rather than duplicates.

## Setup

**1. Clone and install dependencies**

```bash
pip install -r requirements.txt
```

**2. Create a GitHub personal access token**

Go to GitHub → Settings → Developer settings → Personal access tokens.

Required scopes:
- `repo` — for private and public repos
- `public_repo` — if you only need public repos

**3. Configure your token**

```bash
cp .env.example .env
# edit .env and set GITHUB_TOKEN=ghp_...
```

Alternatively, you can paste the token directly in the app's sidebar — it won't be persisted to disk that way.

## Running

```bash
python -m streamlit run app.py
```

## Usage

1. Enter your token in the sidebar and click **Connect**
2. Optionally filter by state (open/closed/all) or a specific repo, then click **Fetch PRs**
3. Click **Edit** on any PR to open the edit panel on the right
4. Toggle the changes you want and click **Save Changes**

For bulk edits, check the boxes next to multiple PRs — the sidebar will show a **Bulk Apply** section where you can configure and apply a template to all selected PRs at once.

## Project structure

```
app.py              # Streamlit entry point
core/
  metadata.py       # Metadata block parsing, rendering, title prefix logic
  github_client.py  # Auth, label creation, rate limit helpers
  pr_fetcher.py     # GitHub Search API → serialized PR dicts
  pr_editor.py      # Write operations (title, body, labels)
ui/
  sidebar.py        # Auth, fetch controls, bulk-apply panel
  pr_table.py       # PR list with status badges and checkboxes
  pr_detail.py      # Per-PR edit form
```
