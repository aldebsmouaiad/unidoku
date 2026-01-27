# pages/04_Glossar.py
from __future__ import annotations

import re
import html
from urllib.parse import unquote_plus

import streamlit as st

from core.state import init_session_state
from core.model_loader import load_model_config
from core import persist


TU_GREEN = "#639A00"
TU_ORANGE = "#CA7406"
TD_BLUE = "#2F3DB8"
OG_ORANGE = "#F28C28"

_URL_RE = re.compile(r"(https?://[^\s<>\"]+|\bwww\.[^\s<>\"]+)", re.IGNORECASE)


def _linkify_urls(text: str) -> str:
    s = text or ""
    if not s.strip():
        return ""

    out: list[str] = []
    last = 0

    for m in _URL_RE.finditer(s):
        start, end = m.span(1)
        url_raw = m.group(1)

        if start > last:
            out.append(html.escape(s[last:start]))

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

    if last < len(s):
        out.append(html.escape(s[last:]))

    return "".join(out)


def _render_definition(defn: str) -> None:
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


def _do_return(aid: str, ret: str, payload: dict) -> None:
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

    st.session_state.pop("nav_return_page", None)
    st.session_state.pop("nav_return_payload", None)
    st.session_state.pop("glossary_focus_term", None)

    persist.rerun_with_save(aid)


def main() -> None:
    init_session_state()

    # KEIN restore hier! (wird zentral in app.py gemacht)
    aid = persist.get_or_create_aid()

    # Darkmode: Theme-State aus app.py (Fallback auf alte Keys)
    dark = bool(st.session_state.get("dark_mode", st.session_state.get("ui_dark_mode", False)))

    border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.10)"
    soft_bg = "rgba(255,255,255,0.06)" if dark else "rgba(0,0,0,0.03)"
    hover_bg = "rgba(255,255,255,0.07)" if dark else "rgba(0,0,0,0.035)"
    shadow = "0 12px 28px rgba(0,0,0,0.40)" if dark else "0 10px 24px rgba(0,0,0,0.06)"

    btn2_bg = "rgba(255,255,255,0.06)" if dark else "#ffffff"
    btn2_text = "rgba(250,250,250,0.92)" if dark else "#111111"

    st.markdown(
        f"""
<style>
  .rgm-page {{
    max-width: 1200px;
    margin: 0 auto;
    padding-bottom: 6px;
  }}

  .rgm-h1 {{
    font-size: 30px;
    font-weight: 850;
    line-height: 1.15;
    margin: 0 0 6px 0;
    color: var(--rgm-text, #111);
  }}

  .rgm-lead {{
    font-size: 15px;
    line-height: 1.75;
    color: var(--rgm-text, #111);
    opacity: 0.92;
    margin: 0;
  }}

  .rgm-hero {{
    background: var(--rgm-card-bg, #fff);
    border: 1px solid {border};
    border-radius: 14px;
    padding: 18px 18px 14px 18px;
    box-shadow: {shadow};
  }}

  .rgm-accent-line {{
    height: 3px;
    width: 96px;
    border-radius: 999px;
    margin: 10px 0 14px 0;
    background: linear-gradient(90deg, {TD_BLUE}, {OG_ORANGE});
  }}

  div#rgm_glossary_tools + div {{
    background: var(--rgm-card-bg, #fff);
    border: 1px solid {border};
    border-radius: 14px;
    padding: 14px 16px;
    box-shadow: {shadow};
    margin-top: 14px;
  }}

  div#rgm_glossary_list + div {{
    margin-top: 14px;
  }}

  .rgm-card-title {{
    font-weight: 850;
    font-size: 15px;
    margin: 0 0 10px 0;
    color: var(--rgm-text, #111);
  }}

  .rgm-pill {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 10px;
    border-radius: 999px;
    border: 1px solid {border};
    background: {soft_bg};
    color: var(--rgm-text, #111);
    font-size: 13px;
    font-weight: 750;
  }}

  .rgm-glossary-def {{
    line-height: 1.75;
    font-size: 14px;
    color: var(--rgm-text, #111);
    opacity: 0.95;
  }}

  a.rgm-glossary-src {{
    color: {TU_GREEN} !important;
    text-decoration: underline !important;
    font-weight: 750;
  }}
  a.rgm-glossary-src:hover {{
    opacity: 0.88;
  }}

  div[data-testid="stExpander"] {{
    margin: 0 0 10px 0;
  }}

  div[data-testid="stExpander"] details {{
    background: var(--rgm-card-bg, #fff);
    border: 1px solid {border};
    border-radius: 14px;
    box-shadow: {shadow};
    overflow: hidden;
  }}

  div[data-testid="stExpander"] summary {{
    padding: 10px 12px !important;
    font-weight: 850 !important;
    font-size: 15px !important;
    color: var(--rgm-text, #111) !important;
  }}

  div[data-testid="stExpander"] summary:hover {{
    background: {hover_bg} !important;
  }}

  div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {{
    padding: 0 12px 12px 12px !important;
  }}

  .stApp button[data-testid="baseButton-secondary"],
  .stApp div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]) {{
    background: {btn2_bg} !important;
    color: {btn2_text} !important;
    border: 1px solid {border} !important;
    border-radius: 10px !important;
    font-weight: 650 !important;
    opacity: 1 !important;
    transition: background 120ms ease, border-color 120ms ease, color 120ms ease;
  }}

  .stApp button[data-testid="baseButton-secondary"] *,
  .stApp div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]) * {{
    color: inherit !important;
  }}

  .stApp button[data-testid="baseButton-secondary"]:not(:disabled):hover,
  .stApp div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]):not(:disabled):hover {{
    background: {TU_ORANGE} !important;
    border-color: {TU_ORANGE} !important;
    color: #ffffff !important;
  }}

  .stApp button[data-testid="baseButton-secondary"]:not(:disabled):hover *,
  .stApp div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]):not(:disabled):hover * {{
    color: #ffffff !important;
  }}

  @media (max-width: 900px) {{
    .rgm-h1 {{ font-size: 26px; }}
    .rgm-hero {{ padding: 16px; }}
    div#rgm_glossary_tools + div {{ padding: 12px 12px; }}
  }}
</style>
        """,
        unsafe_allow_html=True,
    )

    model = load_model_config()
    glossary = model.get("glossary", {}) or {}

    ret = st.session_state.get("nav_return_page")
    payload = st.session_state.get("nav_return_payload") or {}

    st.markdown('<div class="rgm-page">', unsafe_allow_html=True)

    st.markdown(
        """
<div class="rgm-hero">
  <div class="rgm-h1">Glossar</div>
  <div class="rgm-accent-line"></div>
  <p class="rgm-lead">
    Hier finden Sie Definitionen zu zentralen Begriffen und Abkürzungen. Nutzen Sie die Suche oder klappen Sie Einträge auf.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div id="rgm_glossary_tools"></div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="rgm-card-title">Suche</div>', unsafe_allow_html=True)

        focus_raw = (st.session_state.get("glossary_focus_term") or "").strip()
        focus_key = _resolve_focus_term(focus_raw, glossary)

        search_default = unquote_plus(focus_raw).strip() if focus_raw else ""
        search = st.text_input(
            "Suche",
            value=search_default,
            placeholder="Begriff eingeben…",
            label_visibility="collapsed",
        ).strip()

    st.markdown('<div id="rgm_glossary_list"></div>', unsafe_allow_html=True)
    with st.container():
        shown_focus = False

        if focus_key:
            if not search or (search.lower() in focus_key.lower()):
                with st.expander(focus_key, expanded=True):
                    _render_definition(str(glossary.get(focus_key, "")))
                shown_focus = True

        terms: list[str] = []
        for term in sorted(glossary.keys(), key=lambda x: str(x).lower()):
            if not isinstance(term, str):
                continue
            if shown_focus and term == focus_key:
                continue
            if search and (search.lower() not in term.lower()):
                continue
            terms.append(term)

        if shown_focus and terms:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if not shown_focus and not terms:
            st.info("Keine Einträge passend zur aktuellen Auswahl.")
        else:
            for term in terms:
                with st.expander(term, expanded=False):
                    _render_definition(str(glossary.get(term, "")))

    if ret:
        st.markdown("---")
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Zurück", key="glossar_back_btn_bottom", use_container_width=True):
                _do_return(aid=aid, ret=ret, payload=payload)
        with c2:
            st.empty()

    st.markdown("</div>", unsafe_allow_html=True)

    persist.save(aid)


if __name__ == "__main__":
    main()
