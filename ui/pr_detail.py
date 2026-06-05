import streamlit as st
from core.metadata import (
    has_ai_prefix,
    add_ai_prefix,
    remove_ai_prefix,
    upsert_metadata_block,
    has_metadata_block,
    parse_metadata_fields,
    render_metadata_block,
    ALL_SCOPES,
)
from core.pr_editor import save_pr
from core.github_client import LABEL_NAME


def render_pr_detail():
    pr_id = st.session_state.get("selected_pr_id")

    if not pr_id:
        st.subheader("PR Detail")
        st.info("Click **Edit** on a PR to open it here.")
        return

    pr = st.session_state.pr_cache.get(pr_id)
    if not pr:
        st.warning(f"PR `{pr_id}` not found in cache.")
        return

    repo_part = pr["repo_full_name"].split("/")[-1]
    st.subheader(f"{repo_part} #{pr['number']}")
    st.markdown(f"[View on GitHub ↗]({pr['url']})", unsafe_allow_html=False)

    existing = parse_metadata_fields(pr["body"] or "")

    # ── Title ─────────────────────────────────────────────────────────────────
    st.markdown("**Current title**")
    st.code(pr["title"], language=None)

    add_prefix = st.checkbox(
        "Add `[AI]` prefix to title",
        value=has_ai_prefix(pr["title"]),
        key=f"{pr_id}_prefix",
    )

    preview_title = pr["title"]
    if add_prefix and not has_ai_prefix(preview_title):
        preview_title = add_ai_prefix(preview_title)
    elif not add_prefix and has_ai_prefix(preview_title):
        preview_title = remove_ai_prefix(preview_title)

    if preview_title != pr["title"]:
        st.caption(f"New title: `{preview_title}`")

    st.divider()

    # ── Label ─────────────────────────────────────────────────────────────────
    add_label = st.checkbox(
        f"Add `{LABEL_NAME}` label",
        value=pr["has_ai_label"],
        key=f"{pr_id}_label",
        help="Creates the label in the repo if it doesn't exist yet.",
    )

    st.divider()

    # ── Metadata block ────────────────────────────────────────────────────────
    add_metadata = st.checkbox(
        "Add / update AI metadata block",
        value=pr["has_ai_metadata"],
        key=f"{pr_id}_metadata",
    )

    model = existing["model"]
    scopes = existing["scopes"]

    if add_metadata:
        model = st.text_input("Model", value=existing["model"], key=f"{pr_id}_model")
        scopes = st.multiselect(
            "AI-assisted scope",
            ALL_SCOPES,
            default=[s for s in existing["scopes"] if s in ALL_SCOPES],
            key=f"{pr_id}_scopes",
        )
        with st.expander("Preview metadata block"):
            st.code(render_metadata_block(model, scopes), language="markdown")

    st.divider()

    # ── Current body ──────────────────────────────────────────────────────────
    with st.expander("Current PR body"):
        body_text = pr["body"] or "(empty)"
        st.text(body_text[:3000] + ("…" if len(body_text) > 3000 else ""))

    # ── Actions ───────────────────────────────────────────────────────────────
    col_save, col_discard = st.columns(2)

    with col_save:
        if st.button("Save Changes", type="primary", use_container_width=True, key=f"{pr_id}_save"):
            _save(pr, add_prefix, add_label, add_metadata, model, scopes)

    with col_discard:
        if st.button("Close", use_container_width=True, key=f"{pr_id}_discard"):
            _clear_draft(pr_id)
            st.session_state.selected_pr_id = None
            st.rerun()


def _save(pr, add_prefix, add_label, add_metadata, model, scopes):
    pr_id = pr["id"]

    # Compute new title
    new_title = pr["title"]
    if add_prefix and not has_ai_prefix(new_title):
        new_title = add_ai_prefix(new_title)
    elif not add_prefix and has_ai_prefix(new_title):
        new_title = remove_ai_prefix(new_title)
    if new_title == pr["title"]:
        new_title = None

    # Compute new body
    new_body = None
    if add_metadata:
        candidate = upsert_metadata_block(pr["body"] or "", model, scopes)
        if candidate != (pr["body"] or ""):
            new_body = candidate

    # Check if label actually needs adding
    apply_label = add_label and not pr["has_ai_label"]

    if new_title is None and new_body is None and not apply_label:
        st.info("No changes to save.")
        return

    with st.spinner("Saving…"):
        try:
            updated = save_pr(
                st.session_state.github_client,
                pr["repo_full_name"],
                pr["number"],
                new_title=new_title,
                new_body=new_body,
                add_label=apply_label,
            )
            st.session_state.pr_cache[pr_id] = updated
            _clear_draft(pr_id)
            st.success("Saved successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Save failed: {e}")


def _clear_draft(pr_id: str):
    """Remove widget state so the form re-initialises from fresh PR data next open."""
    for suffix in ("_prefix", "_label", "_metadata", "_model", "_scopes"):
        st.session_state.pop(f"{pr_id}{suffix}", None)
