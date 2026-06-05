import streamlit as st
from core.github_client import get_client, get_rate_limit_info
from core.pr_fetcher import fetch_user_prs
from core.pr_editor import save_pr
from core.metadata import upsert_metadata_block, add_ai_prefix, ALL_SCOPES


def render_sidebar():
    with st.sidebar:
        _auth_section()
        if st.session_state.github_client:
            st.divider()
            _fetch_section()
            if st.session_state.pr_cache:
                st.divider()
                _bulk_section()


def _auth_section():
    st.header("GitHub Auth")

    token = st.text_input(
        "Personal Access Token",
        value=st.session_state.github_token,
        type="password",
        help="Requires `repo` scope (or `public_repo` for public repos only).",
    )

    if st.button("Connect", type="primary", use_container_width=True):
        if not token.strip():
            st.error("Enter a token first.")
            return
        with st.spinner("Connecting..."):
            client, result = get_client(token.strip())
        if client:
            st.session_state.github_token = token.strip()
            st.session_state.github_client = client
            st.session_state.github_username = result
            st.session_state.pr_cache = {}
            st.session_state.selected_pr_id = None
            st.success(f"Connected as **{result}**")
        else:
            st.error(result)

    if st.session_state.github_username:
        st.caption(f"Signed in as **{st.session_state.github_username}**")
        rl = get_rate_limit_info(st.session_state.github_client)
        if rl:
            s = rl.get("search", {})
            c = rl.get("core", {})
            st.caption(
                f"Rate limits — Search: {s.get('remaining','?')}/{s.get('limit','?')} "
                f"· Core: {c.get('remaining','?')}/{c.get('limit','?')}"
            )


def _fetch_section():
    st.header("Fetch PRs")

    st.session_state.filter_state = st.selectbox(
        "State",
        ["all", "open", "closed"],
        index=["all", "open", "closed"].index(st.session_state.filter_state),
    )
    st.session_state.filter_repo = st.text_input(
        "Repo (owner/repo)",
        value=st.session_state.filter_repo,
        placeholder="Leave blank for all repos",
    )
    st.session_state.max_prs = st.slider("Max PRs", 10, 500, st.session_state.max_prs, 10)

    if st.button("Fetch PRs", use_container_width=True):
        with st.spinner("Searching..."):
            try:
                prs = fetch_user_prs(
                    st.session_state.github_client,
                    st.session_state.github_username,
                    state=st.session_state.filter_state,
                    max_prs=st.session_state.max_prs,
                    repo_filter=st.session_state.filter_repo,
                )
                st.session_state.pr_cache = {pr["id"]: pr for pr in prs}
                st.session_state.selected_pr_id = None
                st.success(f"Loaded {len(prs)} pull requests.")
            except Exception as e:
                st.error(str(e))

    if st.session_state.pr_cache:
        st.caption(f"{len(st.session_state.pr_cache)} PRs in cache")


def _bulk_section():
    cache = st.session_state.pr_cache
    selected = {pid for pid in cache if st.session_state.get(f"sel_{pid}", False)}

    if not selected:
        st.caption("Select PRs in the list below to bulk-apply changes.")
        return

    st.header(f"Bulk Apply ({len(selected)} PR{'s' if len(selected) != 1 else ''})")

    do_prefix = st.checkbox("Add [AI] prefix to title", value=True, key="bulk_do_prefix")
    do_label = st.checkbox("Add ai-assisted label", value=True, key="bulk_do_label")
    do_metadata = st.checkbox("Add / update metadata block", value=True, key="bulk_do_metadata")

    model = "claude-sonnet-4-6"
    scopes = list(ALL_SCOPES)
    if do_metadata:
        model = st.text_input("Model", value="claude-sonnet-4-6", key="bulk_model")
        scopes = st.multiselect("Scopes", ALL_SCOPES, default=ALL_SCOPES, key="bulk_scopes")

    if st.button("Apply to Selected", type="primary", use_container_width=True):
        _run_bulk(selected, do_prefix, do_label, do_metadata, model, scopes)


def _run_bulk(selected_ids, do_prefix, do_label, do_metadata, model, scopes):
    client = st.session_state.github_client
    cache = st.session_state.pr_cache
    ids = list(selected_ids)

    progress = st.progress(0, text="Starting...")
    results = []

    for i, pr_id in enumerate(ids):
        pr = cache.get(pr_id)
        if not pr:
            results.append({"id": pr_id, "ok": False, "error": "not in cache"})
            continue

        progress.progress((i + 1) / len(ids), text=f"Applying to {pr_id}…")

        new_title = add_ai_prefix(pr["title"]) if do_prefix else None
        if new_title == pr["title"]:
            new_title = None

        new_body = None
        if do_metadata:
            new_body = upsert_metadata_block(pr["body"] or "", model, scopes)
            if new_body == (pr["body"] or ""):
                new_body = None

        try:
            updated = save_pr(
                client,
                pr["repo_full_name"],
                pr["number"],
                new_title=new_title,
                new_body=new_body,
                add_label=do_label,
            )
            st.session_state.pr_cache[pr_id] = updated
            results.append({"id": pr_id, "ok": True, "error": None})
        except Exception as e:
            results.append({"id": pr_id, "ok": False, "error": str(e)})

    progress.empty()

    ok = sum(1 for r in results if r["ok"])
    failed = [r for r in results if not r["ok"]]

    if not failed:
        st.success(f"Applied to {ok} PR{'s' if ok != 1 else ''} successfully.")
    else:
        st.warning(f"{ok} succeeded, {len(failed)} failed:")
        for r in failed:
            st.error(f"• {r['id']}: {r['error']}")

    # Clear checkboxes
    for pr_id in selected_ids:
        st.session_state[f"sel_{pr_id}"] = False
