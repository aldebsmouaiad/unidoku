# pages/04_Glossar.py
from __future__ import annotations

import re
import html
from urllib.parse import unquote_plus

import streamlit as st

from core.state import init_session_state
from core.model_loader import load_model_config
from core import persist
import streamlit.components.v1 as components


# URLs: http(s)://... oder www....
_URL_RE = re.compile(r"(https?://[^\s<>\"]+|\bwww\.[^\s<>\"]+)", re.IGNORECASE)


def _linkify_urls(text: str) -> str:
    """
    Wandelt URLs im Text in <a>-Links um, die in neuem Tab öffnen.
    Alles andere bleibt HTML-escaped.
    """
    s = text or ""
    if not s.strip():
        return ""

    out: list[str] = []
    last = 0

    for m in _URL_RE.finditer(s):
        start, end = m.span(1)
        url_raw = m.group(1)

        # Text davor
        if start > last:
            out.append(html.escape(s[last:start]))

        # Trailing punctuation nicht in den Link aufnehmen
        trimmed = url_raw.rstrip(").,;:!?\u00bb\u201d\u2019]}")
        tail = url_raw[len(trimmed):]

        href = trimmed
        if href.lower().startswith("www."):
            href = "https://" + href

        out.append(
            f'<a class="rgm-glossary-src" href="{html.escape(href, quote=True)}" '
            f'target="_blank" rel="noopener noreferrer">'
            f"{html.escape(trimmed)}"
            f"</a>"
        )

        if tail:
            out.append(html.escape(tail))

        last = end

    # Resttext
    if last < len(s):
        out.append(html.escape(s[last:]))

    return "".join(out)


def _render_definition(defn: str) -> None:
    """
    Definition rendern:
    - normaler Text bleibt Text (escaped)
    - URLs werden klickbar + neuer Tab
    - Newlines bleiben sichtbar
    """
    linked = _linkify_urls(defn or "")
    safe = linked.replace("\n", "<br>")
    st.markdown(f"<div class='rgm-glossary-def'>{safe}</div>", unsafe_allow_html=True)


def _build_alias_to_canonical(glossary: dict) -> dict[str, str]:
    alias_to_canonical: dict[str, str] = {}

    def _add(alias: str, canonical: str) -> None:
        a = (alias or "").strip()
        c = (canonical or "").strip()
        if not a or not c:
            return
        alias_to_canonical.setdefault(a.lower(), c)

    for canonical in glossary.keys():
        if not isinstance(canonical, str):
            continue
        c = canonical.strip()
        if not c:
            continue

        _add(c, c)

        if "(" in c:
            _add(c.split("(", 1)[0].strip(), c)

        if "," in c:
            left, right = [p.strip() for p in c.split(",", 1)]
            if left and right:
                _add(f"{right} {left}", c)

        for abbr in re.findall(r"\b[A-ZÄÖÜ]{3,}\b", c):
            _add(abbr, c)

    return alias_to_canonical


def _resolve_focus_term(focus_raw: str, glossary: dict) -> str | None:
    if not focus_raw:
        return None

    focus = unquote_plus(focus_raw).strip()
    if not focus:
        return None

    lower_map = {k.lower(): k for k in glossary.keys() if isinstance(k, str)}
    if focus.lower() in lower_map:
        return lower_map[focus.lower()]

    alias_to_canon = _build_alias_to_canonical(glossary)
    canon = alias_to_canon.get(focus.lower())
    if canon and canon in glossary:
        return canon

    for k in glossary.keys():
        if isinstance(k, str) and focus.lower() in k.lower():
            return k

    return None


def main():
    # Defaults setzen (ohne vorhandenes zu überschreiben)
    init_session_state()

    # AID + Restore GANZ AM ANFANG (vor Widgets)
    aid = persist.get_or_create_aid()
    persist.restore(aid)

    st.markdown(
        """
<style>
  .rgm-glossary-def{ line-height: 1.45; }
  a.rgm-glossary-src{
    color:#0a8a0a !important;
    text-decoration: underline !important;
    font-weight: 600;
  }
  a.rgm-glossary-src:hover{ opacity: 0.85; }
</style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Glossar")

    model = load_model_config()
    glossary = model.get("glossary", {}) or {}

    # --- Zurück ---
    ret = st.session_state.get("nav_return_page")
    payload = st.session_state.get("nav_return_payload") or {}

    if ret:
        if st.button("← Zurück", key="glossar_back_btn", use_container_width=False):
            if ret == "Erhebung":
                step = int(payload.get("erhebung_step", 2))
                idx = int(payload.get("erhebung_dim_idx", 0))

                st.session_state.erhebung_step = step
                st.session_state.erhebung_dim_idx = idx
                st.session_state.erhebung_dim_idx_ui = idx

                qid = (payload.get("erhebung_qid") or "").strip()
                if qid:
                    st.session_state["_rgm_scroll_mode"] = "qid"
                    st.session_state["_rgm_scroll_qid"] = qid


            st.session_state["nav_request"] = ret

            # Cleanup (Keys entfernen)
            st.session_state.pop("nav_return_page", None)
            st.session_state.pop("nav_return_payload", None)
            st.session_state.pop("glossary_focus_term", None)

            persist.rerun_with_save(aid)

    st.markdown("---")

    # --- Suche / Fokus ---
    focus_raw = (st.session_state.get("glossary_focus_term") or "").strip()
    focus_key = _resolve_focus_term(focus_raw, glossary)

    search_default = unquote_plus(focus_raw).strip() if focus_raw else ""
    search = st.text_input("Suche", value=search_default, placeholder="Begriff eingeben…").strip()

    shown_focus = False
    if focus_key:
        if not search or (search.lower() in focus_key.lower()):
            with st.expander(focus_key, expanded=True):
                _render_definition(str(glossary.get(focus_key, "")))
            st.divider()
            shown_focus = True

    for term in sorted(glossary.keys(), key=lambda x: str(x).lower()):
        if not isinstance(term, str):
            continue

        if shown_focus and term == focus_key:
            continue

        if search and (search.lower() not in term.lower()):
            continue

        with st.expander(term, expanded=False):
            _render_definition(str(glossary.get(term, "")))

    # am Ende speichern
    persist.save(aid)


if __name__ == "__main__":
    main()
