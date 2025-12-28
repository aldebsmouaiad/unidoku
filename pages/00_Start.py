# pages/00_Start.py
from __future__ import annotations

from pathlib import Path
import base64
import html
import streamlit as st

from core.state import init_session_state
from core.model_loader import load_tool_meta

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"


@st.cache_data(show_spinner=False)
def _img_b64(path_str: str) -> str | None:
    """
    Liest ein Bild einmalig von Disk und cached das Base64-Ergebnis.
    Streamlit rerunnt häufig -> ohne Cache würde jedes Mal erneut gelesen.
    """
    path = Path(path_str)
    if not path.exists():
        return None
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def _mailto_html(name: str, email: str | None) -> str:
    """
    Klickbarer Mail-Link als HTML.
    Wichtig: Wir sind in einem HTML-Block, daher kein Markdown verwenden.
    """
    safe_name = html.escape(name or "-")
    if email and isinstance(email, str) and "@" in email:
        safe_email = html.escape(email.strip())
        # color: inherit -> passt in Light/Dark
        return f'<a href="mailto:{safe_email}" style="text-decoration:none;color:inherit;">{safe_name}</a>'
    return safe_name


def _inject_start_css() -> None:
    """
    Nur Layout-/Komponenten-CSS für die Startseite.
    WICHTIG: Keine :root-Variablen mehr setzen (kommt global aus app.py).
    """
    st.markdown(
        """
        <style>
          .block-container {
            padding-top: 2.5rem;
            padding-bottom: 7rem; /* Platz für fixed Footer */
          }

          /* Footer fix unten (nur Logos) */
          .rgm-footer {
            position: fixed;
            left: 0;
            right: 0;
            bottom: 0;

            background: var(--rgm-footer-bg, #ffffff);
            padding: 14px 28px 18px 28px;

            border-top: 1px solid var(--rgm-border, rgba(0,0,0,0.08));
            z-index: 9999;
          }

          .rgm-footer-inner {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 50px;
            flex-wrap: wrap;
          }

          .rgm-footer-inner .logo-wrap {
            background: var(--rgm-logo-bg, transparent);
            border: 1px solid var(--rgm-logo-border, transparent);
            border-radius: 12px;
            padding: 6px 10px;
            display: flex;
            align-items: center;
          }

          .rgm-footer-inner img {
            height: 80px;
            width: auto;
            object-fit: contain;
            display: block;
          }

          /* Metablock oben: größer & luftiger */
          .rgm-meta-top {
            margin-top: 10px;
            margin-bottom: 34px;
            font-size: 14px;
            line-height: 1.7;
            color: var(--rgm-text, #111);
          }

          .rgm-meta-top .row {
            display: flex;
            gap: 14px;
          }

          .rgm-meta-top .k {
            width: 150px;
            font-weight: 600;
          }

          .rgm-btn-wrap { margin-top: 22px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    init_session_state()
    _inject_start_css()

    # --- Meta laden ---
    try:
        meta = load_tool_meta()
    except Exception as e:
        st.error("Metadaten konnten nicht geladen werden.")
        st.exception(e)
        meta = {}

    title = meta.get("title", "Reifegradmodell für die Technische Dokumentation")
    created_by = meta.get("created_by", "Christian Koch")
    created_by_email = meta.get("created_by_email", "christian4.koch@tu-dortmund.de")
    version = meta.get("version", "2.0")
    last_change = meta.get("last_change", "03.12.2025")
    credit = meta.get("credit", "Victor Wolf")
    credit_email = meta.get("credit_email")  # optional

    # Logos (aus /images) – gecached
    logo_unidoku = _img_b64(str(IMAGES_DIR / "logo_unidoku.png"))
    logo_ips = _img_b64(str(IMAGES_DIR / "IPS-Logo-RGB.png"))
    logo_igf = _img_b64(str(IMAGES_DIR / "IGF-RGB.png"))
    logo_bmwe = _img_b64(str(IMAGES_DIR / "bmwi.png"))
    logo_bvl = _img_b64(str(IMAGES_DIR / "BVL_Logo.png"))

    # Titel aus Meta-JSON
    st.markdown(f"## {html.escape(str(title))}")

    # Metadaten oben (Name/E-Mail klickbar)
    st.markdown(
        f"""
<div class="rgm-meta-top">
  <div class="row"><div class="k">Erstellt durch:</div><div>{_mailto_html(created_by, created_by_email)}</div></div>
  <div class="row"><div class="k">Version:</div><div>{html.escape(str(version))}</div></div>
  <div class="row"><div class="k">Letzte Änderung:</div><div>{html.escape(str(last_change))}</div></div>
  <div class="row"><div class="k">Credit:</div><div>{_mailto_html(credit, credit_email)}</div></div>
</div>
        """,
        unsafe_allow_html=True,
    )

    # Button „Weiter zu Einführung“
    st.markdown('<div class="rgm-btn-wrap">', unsafe_allow_html=True)
    if st.button("Weiter zu Einführung", type="primary", use_container_width=True):
        st.session_state["nav_request"] = "Einführung"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    def img_tag(b64: str, alt: str) -> str:
        return f'<div class="logo-wrap"><img src="data:image/png;base64,{b64}" alt="{html.escape(alt)}"/></div>'

    logo_tags = []
    if logo_unidoku:
        logo_tags.append(img_tag(logo_unidoku, "UniDoku"))
    if logo_ips:
        logo_tags.append(img_tag(logo_ips, "IPS"))
    if logo_igf:
        logo_tags.append(img_tag(logo_igf, "IGF"))
    if logo_bmwe:
        logo_tags.append(img_tag(logo_bmwe, "BMWE"))
    if logo_bvl:
        logo_tags.append(img_tag(logo_bvl, "BVL"))

    # Footer nur mit Logos
    st.markdown(
        f"""
<div class="rgm-footer">
  <div class="rgm-footer-inner">
    {''.join(logo_tags)}
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
