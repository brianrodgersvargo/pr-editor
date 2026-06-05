import streamlit as st


def _badge(label: str, active: bool) -> str:
    color = "#2da44e" if active else "#8c959f"
    return (
        f'<span style="background:{color};color:#fff;padding:1px 6px;'
        f'border-radius:12px;font-size:11px;margin-right:3px;white-space:nowrap">'
        f"{label}</span>"
    )


def render_pr_table():
    cache = st.session_state.pr_cache
    prs = sorted(cache.values(), key=lambda p: p.get("updated_at", ""), reverse=True)

    # ── toolbar row ───────────────────────────────────────────────────────────
    t1, t2, t3, t4 = st.columns([2, 2, 4, 2])
    with t1:
        if st.button("Select All", use_container_width=True):
            for p in prs:
                st.session_state[f"sel_{p['id']}"] = True
            st.rerun()
    with t2:
        if st.button("Clear", use_container_width=True):
            for p in prs:
                st.session_state[f"sel_{p['id']}"] = False
            st.rerun()
    with t3:
        search = st.text_input("Filter", placeholder="title or repo…", label_visibility="collapsed")
    with t4:
        selected_count = sum(1 for p in prs if st.session_state.get(f"sel_{p['id']}", False))
        if selected_count:
            st.markdown(
                f'<div style="padding-top:6px;text-align:right">'
                f'<b>{selected_count}</b> selected</div>',
                unsafe_allow_html=True,
            )

    if search:
        q = search.lower()
        prs = [p for p in prs if q in p["title"].lower() or q in p["repo_full_name"].lower()]

    st.caption(f"{len(prs)} PRs shown")

    # ── header row ────────────────────────────────────────────────────────────
    h0, h1, h2, h3, h4 = st.columns([1, 3, 7, 4, 2])
    h0.caption("")
    h1.caption("Repo / #")
    h2.caption("Title")
    h3.caption("Badges")
    h4.caption("")
    st.divider()

    # ── data rows ─────────────────────────────────────────────────────────────
    for pr in prs:
        pr_id = pr["id"]
        c0, c1, c2, c3, c4 = st.columns([1, 3, 7, 4, 2])

        with c0:
            checked = st.checkbox(
                "",
                value=st.session_state.get(f"sel_{pr_id}", False),
                key=f"sel_{pr_id}",
                label_visibility="collapsed",
            )
            # keep selected_pr_ids in sync (read by sidebar)
            _ = checked  # value already persisted in session_state by the widget

        with c1:
            short_repo = pr["repo_full_name"].split("/")[-1]
            st.markdown(
                f'<a href="{pr["url"]}" target="_blank" style="font-size:13px">'
                f"{short_repo}#{pr['number']}</a>",
                unsafe_allow_html=True,
            )

        with c2:
            icon = "🟢" if pr["state"] == "open" else "⚫"
            title = pr["title"]
            if len(title) > 55:
                title = title[:52] + "…"
            st.markdown(f'{icon} <span style="font-size:13px">{title}</span>', unsafe_allow_html=True)

        with c3:
            st.markdown(
                _badge("[AI]", pr["has_ai_prefix"])
                + _badge("label", pr["has_ai_label"])
                + _badge("meta", pr["has_ai_metadata"]),
                unsafe_allow_html=True,
            )

        with c4:
            is_selected = st.session_state.selected_pr_id == pr_id
            if st.button(
                "✏️ Edit" if not is_selected else "▶ Editing",
                key=f"edit_{pr_id}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
            ):
                st.session_state.selected_pr_id = pr_id
                st.rerun()
