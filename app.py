import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="PR Editor",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# One-time session state initialisation
for key, default in {
    "github_token": os.getenv("GITHUB_TOKEN", ""),
    "github_client": None,
    "github_username": None,
    "pr_cache": {},
    "selected_pr_id": None,
    "filter_state": "all",
    "filter_repo": "",
    "max_prs": 100,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

from ui.sidebar import render_sidebar
from ui.pr_table import render_pr_table
from ui.pr_detail import render_pr_detail

render_sidebar()

st.title("PR Editor")
st.caption("Retroactively apply AI attribution to your pull requests.")

if not st.session_state.github_client:
    st.info("Enter your GitHub token in the sidebar and click **Connect** to get started.")
    st.stop()

if not st.session_state.pr_cache:
    st.info("Click **Fetch PRs** in the sidebar to load your pull requests.")
    st.stop()

col_list, col_detail = st.columns([3, 2], gap="large")

with col_list:
    render_pr_table()

with col_detail:
    render_pr_detail()
