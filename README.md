# PR Editor

A Streamlit app to retroactively apply AI attribution metadata to your GitHub pull requests — adding an `[AI]` title prefix, an `ai-assisted` label, and a structured metadata block to the PR body.

## Setup & Running

1. Create a GitHub personal access token with `repo` scope (Settings → Developer settings → Personal access tokens) and add it to a `.env` file:

   ```bash
   cp .env.example .env
   # edit .env and set GITHUB_TOKEN=ghp_...
   ```

2. Install dependencies and start the app:

   ```bash
   task env
   task start
   ```
