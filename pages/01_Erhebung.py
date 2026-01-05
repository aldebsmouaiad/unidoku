# pages/01_Erhebung.py
from __future__ import annotations

import io
import json
import csv
import re
import html
import textwrap
from datetime import datetime
from urllib.parse import quote_plus

import streamlit as st
import streamlit.components.v1 as components

from core.state import init_session_state
from core.model_loader import load_model_config
from core import persist

TD_BLUE = "#2F3DB8"
OG_ORANGE = "#F28C28"


# -----------------------------
# Konfiguration: Ziele & Antworten
# -----------------------------
TARGET_OPTIONS = [
    "Eigenes Ziel",
    "Optimiert",
    "Quantitativ gemanagt",
    "Definiert",
    "Gemanagt",
]

TARGET_TO_LEVEL = {
    "Gemanagt": 2.0,
    "Definiert": 3.0,
    "Quantitativ gemanagt": 4.0,
    "Optimiert": 5.0,
}

ANSWER_OPTIONS = [
    "Nicht anwendbar",
    "Gar nicht",
    "In ein paar Fällen",
    "In den meisten Fällen",
    "Vollständig",
]

# Keine Platzhalter-Option mehr: wir nutzen index=None (keine Vorauswahl)
ANSWER_OPTIONS_WIDGET = ANSWER_OPTIONS


def _inject_erhebung_page_css() -> None:
    """Einheitliches Design für Erhebung (Cards/Typografie/Abstände) – Light/Dark kompatibel."""
    dark = bool(st.session_state.get("dark_mode", False))

    border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.10)"
    soft_bg = "rgba(255,255,255,0.06)" if dark else "rgba(0,0,0,0.03)"
    header_bg = "rgba(255,255,255,0.08)" if dark else "rgba(127,127,127,0.10)"
    shadow = "0 12px 28px rgba(0,0,0,0.40)" if dark else "0 10px 24px rgba(0,0,0,0.06)"

    st.markdown(
        f"""
<style>
  /* =========================================================
     Design Tokens (einheitlich)
     ========================================================= */
  div[data-testid="stAppViewContainer"] {{
    --rgm-td-blue: {TD_BLUE};
    --rgm-og-orange: {OG_ORANGE};
    --rgm-border: {border};
    --rgm-soft: {soft_bg};
    --rgm-header-bg: {header_bg};
  }}

  /* Content Breite wie andere Seiten */
  div[data-testid="stAppViewContainer"] .block-container {{
    max-width: 1200px;
    margin: 0 auto;
    padding-top: 1.0rem;
    padding-bottom: 6.0rem; /* Footer + Luft */
  }}

  /* Anchor-Icon neben Überschriften ausblenden */
  a.anchor-link,
  a.header-anchor,
  a[data-testid="stHeaderLink"] {{
    display: none !important;
  }}

  /* =========================================================
     HERO (wie Einführung/Ausfüllhinweise)
     ========================================================= */
  .rgm-hero {{
    background: var(--rgm-card-bg, #fff);
    border: 1px solid var(--rgm-border);
    border-radius: 14px;
    padding: 18px 18px 14px 18px;
    box-shadow: {shadow};
    margin-top: 6px;
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

  .rgm-muted {{
    font-size: 15px;
    line-height: 1.75;
    color: var(--rgm-text, #111);
    opacity: 0.92;
  }}

  .rgm-accent-line {{
    height: 3px;
    width: 96px;
    border-radius: 999px;
    margin: 10px 0 14px 0;
    background: linear-gradient(90deg, var(--rgm-td-blue), var(--rgm-og-orange));
  }}

  /* Badges unter Hero (Organisation/Bereich/Datum/Ziel) */
  .rgm-badges {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
  }}
  .rgm-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid var(--rgm-border);
    background: var(--rgm-soft);
    color: var(--rgm-text, #111);
    font-size: 12.5px;
    line-height: 1.3;
    white-space: nowrap;
  }}
  .rgm-badge b {{
    font-weight: 850;
  }}

  /* =========================================================
     Step 0: Form-Card (WICHTIG: volle Breite, nicht zentriert)
     Streamlit rendert je nach Version:
       - div.stForm
       - div[data-testid="stForm"]
       - form[data-testid="stForm"]
     ========================================================= */
  div.stForm,
  div[data-testid="stForm"],
  form[data-testid="stForm"] {{
    width: 100% !important;
    max-width: none !important;
    margin: 0 !important;
  }}

  /* Optik der Card auf dem WRAPPER (div.stForm / div[data-testid="stForm"]) */
  div.stForm,
  div[data-testid="stForm"] {{
    border: 1px solid var(--rgm-border) !important;
    border-radius: 14px !important;
    background: var(--rgm-card-bg, #fff) !important;
    box-shadow: {shadow} !important;
    padding: 14px 16px 12px 16px !important;
  }}

  /* Innerer Block ebenfalls volle Breite */
  div.stForm > div,
  div[data-testid="stForm"] > div {{
    width: 100% !important;
    max-width: none !important;
  }}

  div.stForm label,
  div[data-testid="stForm"] label {{
    font-weight: 750 !important;
  }}

  div.stForm button[kind="primary"],
  div[data-testid="stForm"] button[kind="primary"] {{
    border-radius: 12px !important;
    font-weight: 800 !important;
  }}

  /* =========================================================
     Fragenlayout
     ========================================================= */
  .rgm-q {{
    margin: 6px 0 6px 0;
    line-height: 1.40;
  }}
  .rgm-qno {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 44px;
    padding: 2px 10px;
    border-radius: 999px;
    border: 1px solid var(--rgm-border);
    background: var(--rgm-soft);
    font-weight: 850;
    margin-right: 8px;
    white-space: nowrap;
  }}

  /* Tabellen/Key-Value Boxen */
  .rgm-kv-wrap {{
    border: 1px solid var(--rgm-border);
    border-radius: 14px;
    overflow: hidden;
    background: var(--rgm-card-bg, #fff);
    box-shadow: {shadow};
  }}
  .rgm-kv-row {{
    display: grid;
    grid-template-columns: 190px 1fr;
    border-bottom: 1px solid var(--rgm-border);
  }}
  .rgm-kv-row:last-child {{ border-bottom: none; }}
  .rgm-kv-l {{
    background: var(--rgm-header-bg);
    padding: 10px 12px;
    font-weight: 800;
    color: var(--rgm-text, #111);
  }}
  .rgm-kv-r {{
    padding: 10px 12px;
    color: var(--rgm-text, #111);
  }}

  /* Radios kompakter */
  div[data-testid="stRadio"] > div {{
    gap: 0.35rem;
  }}

  /* kleine Mobile-Anpassung */
  @media (max-width: 900px) {{
    .rgm-h1 {{ font-size: 26px; }}
    .rgm-hero {{ padding: 16px; }}
  }}
</style>
        """,
        unsafe_allow_html=True,
    )


def _render_hero(title: str, lead: str = "", body: str = "", extra_html: str = "") -> None:
    t = html.escape(title or "")
    lead_html = f'<p class="rgm-lead">{html.escape(lead)}</p>' if lead else ""
    body_html = f'<div style="height:10px"></div><p class="rgm-muted">{html.escape(body)}</p>' if body else ""

    # extra_html MUSS ohne führende 4 Leerzeichen-Zeilen starten (sonst Markdown-Codeblock).
    extra_html = (extra_html or "").strip()

    st.markdown(
        f"""
<div class="rgm-hero">
  <div class="rgm-h1">{t}</div>
  <div class="rgm-accent-line"></div>
  {lead_html}
  {body_html}
  {extra_html}
</div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Hilfsfunktionen (Allgemein)
# -----------------------------
def _count_total_questions(model: dict) -> int:
    total = 0
    for dim in model.get("dimensions", []):
        for lvl in dim.get("levels", []):
            total += len(lvl.get("questions", []))
    return total


def _count_answered_questions(model: dict) -> int:
    answered = 0
    answers = st.session_state.get("answers", {})
    for dim in model.get("dimensions", []):
        for lvl in dim.get("levels", []):
            for q in lvl.get("questions", []):
                qid = q.get("id")
                if not qid:
                    continue
                if qid in answers and answers[qid] in ANSWER_OPTIONS:
                    answered += 1
    return answered


def _code_sort_key(code: str):
    """
    Sortierung wie Excel: TD zuerst, dann OG; danach numerisch.
    Beispiele: TD1.1 < TD1.2 < ... < TD4.4 < OG1.1 < ... < OG4.4
    """
    c = (code or "").strip()
    m = re.match(r"^([A-Za-z]+)(\d+)(?:\.(\d+))?$", c)
    if not m:
        return (99, c, 999, 999)

    prefix = m.group(1).upper()
    major = int(m.group(2))
    minor = int(m.group(3) or 0)

    prefix_order = {"TD": 0, "OG": 1}.get(prefix, 50)
    return (prefix_order, prefix, major, minor)


def _dims_sorted_from_model(model: dict) -> list[dict]:
    dims = model.get("dimensions", []) or []
    return sorted(dims, key=lambda d: _code_sort_key(str(d.get("code", ""))))


def _safe_filename(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^A-Za-z0-9_\-\.]", "", s)
    return s or "export"


def _safe_dom_id(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\-]", "_", (s or "").strip())


# -----------------------------
# Scroll: Erhebung (Top) / Glossar-Rücksprung (Frage)
# -----------------------------
_SCROLL_QP_MODE = "scroll"     # "top" | "qid"
_SCROLL_QP_QID  = "scroll_q"   # qid


def _request_scroll_to_top() -> None:
    st.session_state["_rgm_scroll_mode"] = "top"
    st.session_state.pop("_rgm_scroll_qid", None)


def _request_scroll_to_qid(qid: str) -> None:
    q = (qid or "").strip()
    st.session_state["_rgm_scroll_mode"] = "qid"
    st.session_state["_rgm_scroll_qid"] = q

    try:
        persist.qp_set(_SCROLL_QP_MODE, "qid")
        persist.qp_set(_SCROLL_QP_QID, q)
    except Exception:
        pass


def _apply_scroll_request() -> None:
    mode = st.session_state.pop("_rgm_scroll_mode", None)
    qid = (st.session_state.pop("_rgm_scroll_qid", "") or "").strip()

    # Fallback: Query Params (nur relevant fürs Glossar/Back)
    if not mode:
        try:
            mode = (persist.qp_get(_SCROLL_QP_MODE) or "").strip() or None
            if not qid:
                qid = (persist.qp_get(_SCROLL_QP_QID) or "").strip()
        except Exception:
            pass

    if not mode:
        return

    if mode == "top":
        anchor = "rgm-page-top"
    elif mode == "qid" and qid:
        anchor = f"rgm-q-{_safe_dom_id(qid)}"
    else:
        anchor = ""

    js = f"""
<script>
(function() {{
  function getRootDoc() {{
    try {{ return window.parent.document; }} catch (e) {{ return document; }}
  }}
  const rootDoc = getRootDoc();

  function findScrollers() {{
    const out = [];
    const push = (el) => {{ if (el && !out.includes(el)) out.push(el); }};
    push(rootDoc.querySelector('[data-testid="stAppViewContainer"]'));
    push(rootDoc.querySelector('[data-testid="stMain"]'));
    push(rootDoc.querySelector('section.main'));
    push(rootDoc.scrollingElement);
    push(rootDoc.documentElement);
    push(rootDoc.body);
    return out.filter(Boolean);
  }}

  function userHasScrolled(th=40) {{
    const scs = findScrollers();
    for (const sc of scs) {{
      const t = (sc && typeof sc.scrollTop === "number") ? sc.scrollTop : 0;
      if (t > th) return true;
    }}
    return false;
  }}

  function forceTop() {{
    const scs = findScrollers();
    for (const sc of scs) {{
      try {{
        if (sc.scrollTo) sc.scrollTo({{ top: 0, left: 0, behavior: "auto" }});
        sc.scrollTop = 0;
      }} catch (e) {{}}
    }}
    try {{
      (rootDoc.defaultView || window.parent).scrollTo(0, 0);
    }} catch (e) {{}}
  }}

  function scrollToId(id) {{
    if (!id) return false;
    const el = rootDoc.getElementById(id);
    if (!el) return false;
    try {{
      el.scrollIntoView({{ block: "start", behavior: "auto" }});
    }} catch (e) {{}}
    return true;
  }}

  function clearScrollParamsOnce() {{
    try {{
      const w = window.parent || window;
      const u = new URL(w.location.href);
      u.searchParams.delete("{_SCROLL_QP_MODE}");
      u.searchParams.delete("{_SCROLL_QP_QID}");
      w.history.replaceState({{}}, "", u.toString());
    }} catch (e) {{}}
  }}

  const mode = {json.dumps(mode)};
  const anchor = {json.dumps(anchor)};

  let tries = 0;

  const TOP_MAX_TRIES = 6;
  const QID_MAX_TRIES = 30;

  function tick() {{
    tries += 1;

    if (tries > 1 && userHasScrolled()) {{
      clearScrollParamsOnce();
      return;
    }}

    if (mode === "top") {{
      clearScrollParamsOnce();
      scrollToId(anchor);
      forceTop();
      if (tries >= TOP_MAX_TRIES) return;
      setTimeout(tick, 70);
      return;
    }}

    if (mode === "qid") {{
      const ok = scrollToId(anchor);
      if (ok) {{
        clearScrollParamsOnce();
        return;
      }}
      if (tries >= QID_MAX_TRIES) {{
        clearScrollParamsOnce();
        return;
      }}
      setTimeout(tick, 70);
      return;
    }}

    clearScrollParamsOnce();
  }}

  setTimeout(tick, 80);
}})();
</script>
"""
    components.html(js, height=0)


# -----------------------------
# Glossar: Links + Navigation
# -----------------------------
def _inject_glossary_link_css() -> None:
    st.markdown(
        """
<style>
  a.rgm-glossary-link{
    color:#2E7D32 !important;
    text-decoration: underline !important;
    font-weight: 600;
  }
  a.rgm-glossary-link:hover{ opacity: 0.85; }
</style>
        """,
        unsafe_allow_html=True,
    )


def _build_glossary_alias_index(glossary: dict) -> tuple[list[str], dict[str, str]]:
    aliases: list[str] = []
    alias_to_canonical: dict[str, str] = {}

    def _add(alias: str, canonical: str):
        a = (alias or "").strip()
        c = (canonical or "").strip()
        if not a or not c:
            return
        al = a.lower()
        if al in alias_to_canonical:
            return
        alias_to_canonical[al] = c
        aliases.append(a)

    def _add_adj_variants(phrase: str, canonical: str):
        endings = ["e", "en", "er", "es", "em"]
        tokens = (phrase or "").split()
        if len(tokens) < 2:
            return

        for i in range(len(tokens) - 1):
            t = tokens[i]
            if not t:
                continue
            if not re.match(r"^[a-zäöüß]", t):
                continue

            for end in endings:
                if t.endswith(end) and len(t) > len(end) + 3:
                    stem = t[: -len(end)]
                    for e in endings:
                        variant_tokens = tokens[:]
                        variant_tokens[i] = stem + e
                        _add(" ".join(variant_tokens), canonical)
                    break

    if not isinstance(glossary, dict):
        return [], {}

    for canonical in glossary.keys():
        if not isinstance(canonical, str):
            continue
        c = canonical.strip()
        if not c:
            continue

        _add(c, c)

        if "," in c:
            left, right = [p.strip() for p in c.split(",", 1)]
            if left and right:
                swapped = f"{right} {left}"
                _add(swapped, c)
                _add_adj_variants(swapped, c)

        if "(" in c:
            left = c.split("(", 1)[0].strip()
            _add(left, c)

            if ")" in c:
                inside = c.split("(", 1)[1].rsplit(")", 1)[0].strip()
                if inside:
                    _add(inside, c)

        for sep in ["–", "-", ":"]:
            if sep in c:
                _add(c.split(sep, 1)[0].strip(), c)

        for abbr in re.findall(r"\b[A-ZÄÖÜ]{3,}\b", c):
            _add(abbr, c)

        _add_adj_variants(c, c)

    aliases_sorted = sorted(aliases, key=len, reverse=True)
    return aliases_sorted, alias_to_canonical


def _glossary_linkify(text: str, glossary: dict, return_page: str, return_payload: dict) -> str:
    raw = (text or "")
    if not raw.strip() or not isinstance(glossary, dict) or not glossary:
        return html.escape(raw).replace("\n", "<br>")

    aliases_sorted, alias_to_canonical = _build_glossary_alias_index(glossary)
    if not aliases_sorted or not isinstance(alias_to_canonical, dict):
        return html.escape(raw).replace("\n", "<br>")

    word_chars = r"A-Za-z0-9ÄÖÜäöüß_"
    suffix_chars = r"A-Za-zÄÖÜäöüß"

    parts_pat: list[str] = []
    for alias in aliases_sorted:
        a = (alias or "").strip()
        if not a:
            continue

        esc = re.escape(a)

        starts_word = re.match(rf"^[{word_chars}]", a) is not None
        ends_word = re.match(rf".*[{word_chars}]$", a) is not None

        tokens = a.split()
        last_token = tokens[-1] if tokens else ""
        allow_compound_suffix = (len(tokens) >= 2) and bool(re.match(r"^[A-ZÄÖÜ]", last_token))

        if starts_word:
            esc = rf"(?<![{word_chars}]){esc}"

        if ends_word:
            if allow_compound_suffix:
                esc = rf"{esc}(?:[{suffix_chars}]+)?"
            else:
                esc = rf"{esc}(?![{word_chars}])"

        parts_pat.append(esc)

    if not parts_pat:
        return html.escape(raw).replace("\n", "<br>")

    try:
        pattern = re.compile("|".join(parts_pat), flags=re.IGNORECASE)
    except Exception:
        return html.escape(raw).replace("\n", "<br>")

    ret_step = str(return_payload.get("erhebung_step", "")) if isinstance(return_payload, dict) else ""
    ret_idx = str(return_payload.get("erhebung_dim_idx", "")) if isinstance(return_payload, dict) else ""
    ret_code = str(return_payload.get("dim_code", "")) if isinstance(return_payload, dict) else ""
    ret_qid = str(return_payload.get("qid", "")) if isinstance(return_payload, dict) else ""

    def _href(canonical_term: str) -> str:
        qs = [
            "page=Glossar",
            f"g={quote_plus(canonical_term)}",
            f"from={quote_plus(return_page or '')}",
        ]
        if ret_step:
            qs.append(f"ret_step={quote_plus(ret_step)}")
        if ret_idx:
            qs.append(f"ret_idx={quote_plus(ret_idx)}")
        if ret_code:
            qs.append(f"ret_code={quote_plus(ret_code)}")
        if ret_qid:
            qs.append(f"ret_q={quote_plus(ret_qid)}")

        aid_now = persist.qp_get("aid") or st.session_state.get("_rgm_aid", "")
        if aid_now:
            qs.append(f"aid={quote_plus(str(aid_now))}")

        return "?" + "&".join(qs)

    alias_items = sorted(
        ((a.lower(), c) for a, c in alias_to_canonical.items() if isinstance(a, str) and isinstance(c, str)),
        key=lambda x: len(x[0]),
        reverse=True,
    )

    out: list[str] = []
    last = 0

    for m in pattern.finditer(raw):
        start, end = m.start(), m.end()
        if start > last:
            out.append(html.escape(raw[last:start]).replace("\n", "<br>"))

        matched = m.group(0)
        ml = matched.lower()

        canonical = alias_to_canonical.get(ml)
        if not canonical:
            for al, canon in alias_items:
                if ml.startswith(al):
                    canonical = canon
                    break

        if canonical and canonical in glossary:
            out.append(
                f'<a class="rgm-glossary-link" href="{_href(canonical)}" target="_self" rel="noopener noreferrer">'
                f"{html.escape(matched)}"
                f"</a>"
            )
        else:
            out.append(html.escape(matched))

        last = end

    if last < len(raw):
        out.append(html.escape(raw[last:]).replace("\n", "<br>"))

    return "".join(out)


# -----------------------------
# Persist / Session Sticky Aid
# -----------------------------
def _ensure_aid_sticky() -> str:
    aid = (persist.qp_get("aid") or st.session_state.get("_rgm_aid") or "").strip()

    if not aid:
        aid = persist.get_or_create_aid()

    st.session_state["_rgm_aid"] = aid
    persist.qp_set("aid", aid)
    return aid


# -----------------------------
# Excel-Look Renderer
# -----------------------------
def _render_process_profile(profile: dict, glossary: dict, return_page: str, return_payload: dict) -> None:
    if not isinstance(profile, dict):
        profile = {}

    rows = [
        ("Zweck", profile.get("purpose", "")),
        ("Ergebnisse", profile.get("results", "")),
        ("Basispraktiken", profile.get("basic_practices", "")),
        ("Arbeitsprodukte", profile.get("work_products", "")),
    ]

    parts = ['<div class="rgm-kv-wrap">']
    for label, value in rows:
        label_html = html.escape((label or "").strip())
        value_html = _glossary_linkify(str(value or ""), glossary, return_page, return_payload)
        parts.append(
            f'<div class="rgm-kv-row">'
            f'  <div class="rgm-kv-l">{label_html}</div>'
            f'  <div class="rgm-kv-r">{value_html}</div>'
            f"</div>"
        )
    parts.append("</div>")

    st.markdown("".join(parts), unsafe_allow_html=True)


def _render_excel_text_box(title_left: str, text_right: str, glossary: dict, return_page: str, return_payload: dict) -> None:
    left = html.escape((title_left or "").strip())
    right = _glossary_linkify(str(text_right or ""), glossary, return_page, return_payload)

    st.markdown(
        f"""
<div class="rgm-kv-wrap">
  <div class="rgm-kv-row">
    <div class="rgm-kv-l">{left}</div>
    <div class="rgm-kv-r">{right}</div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _render_level_info_expander(lvl: dict, glossary: dict, return_page: str, return_payload: dict) -> None:
    acceptance = str(lvl.get("acceptance_criteria", "") or "").strip()
    benefit = str(lvl.get("benefit", "") or "").strip()

    if not acceptance and not benefit:
        return

    with st.expander("Abnahmekriterien & Nutzen bei Erreichen der Stufe", expanded=False):
        if acceptance:
            _render_excel_text_box("Abnahmekriterien", acceptance, glossary, return_page, return_payload)
            st.markdown("")
        if benefit:
            _render_excel_text_box("Nutzen bei Erreichen der Stufe", benefit, glossary, return_page, return_payload)


# -----------------------------
# State / Reset / Import-Export
# -----------------------------
def _reset_erhebung_answers() -> None:
    st.session_state["answers"] = {}
    for k in list(st.session_state.keys()):
        if k.startswith("q_"):
            del st.session_state[k]


def _export_own_targets_json(targets: dict[str, float], model: dict, meta: dict) -> bytes:
    payload = {
        "schema": "rgm_own_target_v1",
        "created_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "org": meta.get("org", ""),
        "area": meta.get("area", ""),
        "date_str": meta.get("date_str", ""),
        "targets": {k: int(round(float(v))) for k, v in targets.items()},
        "codes": [str(d.get("code", "")).strip() for d in _dims_sorted_from_model(model)],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def _parse_own_targets_upload(file_name: str, raw: bytes) -> dict[str, int]:
    name = (file_name or "").lower().strip()

    if name.endswith(".json"):
        obj = json.loads(raw.decode("utf-8"))
        if isinstance(obj, dict) and "targets" in obj and isinstance(obj["targets"], dict):
            data = obj["targets"]
        elif isinstance(obj, dict):
            data = obj
        else:
            raise ValueError("Ungültiges JSON-Format.")

        out: dict[str, int] = {}
        for k, v in data.items():
            code = str(k).strip()
            if not code:
                continue
            try:
                iv = int(round(float(v)))
            except Exception:
                raise ValueError(f"Ungültiger Zielwert für {code}: {v!r}")
            out[code] = iv
        return out

    if name.endswith(".csv"):
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise ValueError("CSV enthält keinen Header.")

        f = [h.strip().lower() for h in reader.fieldnames]

        def _pick(*cands: str) -> str | None:
            for cand in cands:
                if cand.lower() in f:
                    return reader.fieldnames[f.index(cand.lower())]
            return None

        code_col = _pick("code", "kürzel", "kuerzel", "subdimension_code")
        val_col = _pick("target", "ziel", "eigenes ziel", "eigenes_ziel", "eigenesziel")

        if not code_col or not val_col:
            raise ValueError("CSV Header muss Spalten für Kürzel/Code und Ziel enthalten (z.B. code,target).")

        out: dict[str, int] = {}
        for row in reader:
            code = str(row.get(code_col, "")).strip()
            if not code:
                continue
            v = row.get(val_col, "")
            try:
                iv = int(round(float(str(v).strip())))
            except Exception:
                raise ValueError(f"Ungültiger Zielwert für {code}: {v!r}")
            out[code] = iv
        return out

    raise ValueError("Bitte eine .json oder .csv Datei hochladen.")


def _apply_imported_targets(imported: dict[str, int], dims_sorted: list[dict]) -> tuple[int, list[str]]:
    options = [1, 2, 3, 4, 5]

    base_default = int(round(float(st.session_state.get("global_target_level", 3.0))))
    base_default = max(1, min(5, base_default))

    targets: dict[str, float] = {}
    missing: list[str] = []
    used = 0

    for d in dims_sorted:
        code = str(d.get("code", "")).strip()
        if not code:
            continue

        if code in imported:
            v = imported[code]
            if v not in options:
                v = max(1, min(5, int(v)))
            used += 1
        else:
            v = base_default
            missing.append(code)

        targets[code] = float(v)
        st.session_state[f"own_target_val_{code}"] = int(v)

    st.session_state.dimension_targets = targets
    st.session_state.erhebung_own_target_defined = True
    return used, missing


# -----------------------------
# Footer (Navigation + Fortschritt Pipeline)
# -----------------------------
def _inject_erhebung_css_for_footer() -> None:
    dark = bool(st.session_state.get("dark_mode", False))

    border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.10)"
    bg = "rgba(17,24,39,0.96)" if dark else "rgba(246,247,249,0.96)"
    shadow = "0 -10px 24px rgba(0,0,0,0.35)" if dark else "0 -10px 24px rgba(0,0,0,0.06)"

    st.markdown(
        f"""
<style>
  div#rgm-erhebung-footer-anchor + div {{
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;

    z-index: 9999;
    background: {bg};
    border-top: 1px solid {border};
    box-shadow: {shadow};
    backdrop-filter: blur(6px);
    padding: 12px 18px 10px 18px;
  }}

  div#rgm-erhebung-footer-anchor + div > div {{
    max-width: 1200px;
    margin: 0 auto;
  }}

  .rgm-footer-title {{
    font-weight: 850;
    margin-bottom: 8px;
    color: var(--rgm-text, #111);
  }}

  .rgm-progress-wrap{{ margin-top: 10px; }}
  .rgm-progress-top{{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:12px;
    margin-bottom:6px;
  }}
  .rgm-progress-label{{
    font-size:12px;
    font-weight:750;
    color: var(--rgm-text, #111);
    opacity: 0.80;
  }}
  .rgm-progress-nums{{
    font-size:12px;
    font-weight:850;
    color: var(--rgm-text, #111);
    opacity: 0.80;
  }}

  .rgm-pipe{{
    display:flex;
    gap:4px;
    width:100%;
  }}
  .rgm-seg{{
    flex:1;
    height:8px;
    border-radius:6px;
    background: rgba(0,0,0,0.10);
  }}
  .rgm-seg-done{{
    background: #7FB800;
  }}
</style>
        """,
        unsafe_allow_html=True,
    )


def _footer_navigation(model: dict, aid: str) -> None:
    """
    Footer-Layout:
    Navigation
    Zu Dimension springen
    [Selectbox]
    [Zurück] [Weiter]
    Fortschritt (Pipe)
    """
    dims = model.get("dimensions", []) or []
    if not dims:
        return

    labels = [f"{d.get('code','')} – {d.get('name','')}".strip(" –") for d in dims]
    n = len(dims)

    idx = int(st.session_state.get("erhebung_dim_idx", 0))
    idx = max(0, min(idx, n - 1))
    st.session_state["erhebung_dim_idx"] = idx
    st.session_state["erhebung_dim_idx_ui"] = idx

    def _on_jump():
        try:
            new_idx = int(st.session_state.get("erhebung_dim_idx_ui", idx))
        except Exception:
            return
        new_idx = max(0, min(new_idx, n - 1))
        old_idx = int(st.session_state.get("erhebung_dim_idx", idx))
        if new_idx == old_idx:
            return
        st.session_state["erhebung_dim_idx"] = new_idx
        _request_scroll_to_top()
        persist.save(aid)

    st.markdown('<div id="rgm-erhebung-footer-anchor"></div>', unsafe_allow_html=True)
    _inject_erhebung_css_for_footer()

    footer = st.container()
    with footer:
        st.markdown('<div class="rgm-footer-title">Navigation</div>', unsafe_allow_html=True)
        st.caption("Zu Dimension springen")

        st.selectbox(
            "",
            options=list(range(n)),
            format_func=lambda i: labels[i],
            key="erhebung_dim_idx_ui",
            label_visibility="collapsed",
            on_change=_on_jump,
        )

        st.markdown("")

        b1, b2 = st.columns(2, gap="medium")

        with b1:
            if st.button("◀ Zurück", use_container_width=True, disabled=(idx == 0), key="erh_prev_btn"):
                st.session_state["erhebung_dim_idx"] = max(0, idx - 1)
                _request_scroll_to_top()
                persist.save(aid)
                st.rerun()

        with b2:
            is_last = (idx == n - 1)
            if st.button("Zum Dashboard ▶" if is_last else "Weiter ▶", use_container_width=True, key="erh_next_btn"):
                if not is_last:
                    st.session_state["erhebung_dim_idx"] = min(n - 1, idx + 1)
                    _request_scroll_to_top()
                else:
                    st.session_state["nav_request"] = "Dashboard"
                persist.save(aid)
                st.rerun()

        answered = _count_answered_questions(model)
        total = _count_total_questions(model)

        segments = 20
        done = 0
        if total > 0 and answered > 0:
            done = max(1, int((answered / total) * segments))
        done = min(segments, done)

        pipe: list[str] = []
        pipe.append('<div class="rgm-progress-wrap">')
        pipe.append(
            f'<div class="rgm-progress-top">'
            f'  <div class="rgm-progress-label">Fortschritt</div>'
            f'  <div class="rgm-progress-nums">{answered}/{total}</div>'
            f"</div>"
        )
        pipe.append('<div class="rgm-pipe">')
        for i in range(segments):
            cls = "rgm-seg rgm-seg-done" if i < done else "rgm-seg"
            pipe.append(f'<div class="{cls}"></div>')
        pipe.append("</div></div>")

        st.markdown("".join(pipe), unsafe_allow_html=True)


# -----------------------------
# Step 0: Eingabemaske
# -----------------------------
def _meta_form_step(aid: str) -> None:
    _render_hero("Erhebung", "Angaben zur Erhebung")
    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)

    meta = st.session_state.meta
    prev_target_label = meta.get("target_label", "")

    current_target = meta.get("target_label") or "Quantitativ gemanagt"
    if current_target not in TARGET_OPTIONS:
        current_target = "Quantitativ gemanagt"

    open_own_target_clicked = False
    start_clicked = False

    with st.form("erhebung_meta_form", clear_on_submit=False):
        c1, c2 = st.columns(2, gap="large")

        with c1:
            org = st.text_input("Name der Organisation:", value=meta.get("org", ""), placeholder="Beispiel GmbH")
            area = st.text_input("Bereich:", value=meta.get("area", ""), placeholder="Bereich A")
            assessor = st.text_input(
                "Erhebung durchgeführt von:", value=meta.get("assessor", ""), placeholder="Herr/Frau Beispiel"
            )

        with c2:
            date_str = st.text_input("Datum der Durchführung:", value=meta.get("date_str", ""), placeholder="TT.MM.JJJJ")
            target_label = st.selectbox(
                "Angestrebtes Ziel:",
                TARGET_OPTIONS,
                index=TARGET_OPTIONS.index(current_target),
            )

        if target_label == "Eigenes Ziel":
            if not st.session_state.get("erhebung_own_target_defined", False):
                open_own_target_clicked = st.form_submit_button(
                    "Eigenes Ziel definieren", type="primary", use_container_width=True
                )
            else:
                start_clicked = st.form_submit_button("Erhebung starten", type="primary", use_container_width=True)
        else:
            start_clicked = st.form_submit_button("Erhebung starten", type="primary", use_container_width=True)

    if meta.get("target_label") == "Eigenes Ziel" and st.session_state.get("erhebung_own_target_defined", False):
        left, right = st.columns([1, 3])
        with left:
            if st.button("Eigenes Ziel ändern", use_container_width=True, key="own_target_change_btn"):
                st.session_state.erhebung_step = 1
                persist.rerun_with_save(aid)
        with right:
            st.success("Eigenes Ziel ist definiert.")

    if not open_own_target_clicked and not start_clicked:
        return

    errors = []
    if not org.strip():
        errors.append("Bitte den Namen der Organisation angeben.")
    if not assessor.strip():
        errors.append("Bitte angeben, wer die Erhebung durchgeführt hat.")
    if date_str.strip() and not re.match(r"^\d{2}\.\d{2}\.\d{4}$", date_str.strip()):
        errors.append("Datum bitte im Format TT.MM.JJJJ eingeben (z. B. 03.12.2025).")

    if errors:
        for e in errors:
            st.error(e)
        return

    meta["org"] = org.strip()
    meta["area"] = area.strip()
    meta["assessor"] = assessor.strip()
    meta["date_str"] = date_str.strip()
    meta["target_label"] = target_label

    if target_label != prev_target_label:
        st.session_state.dimension_targets = {}
        for k in list(st.session_state.keys()):
            if k.startswith("own_target_val_") or k.startswith("target_"):
                del st.session_state[k]
        st.session_state.erhebung_own_target_defined = False
        st.session_state.pop("own_target_dirty", None)
        st.session_state.pop("own_target_saved_msg_bottom", None)

    if target_label == "Eigenes Ziel":
        if open_own_target_clicked:
            st.session_state.erhebung_step = 1
            persist.rerun_with_save(aid)

        if start_clicked and not st.session_state.get("erhebung_own_target_defined", False):
            st.error("Bitte zuerst „Eigenes Ziel definieren“.")
            return

        if start_clicked:
            _reset_erhebung_answers()
            st.session_state.erhebung_step = 2
            st.session_state.erhebung_dim_idx = 0
            st.session_state.erhebung_dim_idx_ui = 0
            _request_scroll_to_top()
            persist.rerun_with_save(aid)
    else:
        st.session_state["erhebung_own_target_defined"] = False
        st.session_state.global_target_level = float(TARGET_TO_LEVEL[target_label])

        st.session_state.dimension_targets = {}
        st.session_state.pop("own_target_dirty", None)
        st.session_state.pop("own_target_saved_msg_bottom", None)
        for k in list(st.session_state.keys()):
            if k.startswith("target_") or k.startswith("own_target_val_"):
                del st.session_state[k]

        if start_clicked:
            _reset_erhebung_answers()
            st.session_state.erhebung_step = 2
            st.session_state.erhebung_dim_idx = 0
            st.session_state.erhebung_dim_idx_ui = 0
            _request_scroll_to_top()
            persist.rerun_with_save(aid)


# -----------------------------
# Step 1: Eigenes Ziel definieren
# (unverändert – aus Platzgründen identisch zu deiner Version)
# -----------------------------
def _own_target_step(aid: str) -> None:
    _render_hero(
        "Eigenes Ziel definieren",
        "Zielniveau je Subdimension",
        "Bitte wählen Sie für jede Subdimension den angestrebten Reifegrad zwischen 1 und 5. "
        "Optional können Sie vorhandene Zielwerte importieren oder exportieren.",
    )
    st.markdown("")

    model = load_model_config()
    dims_sorted = _dims_sorted_from_model(model)
    if not dims_sorted:
        st.error("Keine Subdimensionen gefunden (Model-Konfiguration leer).")
        return

    st.markdown("#### Import / Export")

    col_imp, col_exp = st.columns([1.3, 1.0], gap="large")
    with col_imp:
        up = st.file_uploader(
            "Eigenes Ziel hochladen (JSON oder CSV):",
            type=["json", "csv"],
            key="own_target_upload_file",
            help="JSON: exportiertes Format. CSV: Spalten z.B. code,target",
        )
        if st.button("Importieren", use_container_width=True, key="own_target_import_btn", disabled=(up is None)):
            try:
                raw = up.getvalue() if up is not None else b""
                imported = _parse_own_targets_upload(up.name if up else "", raw)
                used, missing = _apply_imported_targets(imported, dims_sorted)

                st.session_state["own_target_saved_msg_bottom"] = True

                msg = f"Import erfolgreich: {used} Werte übernommen."
                if missing:
                    msg += (
                        " Fehlende Subdimensionen wurden mit dem Standardwert vorbelegt "
                        f"({int(round(float(st.session_state.get('global_target_level', 3.0))))})."
                    )
                st.session_state["own_target_import_msg"] = ("success", msg)
                persist.rerun_with_save(aid)
            except Exception as e:
                st.session_state["own_target_import_msg"] = ("error", str(e))
                persist.rerun_with_save(aid)

    with col_exp:
        targets_now: dict[str, float] = st.session_state.get("dimension_targets", {})
        can_export = bool(targets_now)
        meta = st.session_state.meta
        fn = f"eigenes_ziel_{_safe_filename(meta.get('org',''))}_{_safe_filename(meta.get('date_str',''))}.json"
        data = _export_own_targets_json(targets_now, model, meta) if can_export else b""
        st.download_button(
            "Eigenes Ziel herunterladen",
            data=data,
            file_name=fn,
            mime="application/json",
            use_container_width=True,
            disabled=not can_export,
        )
        st.caption("Download ist verfügbar, sobald Werte vorhanden sind (Import oder Speicherung).")

    if st.session_state.get("own_target_import_msg"):
        kind, msg = st.session_state.pop("own_target_import_msg")
        if kind == "success":
            st.success(msg)
        else:
            st.error(msg)

    st.markdown("---")

    query = st.text_input(
        "Suche (Kürzel oder Subdimension):",
        value="",
        placeholder="z. B. TD3 oder Übersetzungsmanagement",
    )

    def _match(d: dict) -> bool:
        if not query.strip():
            return True
        q = query.strip().lower()
        return q in str(d.get("code", "")).lower() or q in str(d.get("name", "")).lower()

    filtered = [d for d in dims_sorted if _match(d)]

    options = [1, 2, 3, 4, 5]

    existing: dict = st.session_state.get("dimension_targets", {}) or {}
    base_default = int(round(float(st.session_state.get("global_target_level", 3.0))))
    base_default = max(1, min(5, base_default))

    for dd in dims_sorted:
        c = str(dd.get("code", "")).strip()
        if not c:
            continue
        k_all = f"own_target_val_{c}"

        dv = existing.get(c, base_default)
        try:
            dv = int(round(float(dv)))
        except Exception:
            dv = base_default
        dv = max(1, min(5, dv))

        if k_all not in st.session_state or st.session_state.get(k_all) not in options:
            st.session_state[k_all] = dv

    if not filtered:
        st.info("Keine Treffer für die aktuelle Suche.")
    else:
        h1, h2, h3 = st.columns([0.18, 0.52, 0.30], vertical_alignment="center")
        with h1:
            st.markdown("**Kürzel**")
        with h2:
            st.markdown("**Subdimension**")
        with h3:
            st.markdown("**Eigenes Ziel**")

        for d in filtered:
            code = str(d.get("code", "")).strip()
            name = str(d.get("name", "")).strip()
            k = f"own_target_val_{code}"

            r1, r2, r3 = st.columns([0.18, 0.52, 0.30], vertical_alignment="center")
            with r1:
                st.markdown(f"**{code}**")
            with r2:
                st.markdown(name)
            with r3:
                st.radio("", options=options, key=k, horizontal=True, label_visibility="collapsed")

    stored = st.session_state.get("dimension_targets", {}) or {}
    defined = bool(st.session_state.get("erhebung_own_target_defined", False))

    dirty = False
    if defined and stored:
        for dd in dims_sorted:
            c = str(dd.get("code", "")).strip()
            if not c:
                continue
            k_all = f"own_target_val_{c}"
            cur = st.session_state.get(k_all, None)
            if cur not in options:
                continue
            if float(stored.get(c, -999.0)) != float(cur):
                dirty = True
                break

    st.session_state["own_target_dirty"] = dirty

    st.markdown("---")

    b1, b2, _ = st.columns([1, 1, 2])
    with b1:
        if st.button("Zurück", use_container_width=True, key="own_target_back_btn"):
            st.session_state.erhebung_step = 0
            persist.rerun_with_save(aid)

    with b2:
        save_label = "Änderungen speichern" if dirty else "Eigenes Ziel speichern"
        save_clicked = st.button(save_label, type="primary", use_container_width=True, key="own_target_save_btn")

    if save_clicked:
        targets: dict[str, float] = {}
        for d in dims_sorted:
            code = str(d.get("code", "")).strip()
            val = st.session_state.get(f"own_target_val_{code}", None)
            if val not in options:
                val = base_default
            targets[code] = float(int(val))

        st.session_state.dimension_targets = targets
        st.session_state.erhebung_own_target_defined = True

        st.session_state["own_target_dirty"] = False
        st.session_state["own_target_saved_msg_bottom"] = True
        persist.rerun_with_save(aid)

    if st.session_state.get("own_target_saved_msg_bottom", False):
        st.success("Eigenes Ziel wurde gespeichert. Du kannst jetzt die Erhebung starten.")
        st.session_state.pop("own_target_saved_msg_bottom", None)
        st.session_state["own_target_dirty"] = False
        dirty = False

    if dirty:
        st.warning(
            "Sie haben Werte geändert, die noch nicht gespeichert wurden. "
            "Bitte „Änderungen speichern“ klicken, damit diese Werte in der Erhebung verwendet werden."
        )

    if st.session_state.get("erhebung_own_target_defined", False):
        can_start = not dirty
        if st.button("Erhebung starten", type="primary", use_container_width=True, key="own_target_start_btn", disabled=not can_start):
            _reset_erhebung_answers()
            st.session_state.erhebung_step = 2
            st.session_state.erhebung_dim_idx = 0
            st.session_state.erhebung_dim_idx_ui = 0
            _request_scroll_to_top()
            persist.rerun_with_save(aid)


# -----------------------------
# Step 2: Fragen
# -----------------------------
def _render_dimension(dim: dict, glossary: dict, dim_idx: int, aid: str) -> None:
    code = str(dim.get("code", "")).strip()
    name = str(dim.get("name", "")).strip()

    st.subheader(f"{code} – {name}")
    _inject_glossary_link_css()

    if "answers" not in st.session_state or not isinstance(st.session_state.get("answers"), dict):
        st.session_state["answers"] = {}
    answers: dict = st.session_state["answers"]

    return_page = "Erhebung"
    return_payload_base = {
        "erhebung_step": int(st.session_state.get("erhebung_step", 2)),
        "erhebung_dim_idx": int(dim_idx),
        "dim_code": code,
    }

    process_profile = dim.get("process_profile", {}) or {}
    has_any_profile = any(str(process_profile.get(k, "") or "").strip() for k in ["purpose", "results", "basic_practices", "work_products"])
    if has_any_profile:
        with st.expander("Prozess-Steckbrief", expanded=False):
            _render_process_profile(process_profile, glossary, return_page, return_payload_base)

    st.markdown("---")

    meta_target = st.session_state.meta.get("target_label", "")
    dim_targets = st.session_state.get("dimension_targets", {}) or {}

    if meta_target == "Eigenes Ziel":
        if not st.session_state.get("erhebung_own_target_defined", False):
            st.warning("Eigenes Ziel ist nicht definiert. Bitte zuerst „Eigenes Ziel definieren“.")
        else:
            target_val = dim_targets.get(code, None)
            if target_val is None:
                st.warning("Für diese Subdimension wurde kein Ziel gefunden. Bitte „Eigenes Ziel ändern“ nutzen.")
            else:
                st.markdown(f"**Eigenes Sollniveau:** {float(target_val):.0f}")
                st.caption("Änderungen am Eigenen Ziel bitte über „Eigenes Ziel ändern“ durchführen.")
    else:
        target_val = float(st.session_state.get("global_target_level", 3.0))
        st.markdown(f"**Sollniveau:** {target_val:.0f}")
        st.caption("Vordefiniertes Ziel. Änderungen bitte über „Angaben bearbeiten“ vornehmen.")

    st.markdown("---")

    dirty = False
    levels = dim.get("levels", []) or []
    for li, lvl in enumerate(levels):
        level_no = int(lvl.get("level_number", 0) or 0)
        level_name = str(lvl.get("name", "") or "").strip()

        st.markdown(f"**Stufe {level_no} – {level_name}**" if level_name else f"**Stufe {level_no}**")
        _render_level_info_expander(lvl, glossary, return_page, return_payload_base)

        questions = lvl.get("questions", []) or []
        for i, q in enumerate(questions, start=1):
            qid = q.get("id")
            qtext = str(q.get("text", "") or "").strip()
            if not qid:
                continue

            anchor_id = f"rgm-q-{_safe_dom_id(str(qid))}"
            st.markdown(f'<div id="{anchor_id}"></div>', unsafe_allow_html=True)

            return_payload_q = dict(return_payload_base)
            return_payload_q["qid"] = str(qid)

            q_html = _glossary_linkify(qtext, glossary, return_page, return_payload_q)
            st.markdown(
                f'<div class="rgm-q"><span class="rgm-qno">{level_no}.{i}</span>{q_html}</div>',
                unsafe_allow_html=True,
            )

            k_widget = f"q_{qid}"
            saved = answers.get(qid, None)

            if st.session_state.get(k_widget, None) == "":
                st.session_state.pop(k_widget, None)

            if k_widget in st.session_state and st.session_state.get(k_widget) not in ANSWER_OPTIONS:
                st.session_state.pop(k_widget, None)

            default_index = ANSWER_OPTIONS.index(saved) if saved in ANSWER_OPTIONS else None

            choice = st.radio(
                "",
                ANSWER_OPTIONS,
                index=default_index,
                key=k_widget,
                label_visibility="collapsed",
            )
            if choice in ANSWER_OPTIONS and choice != saved:
                answers[qid] = choice
                dirty = True

        if li < len(levels) - 1:
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            st.markdown(
                "<hr style='margin: 10px 0 18px 0; border:0; border-top:1px solid var(--rgm-border, rgba(0,0,0,0.10));'>",
                unsafe_allow_html=True,
            )

    if dirty:
        persist.save(aid)


def _questions_step(aid: str) -> None:
    model = load_model_config()
    glossary = model.get("glossary", {}) or {}

    dims_sorted = _dims_sorted_from_model(model)
    model_sorted = dict(model)
    model_sorted["dimensions"] = dims_sorted

    st.markdown('<div id="rgm-page-top"></div>', unsafe_allow_html=True)

    meta = st.session_state.meta
    target_label = meta.get("target_label", "-")

    # WICHTIG: dedent => KEIN Markdown-Codeblock!
    badges_html = textwrap.dedent(
        f"""
        <div class="rgm-badges">
          <div class="rgm-badge"><b>Organisation:</b>&nbsp;{html.escape(meta.get('org','-') or '-')}</div>
          <div class="rgm-badge"><b>Bereich:</b>&nbsp;{html.escape(meta.get('area','-') or '-')}</div>
          <div class="rgm-badge"><b>Datum:</b>&nbsp;{html.escape(meta.get('date_str','-') or '-')}</div>
          <div class="rgm-badge"><b>Ziel:</b>&nbsp;{html.escape(target_label or '-')}</div>
        </div>
        """
    ).strip()

    _render_hero(
        "Erhebung",
        "Bitte beantworten Sie die Fragen je Subdimension so objektiv wie möglich.",
        extra_html=badges_html,
    )

    st.markdown("---")

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.2], gap="small")
    with c1:
        if st.button("Angaben bearbeiten", use_container_width=True, key="edit_meta_btn"):
            st.session_state.erhebung_step = 0
            _request_scroll_to_top()
            persist.rerun_with_save(aid)
    with c2:
        if target_label == "Eigenes Ziel":
            if st.button("Eigenes Ziel ändern", use_container_width=True, key="edit_own_target_btn"):
                st.session_state.erhebung_step = 1
                _request_scroll_to_top()
                persist.rerun_with_save(aid)
        else:
            st.button("Eigenes Ziel ändern", disabled=True, use_container_width=True, key="noop_edit_own_target")
    with c3:
        if st.button("Ausfüllhinweise", use_container_width=True, key="open_hints_btn"):
            st.session_state["nav_request"] = "Ausfüllhinweise"
            persist.rerun_with_save(aid)
    with c4:
        if target_label == "Eigenes Ziel" and st.session_state.get("erhebung_own_target_defined", False):
            targets_now: dict[str, float] = st.session_state.get("dimension_targets", {})
            fn = f"eigenes_ziel_{_safe_filename(meta.get('org',''))}_{_safe_filename(meta.get('date_str',''))}.json"
            data = _export_own_targets_json(targets_now, model, meta)
            st.download_button(
                "Eigenes Ziel herunterladen",
                data=data,
                file_name=fn,
                mime="application/json",
                use_container_width=True,
            )
        else:
            st.button("Eigenes Ziel herunterladen", disabled=True, use_container_width=True, key="noop_download_own_target")

    st.markdown("---")

    if not dims_sorted:
        st.error("Keine Dimensionen/Subdimensionen gefunden (Model-Konfiguration leer).")
        return

    idx = int(st.session_state.get("erhebung_dim_idx", 0))
    idx = min(max(idx, 0), len(dims_sorted) - 1)
    st.session_state.erhebung_dim_idx = idx

    _render_dimension(dims_sorted[idx], glossary, idx, aid)
    _footer_navigation(model_sorted, aid)

    _apply_scroll_request()


# -----------------------------
# Main Entry
# -----------------------------
def main():
    init_session_state()
    _inject_erhebung_page_css()

    aid = _ensure_aid_sticky()
    if st.session_state.get("_rgm_restored_aid") != aid:
        persist.restore(aid)
        st.session_state["_rgm_restored_aid"] = aid

    if "erhebung_step" not in st.session_state:
        st.session_state.erhebung_step = 0
    if "erhebung_dim_idx" not in st.session_state:
        st.session_state.erhebung_dim_idx = 0
    if "erhebung_dim_idx_ui" not in st.session_state:
        st.session_state.erhebung_dim_idx_ui = 0
    if "erhebung_own_target_defined" not in st.session_state:
        st.session_state.erhebung_own_target_defined = False
    if "answers" not in st.session_state or not isinstance(st.session_state.get("answers"), dict):
        st.session_state["answers"] = {}
    if "dimension_targets" not in st.session_state or not isinstance(st.session_state.get("dimension_targets"), dict):
        st.session_state["dimension_targets"] = {}

    if st.session_state.meta.get("target_label") != "Eigenes Ziel":
        st.session_state.erhebung_own_target_defined = False

    step = int(st.session_state.get("erhebung_step", 0))
    if step == 0:
        _meta_form_step(aid)
    elif step == 1:
        _own_target_step(aid)
    else:
        _questions_step(aid)

    persist.save(aid)


if __name__ == "__main__":
    main()
