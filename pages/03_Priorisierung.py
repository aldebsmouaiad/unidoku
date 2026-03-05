# /workspaces/unidoku/pages/03_Priorisierung.py
from __future__ import annotations

import copy
import json

import streamlit as st
import streamlit.components.v1 as components

from pathlib import Path
import urllib.request
import urllib.error

from core.model_loader import load_model_config
from core.overview import build_overview_table
from core.state import init_session_state

TU_ORANGE = "#CA7406"
TD_BLUE = "#2F3DB8"
OG_ORANGE = "#F28C28"

PRIORITY_OPTIONS = ["", "A (hoch)", "B (mittel)", "C (niedrig)"]

MEASURES_FILE = Path(__file__).resolve().parents[1] / "data" / "measures.json"

@st.cache_data(ttl=60)
def load_measures_map() -> dict:
    if MEASURES_FILE.exists():
        try:
            data = json.loads(MEASURES_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}

def normalize_measure_text(text: str) -> str:
    return " ".join((text or "").split()).strip()

MEASURE_PICK_PLACEHOLDER = "— bitte auswählen —"

@st.dialog("Maßnahmen-Vorschläge")
def measure_dialog(code: str, suggestions: list[str]) -> None:
    # Optional: kleine Infozeile, kann auch weg
    st.caption(f"Dimension: {code}")

    if not suggestions:
        st.info("Keine Vorschläge vorhanden.")
        return

    box = st.container(height=620)  # passt gut zu 92vh Dialog
    with box:
        # Duplikate case-insensitive entfernen
        seen = set()
        uniq = []
        for s in suggestions:
            s = (s or "").strip()
            k = s.lower()
            if s and k not in seen:
                seen.add(k)
                uniq.append(s)
        suggestions = uniq
        
        choice = st.radio(
            label="",
            options=[MEASURE_PICK_PLACEHOLDER] + suggestions,
            index=0,
            key=f"dlg_pick_{code}",
            label_visibility="collapsed",
        )

    # Sobald Nutzer etwas auswählt -> übernehmen + Dialog schließen (ohne Button)
    if choice != MEASURE_PICK_PLACEHOLDER:
        st.session_state[f"action_{code}"] = choice
        st.rerun()  # schließt den Dialog

def render_measure_sharing_consent() -> None:
    """
    Opt-In am Anfang der Seite:
    Nutzer entscheidet, ob Maßnahmen als Vorschläge für andere gespeichert werden dürfen.
    """
    st.info(
        "**Hinweis (Maßnahmen-Pool):**\n\n"
        "Sie können optional Ihre eingegebenen Maßnahmen **als Vorschläge für andere Nutzer** bereitstellen.\n"
        "Wenn Sie zustimmen, wird **ausschließlich der Text im Feld „Maßnahme“** gespeichert.\n\n"
        "Bitte tragen Sie dort **keine sensiblen Daten** ein."
    )

    if "share_measures_opt_in" not in st.session_state:
        st.session_state["share_measures_opt_in"] = False
    if "share_measures_radio" not in st.session_state:
        st.session_state["share_measures_radio"] = "Nein"

    c1, c2 = st.columns([3, 1], gap="small")
    with c1:
        st.radio(
            "Möchten Sie Ihre Maßnahmen speichern und als Vorschläge für andere Nutzer zur Verfügung stellen?",
            options=["Nein", "Ja"],
            horizontal=True,
            key="share_measures_radio",
        )
    with c2:
        if st.button("Übernehmen", use_container_width=True):
            st.session_state["share_measures_opt_in"] = (st.session_state["share_measures_radio"] == "Ja")
            st.toast("Einstellung gespeichert.", icon="✅")
            st.rerun()
            
def github_create_measure_issue(measure_text: str, dimension_code: str) -> int:
    """
    Erstellt ein GitHub Issue (Label: measure:pending).
    Benötigt secrets:
      GITHUB_OWNER, GITHUB_REPO, GITHUB_TOKEN
    """
    owner = st.secrets["GITHUB_OWNER"]
    repo = st.secrets["GITHUB_REPO"]
    token = st.secrets["GITHUB_TOKEN"]

    txt = normalize_measure_text(measure_text)
    if len(txt) < 3:
        raise ValueError("Maßnahme zu kurz.")
    if len(txt) > 240:
        raise ValueError("Maßnahme zu lang (max. 240 Zeichen).")

    title = f"[Measure Pool] {dimension_code}: {txt[:80]}"
    body = (
        "### measure_text\n"
        f"{txt}\n\n"
        "### dimension_code\n"
        f"{dimension_code}\n"
    )

    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    payload = {"title": title, "body": body, "labels": ["measure:pending"]}
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            out = json.loads(resp.read().decode("utf-8"))
            return int(out["number"])
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub Issue fehlgeschlagen: {e.code} {e.read().decode('utf-8')}")


def get_answers() -> dict:
    return st.session_state.get("answers", {}) or {}


def after_dash(text: str) -> str:
    """
    Gibt nur den Teil nach dem ersten '-' zurück (getrimmt).
    Beispiel: 'Wissensmanagement - Wissensspeicherung' -> 'Wissensspeicherung'
    """
    s = "" if text is None else str(text)
    return s.split("-", 1)[1].strip() if "-" in s else s.strip()


def _stable_json(obj: dict) -> str:
    """Stabiler Vergleich für Dicts (Dirty-Check)."""
    return json.dumps(obj or {}, sort_keys=True, ensure_ascii=False)


def collect_priorities_from_session(codes: list[str], keep_existing: dict) -> dict:
    """
    Baut ein priorities-dict aus den aktuellen Widget-Werten in st.session_state.
    - codes: alle Dimension-Codes, die in dieser Ansicht gerendert wurden
    - keep_existing: vorhandene Werte, die erhalten bleiben sollen (z.B. nicht gerenderte Codes)
    """
    new_priorities = dict(keep_existing) if isinstance(keep_existing, dict) else {}

    for code in codes:
        prio = st.session_state.get(f"prio_{code}", "") or ""
        action = st.session_state.get(f"action_{code}", "") or ""
        timeframe = st.session_state.get(f"timeframe_{code}", "") or ""
        responsible = st.session_state.get(f"resp_{code}", "") or ""

        if prio or action or timeframe or responsible:
            new_priorities[code] = {
                "priority": prio,
                "action": action,
                "timeframe": timeframe,
                "responsible": responsible,
            }
        else:
            new_priorities.pop(code, None)

    return new_priorities


def _inject_priorisierung_css() -> None:
    """Einheitliches Design (wie Einführung/Ausfüllhinweise) für Priorisierung."""
    # Darkmode robust (falls App "ui_dark_mode" nutzt)
    dark = bool(st.session_state.get("ui_dark_mode", st.session_state.get("dark_mode", False)))

    border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.10)"
    soft_bg = "rgba(255,255,255,0.06)" if dark else "rgba(0,0,0,0.03)"
    header_bg = "rgba(255,255,255,0.08)" if dark else "rgba(127,127,127,0.10)"
    hover_bg = "rgba(255,255,255,0.07)" if dark else "rgba(0,0,0,0.035)"
    shadow = "0 12px 28px rgba(0,0,0,0.40)" if dark else "0 10px 24px rgba(0,0,0,0.06)"

    # Secondary-Button (Zurück) – wie in Einführung
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

  .rgm-muted {{
    font-size: 15px;
    line-height: 1.75;
    color: var(--rgm-text, #111);
    opacity: 0.92;
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

  .rgm-card {{
    background: var(--rgm-card-bg, #fff);
    border: 1px solid {border};
    border-radius: 14px;
    padding: 14px 16px;
    box-shadow: {shadow};
    margin-top: 16px;
  }}

  .rgm-card-title {{
    font-weight: 850;
    font-size: 15px;
    margin: 0 0 10px 0;
    color: var(--rgm-text, #111);
  }}

  .rgm-subtle {{
    font-size: 13px;
    line-height: 1.6;
    color: var(--rgm-text, #111);
    opacity: 0.85;
    margin: 0;
  }}

  .rgm-divider {{
    height: 1px;
    background: {border};
    margin: 16px 0 8px 0;
  }}

  /* Expander als „Card“ */
  div[data-testid="stExpander"] {{
    border: 1px solid {border};
    border-radius: 14px;
    overflow: hidden;
    box-shadow: {shadow};
    background: var(--rgm-card-bg, #fff);
  }}

  div[data-testid="stExpander"] summary {{
    padding: 12px 14px !important;
    font-weight: 850 !important;
    color: var(--rgm-text, #111) !important;
    background: {header_bg} !important;
  }}

  div[data-testid="stExpander"] summary:hover {{
    background: {hover_bg} !important;
  }}

  div[data-testid="stExpander"] details {{
    border-radius: 14px;
  }}

  /* Expander Body Padding (Innenraum) */
  div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {{
    padding: 12px 14px 14px 14px;
  }}

  /* Kleine Pill für Gap */
  .rgm-pill {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid {border};
    background: {soft_bg};
    color: var(--rgm-text, #111);
    font-size: 13px;
    font-weight: 750;
    margin: 8px 0 8px 0;
    width: fit-content;
  }}

  /* Widgets: etwas ruhiger (ohne zu aggressiv in Streamlit einzugreifen) */
  div[data-testid="stTextInput"] input,
  div[data-testid="stSelectbox"] div {{
    border-radius: 10px !important;
  }}

  /* =========================================
     NAV-BUTTONS: Secondary wie in Einführung
     ========================================= */
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

  .stApp button[data-testid="baseButton-secondary"]:focus,
  .stApp div.stButton > button:not([data-testid="baseButton-primary"]):not([kind="primary"]):focus {{
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(99,154,0,0.25) !important;
  }}

  @media (max-width: 900px) {{
    .rgm-h1 {{ font-size: 26px; }}
    .rgm-hero {{ padding: 16px; }}
    .rgm-card {{ padding: 12px 12px; }}
  }}
  
  /* ==========================
   DIALOG (st.dialog) – fast fullscreen
   ========================== */

/* Streamlit nutzt je nach Version stDialog oder stModal */
div[data-testid="stDialog"] > div[role="dialog"],
div[data-testid="stModal"] > div[role="dialog"],
div[data-testid="stDialog"] div[role="dialog"],
div[data-testid="stModal"] div[role="dialog"]{{
  width: 96vw !important;
  max-width: 96vw !important;
  height: 92vh !important;
  max-height: 92vh !important;
}}

/* Innenbereich scrollbar (falls Inhalt länger ist) */
div[data-testid="stDialog"] div[role="dialog"] section,
div[data-testid="stModal"] div[role="dialog"] section{{
  max-height: 92vh !important;
  overflow: auto !important;
}}

/* Mobile etwas mehr Rand */
@media (max-width: 700px){{
  div[data-testid="stDialog"] div[role="dialog"],
  div[data-testid="stModal"] div[role="dialog"]{{
    width: 98vw !important;
    max-width: 98vw !important;
    height: 94vh !important;
    max-height: 94vh !important;
  }}
}}
</style>
        """,
        unsafe_allow_html=True,
    )
    


def attach_datalist_to_measure_input(marker_id: str, datalist_id: str, options: list[str]) -> None:
    """
    Baut im Parent-DOM eine <datalist> und hängt sie an das Textfeld,
    das im selben Container wie der marker_id liegt.
    """
    # JSON sicher in JS einbetten
    marker_js = json.dumps(marker_id)
    list_js = json.dumps(datalist_id)
    opts_js = json.dumps(options or [], ensure_ascii=False)

    components.html(
    f"""
<script>
(() => {{
  const markerId = {marker_js};
  const listId = {list_js};
  const options = {opts_js};

  function findInput(doc, marker) {{
    // 1) Scope möglichst eng: Expander-Body / Container
    const scope =
      marker.closest('div[data-testid="stExpanderDetails"]') ||
      marker.closest('div[data-testid="stVerticalBlock"]') ||
      doc;

    // 2) Versuche: erstes Text-Input nach dem Marker innerhalb des Scopes
    const inputs = Array.from(scope.querySelectorAll('input[type="text"], input'));
    for (const inp of inputs) {{
      const rel = marker.compareDocumentPosition(inp);
      // inp liegt nach marker
      if (rel & Node.DOCUMENT_POSITION_FOLLOWING) return inp;
    }}

    // 3) Fallback: irgendein Input im Scope
    return inputs[0] || null;
  }}

  function upsert() {{
    const doc = window.parent.document;
    const marker = doc.getElementById(markerId);
    if (!marker) return false;

    const input = findInput(doc, marker);
    if (!input) return false;

    let dl = doc.getElementById(listId);
    if (!dl) {{
      dl = doc.createElement("datalist");
      dl.id = listId;
      doc.body.appendChild(dl);
    }}

    dl.innerHTML = "";
    for (const v of options) {{
      const opt = doc.createElement("option");
      opt.value = v;
      dl.appendChild(opt);
    }}

    input.setAttribute("list", listId);
    return true;
  }}

  let tries = 0;
  const t = setInterval(() => {{
    tries++;
    if (upsert() || tries >= 30) clearInterval(t);
  }}, 120);
}})();
</script>
""",
    height=0,
    width=0,
)


def main() -> None:
    init_session_state()
    _inject_priorisierung_css()

    st.markdown('<div class="rgm-page">', unsafe_allow_html=True)

    # HERO
    st.markdown(
        """
<div class="rgm-hero">
  <div class="rgm-h1">Priorisierung &amp; Maßnahmenplanung</div>
  <div class="rgm-accent-line"></div>
  <p class="rgm-lead">
    Legen Sie für jede Dimension fest, wie wichtig sie ist und welche konkreten Maßnahmen Sie angehen möchten.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )
    
    render_measure_sharing_consent()
    st.markdown('<div class="rgm-divider"></div>', unsafe_allow_html=True)

    model = load_model_config()

    answers = get_answers()
    global_target = float(st.session_state.get("global_target_level", 3.0))
    dim_targets = st.session_state.get("dimension_targets", {}) or {}

    # committed = offiziell übernommene Werte
    priorities_committed = st.session_state.get("priorities", {}) or {}

    # Draft/Committed einmalig initialisieren
    if "priorities_draft" not in st.session_state:
        st.session_state["priorities_draft"] = copy.deepcopy(priorities_committed)
    if "priorities_committed" not in st.session_state:
        st.session_state["priorities_committed"] = copy.deepcopy(priorities_committed)

    df = build_overview_table(
        model=model,
        answers=answers,
        global_target_level=global_target,
        per_dimension_targets=dim_targets,
        priorities=priorities_committed,
    )

    if df is None or df.empty:
        st.markdown(
            """
<div class="rgm-card">
  <div class="rgm-card-title">Hinweis</div>
  <p class="rgm-subtle">Noch keine Ergebnisse vorhanden – bitte zuerst die Erhebung durchführen.</p>
</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = df.copy()
    df["name_short"] = df["name"].apply(after_dash)

    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        cat = st.selectbox("Kategorie", options=["Alle", "TD", "OG"], index=0)
    with c2:
        show_all = st.checkbox("Alle Dimensionen anzeigen (auch Gap ≤ 0)", value=False)

    df_view = df.copy()
    if cat != "Alle":
        df_view = df_view[df_view["category"] == cat]
    if not show_all:
        df_view = df_view[df_view["gap"] > 0]

    st.markdown('<div class="rgm-divider"></div>', unsafe_allow_html=True)

    # -----------------------------
    # Eingaben (Draft) – ohne Form
    # -----------------------------
    rendered_codes: list[str] = []
    draft = st.session_state.get("priorities_draft", {}) or {}

    if df_view.empty:
        st.info("Keine Dimensionen mit Handlungsbedarf (Gap > 0) in der aktuellen Filterauswahl.")
    else:
        for _, row in df_view.iterrows():
            code = str(row["code"])
            name_short = str(row["name_short"])
            gap = float(row["gap"])
            rendered_codes.append(code)

            prev = draft.get(code, {})
            prev_prio = prev.get("priority", "")
            prev_action = prev.get("action", "")
            prev_time = prev.get("timeframe", "")
            prev_resp = prev.get("responsible", "")

            try:
                default_index = PRIORITY_OPTIONS.index(prev_prio)
            except ValueError:
                default_index = 0

            label = f"{code} – {name_short} · Gap {gap:.2f}"
            with st.expander(label, expanded=(gap >= 1.0)):
                st.markdown(f"<div class='rgm-pill'>Gap (Soll–Ist): <b>{gap:.2f}</b> Reifegradstufen</div>", unsafe_allow_html=True)

                # Zeile 1: Priorität + Maßnahme
                r1c1, r1c2 = st.columns([1, 5], gap="large")
                with r1c1:
                    st.selectbox(
                        "Priorität",
                        options=PRIORITY_OPTIONS,
                        index=default_index,
                        key=f"prio_{code}",
                    )
                with r1c2:
                    measures_map = load_measures_map()
                    suggestions = measures_map.get(code, []) or []

                    # Eine Zeile: links das einzige Maßnahme-Feld, rechts das Icon
                    mcol, icol = st.columns([12, 1], gap="small")

                    with mcol:
                        st.text_input(
                            "Maßnahme",
                            value=prev_action,
                            key=f"action_{code}",
                            placeholder="z. B. Redaktionsleitfaden erstellen",
                        )

                    with icol:
                        if st.button(
                            "📋",
                            key=f"open_measures_{code}",
                            use_container_width=True,
                            disabled=not suggestions,
                            help="Vorschläge anzeigen",
                        ):
                            measure_dialog(code, suggestions)

                    # Speichern in Pool (dein bestehender Teil)
                    if st.session_state.get("share_measures_opt_in", False):
                        if st.button("➕ In Pool speichern…", key=f"save_pool_{code}"):
                            st.session_state["pending_pool_save"] = {
                                "code": code,
                                "text": normalize_measure_text(st.session_state.get(f"action_{code}", "")),
                            }
                    else:
                        st.caption("Speichern in den Vorschlags-Pool ist deaktiviert (oben „Nein“).")
        

                st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

                # Zeile 2: Verantwortlich + Zeitraum
                r2c1, r2c2 = st.columns([3, 2], gap="large")
                with r2c1:
                    st.text_input(
                        "Verantwortlich",
                        value=prev_resp,
                        key=f"resp_{code}",
                        placeholder="z. B. Christian Koch",
                    )
                with r2c2:
                    st.text_input(
                        "Zeitraum",
                        value=prev_time,
                        key=f"timeframe_{code}",
                        placeholder="z. B. Q1/2026",
                    )

        # Draft aus Widgets aktualisieren
        st.session_state["priorities_draft"] = collect_priorities_from_session(
            codes=rendered_codes,
            keep_existing=st.session_state.get("priorities_draft", {}),
        )
    
    pending = st.session_state.get("pending_pool_save")
    if pending:
        st.warning(
            f"Möchten Sie diese Maßnahme als Vorschlag für **{pending['code']}** speichern?\n\n"
            f"**{pending['text'] or '(leer)'}**\n\n"
            "⚠️ Es wird nur der Text aus „Maßnahme“ gespeichert. Bitte keine sensiblen Daten."
        )
        y, n = st.columns(2, gap="small")
        with y:
            if st.button("Ja, speichern", type="primary", use_container_width=True):
                try:
                    issue_no = github_create_measure_issue(pending["text"], pending["code"])
                    st.success(f"Gesendet (Issue #{issue_no}). Nach Verarbeitung erscheint es als Vorschlag.")
                except Exception as e:
                    st.error(f"Speichern fehlgeschlagen: {e}")
                st.session_state.pop("pending_pool_save", None)
                st.rerun()
        with n:
            if st.button("Abbrechen", use_container_width=True):
                st.session_state.pop("pending_pool_save", None)
                st.rerun()

    # Dirty-Check
    draft_now = st.session_state.get("priorities_draft", {}) or {}
    committed_now = st.session_state.get("priorities_committed", {}) or {}
    dirty = _stable_json(draft_now) != _stable_json(committed_now)

    # -----------------------------
    # Übernehmen + Hinweis
    # -----------------------------
    if st.button(
        "Priorisierungen übernehmen",
        type="primary",
        use_container_width=True,
        disabled=not dirty,
    ):
        st.session_state["priorities"] = copy.deepcopy(draft_now)
        st.session_state["priorities_committed"] = copy.deepcopy(draft_now)
        st.success("Priorisierungen wurden übernommen.")
        st.rerun()

    if dirty:
        st.warning(
            "Sie haben Priorisierungen geändert, die noch nicht übernommen wurden. "
            "Bitte zuerst „Priorisierungen übernehmen“ klicken, damit diese Werte verwendet werden."
        )

    st.markdown("---")

    # Navigation (einheitlich)
    left, right = st.columns([1, 1], gap="large")
    with left:
        if st.button("Zurück", use_container_width=True):
            st.session_state["nav_request"] = "Dashboard"
            st.rerun()

    with right:
        if st.button(
            "Weiter zur Gesamtübersicht",
            type="primary",
            use_container_width=True,
            disabled=dirty,
        ):
            st.session_state["nav_request"] = "Gesamtübersicht"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
