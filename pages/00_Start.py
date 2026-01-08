# pages/00_Start.py
from __future__ import annotations

from pathlib import Path
import base64
import html
import streamlit as st

from core.state import init_session_state
from core.model_loader import load_tool_meta

TU_GREEN = "#639A00"
TU_ORANGE = "#CA7406"

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


def _mail_icon_link(email: str) -> str:
    """
    Kleines Mail-Icon (SVG) als mailto-Link.
    """
    safe_email = html.escape((email or "").strip())
    if "@" not in safe_email:
        return ""
    return f"""
<a href="mailto:{safe_email}" title="{safe_email}" aria-label="E-Mail an {safe_email}">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
       stroke-linecap="round" stroke-linejoin="round">
    <path d="M4 4h16v16H4z"></path>
    <path d="M22 6l-10 7L2 6"></path>
  </svg>
</a>
"""

def _name_with_mail(name: str, email: str | None) -> str:
    safe_name = html.escape(name or "-")
    if email and isinstance(email, str) and "@" in email:
        return f'<span class="rgm-mail"><span>{safe_name}</span>{_mail_icon_link(email)}</span>'
    return safe_name

def _inject_start_css() -> None:
    st.markdown(
        f"""
        <style>
          /* =========================================
             TU Corporate Design (nur Akzentfarben!)
             -> NICHT --rgm-* überschreiben, sonst Darkmode kaputt
             ========================================= */
          :root {{
            --tu-green: {TU_GREEN};
            --tu-orange: {TU_ORANGE};
          }}

          /* Links im TU-Grün */
          a {{ color: var(--tu-green) !important; }}

          /* Primary Buttons (TU-Grün / Hover Orange) */
          div.stButton > button,
          button[kind="primary"],
          button[data-testid="baseButton-primary"] {{
            background: var(--tu-green) !important;
            border: 1px solid var(--tu-green) !important;
            color: #ffffff !important;
            border-radius: 10px !important;
            font-weight: 650 !important;
          }}
          div.stButton > button:hover,
          button[kind="primary"]:hover,
          button[data-testid="baseButton-primary"]:hover {{
            background: var(--tu-orange) !important;
            border-color: var(--tu-orange) !important;
          }}
          div.stButton > button:focus {{
            outline: none !important;
            box-shadow: 0 0 0 3px rgba(99,154,0,0.25) !important;
          }}

          /* =========================================
             Layout: Platz für Footer (responsiv)
             ========================================= */
          .block-container{{
            padding-top: 2.5rem;
            --rgm-footer-h: 124px;
            padding-bottom: calc(var(--rgm-footer-h) + env(safe-area-inset-bottom) + 18px);
          }}

          @media (max-width: 1200px){{ .block-container{{ --rgm-footer-h: 112px; }} }}
          @media (max-width: 900px){{ .block-container{{ --rgm-footer-h: 102px; }} }}
          @media (max-width: 600px){{ .block-container{{ --rgm-footer-h: 96px; }} }}

          /* =========================================
             Footer fixed unten (Logos)
             ========================================= */
          .rgm-footer{{
            position: fixed;
            left: 0;
            right: 0;
            bottom: 0;

            background: var(--rgm-footer-bg, #ffffff);
            padding: 10px 22px;

            border-top: 1px solid var(--rgm-border, rgba(0,0,0,0.08));
            z-index: 9999;
          }}

          .rgm-footer-inner{{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 28px;
            flex-wrap: nowrap;

            overflow-x: auto;
            overflow-y: hidden;
            -webkit-overflow-scrolling: touch;

            padding: 0 18px;
            box-sizing: border-box;

            scrollbar-width: thin;
          }}

          .rgm-footer-inner.is-overflow{{ justify-content: flex-start; }}

          .rgm-footer-inner::after{{
            content: "";
            flex: 0 0 18px;
          }}

          .rgm-footer-inner .rgm-footer-logo{{
            flex: 0 0 auto;
            display: inline-flex;
            align-items: center;
            justify-content: center;

            background: #ffffff;
            border: 1px solid rgba(0,0,0,0.10);
            border-radius: 14px;

            padding: 10px 14px;
            text-decoration: none;
            color: inherit;

            box-shadow: 0 6px 18px rgba(0,0,0,0.20);
          }}

          .rgm-footer-inner .rgm-footer-logo:hover{{ opacity: 0.94; }}

          .rgm-footer-inner .rgm-footer-logo img{{
            height: 64px;
            width: auto;
            object-fit: contain;
            display: block;
          }}

          @media (max-width: 1200px){{
            .rgm-footer{{ padding: 9px 18px; }}
            .rgm-footer-inner{{ gap: 18px; }}
            .rgm-footer-inner .rgm-footer-logo img{{ height: 58px; }}
          }}

          @media (max-width: 900px){{
            .rgm-footer{{ padding: 8px 16px; }}
            .rgm-footer-inner{{ gap: 14px; justify-content: flex-start; }}
            .rgm-footer-inner .rgm-footer-logo img{{ height: 52px; }}
            .rgm-footer-inner .rgm-footer-logo{{ padding: 6px 8px; }}
          }}

          @media (max-width: 600px){{
            .rgm-footer{{ padding: 8px 12px; }}
            .rgm-footer-inner .rgm-footer-logo img{{ height: 48px; }}
          }}

          .rgm-footer-inner::-webkit-scrollbar{{ height: 6px; }}
          .rgm-footer-inner::-webkit-scrollbar-thumb{{ border-radius: 999px; }}

          /* ===== Meta-Block / Mail Icon ===== */
          .rgm-meta-top {{
            background: var(--rgm-card-bg, #ffffff);
            border: 1px solid var(--rgm-border, rgba(0,0,0,0.08));
            border-radius: 14px;
            padding: 14px 16px;
            max-width: 520px;
            margin-top: 10px;
            margin-bottom: 34px;
            font-size: 14px;
            line-height: 1.7;
            color: var(--rgm-text, #111);
          }}

          .rgm-meta-top .row {{ display: flex; gap: 14px; }}
          .rgm-meta-top .k {{ width: 150px; font-weight: 600; }}

          .rgm-btn-wrap {{ margin-top: 22px; }}

          .rgm-mail {{ display: inline-flex; align-items: center; gap: 8px; }}
          .rgm-mail a {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 26px;
            height: 26px;
            border-radius: 8px;
            border: 1px solid var(--rgm-border, rgba(0,0,0,0.10));
            text-decoration: none;
            color: inherit;
            opacity: 0.95;
          }}
          .rgm-mail a:hover {{
            opacity: 1;
            transform: translateY(-0.5px);
            border-color: var(--tu-green);
          }}
          .rgm-mail svg {{ width: 15px; height: 15px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <script>
    (function(){
      if (window.__rgmFooterCenteringInstalled) return;
      window.__rgmFooterCenteringInstalled = true;

      function updateFooterOverflow(){
        const el = document.querySelector(".rgm-footer-inner");
        if (!el) return;
        const overflow = el.scrollWidth > el.clientWidth + 1;
        el.classList.toggle("is-overflow", overflow);
      }

      window.addEventListener("load", updateFooterOverflow);
      window.addEventListener("resize", updateFooterOverflow);

      const obs = new MutationObserver(updateFooterOverflow);
      obs.observe(document.body, { childList: true, subtree: true });

      setTimeout(updateFooterOverflow, 50);
    })();
    </script>
        """,
        unsafe_allow_html=True,
    )


def main():
    init_session_state()
    _inject_start_css()

    st.title("Reifegradmodell für die Technische Dokumentation")

    st.caption("Fragebasiertes Tool zur Bewertung und Weiterentwicklung der technischen Dokumentation.")

    # --- Meta laden ---
    try:
        meta = load_tool_meta()
    except Exception as e:
        st.error("Metadaten konnten nicht geladen werden.")
        st.exception(e)
        meta = {}

    support_name = meta.get("support_name", "Mouaiad Aldebs")
    support_email = meta.get("support_email", "mouaiad.aldebs@tu-dortmund.de")



    # title = meta.get("title", "Reifegradmodell für die Technische Dokumentation")
    created_by = meta.get("created_by", "Christian Koch")
    created_by_email = meta.get("created_by_email", "christian4.koch@tu-dortmund.de")
    version = meta.get("version", "2.0")
    last_change = meta.get("last_change", "03.12.2025")
    credit = meta.get("credit", "Victor Wolf")
    credit_email = meta.get("credit_email")  # optional

    # Logos (aus /images) – gecached
    logo_unidoku = _img_b64(str(IMAGES_DIR / "logo_unidoku.png"))
    logo_niro = _img_b64(str(IMAGES_DIR / "NIRO.png"))
    logo_tu = _img_b64(str(IMAGES_DIR / "tu.png"))
    logo_igf = _img_b64(str(IMAGES_DIR / "IGF-RGB.png"))
    logo_bmwe = _img_b64(str(IMAGES_DIR / "bmwi.png"))
    logo_bvl = _img_b64(str(IMAGES_DIR / "BVL_Logo.png"))

    # Metadaten oben (Name/E-Mail klickbar)
    st.markdown(
        f"""
<div class="rgm-meta-top">
  <div class="row"><div class="k">Erstellt durch:</div><div>{_name_with_mail(created_by, created_by_email)}</div></div>
  <div class="row"><div class="k">Version:</div><div>{html.escape(str(version))}</div></div>
  <div class="row"><div class="k">Letzte Änderung:</div><div>{html.escape(str(last_change))}</div></div>
  <div class="row"><div class="k">Credit:</div><div>{_name_with_mail(credit, credit_email)}</div></div>
  <div class="row"><div class="k">Technischer Support:</div><div>{_name_with_mail(support_name, support_email)}</div></div>
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

    LOGO_URLS = {
      "UniDoku": "https://ips.mb.tu-dortmund.de/forschen-beraten/forschungsprojekte/unidoku/",
      "TU": "https://www.tu-dortmund.de/",
      "NIRO": "https://ni-ro.de/",
      "IGF": "https://www.igf-foerderung.de/",
      "BMWE": "https://www.bundeswirtschaftsministerium.de/Navigation/DE/Home/home.html",
      "BVL": "https://www.bvl.de/",
    }

    def img_tag(b64: str, alt: str) -> str:
      url = LOGO_URLS.get(alt)
      img_html = f'<img src="data:image/png;base64,{b64}" alt="{html.escape(alt)}"/>'
  
      if url:
          return (
              f'<a class="rgm-footer-logo" href="{html.escape(url)}" '
              f'target="_blank" rel="noopener noreferrer">{img_html}</a>'
          )
  
      # fallback ohne Link
      return f'<span class="rgm-footer-logo">{img_html}</span>'


    logo_tags = []
    if logo_unidoku:
        logo_tags.append(img_tag(logo_unidoku, "UniDoku"))
    if logo_tu:
        logo_tags.append(img_tag(logo_tu, "TU"))
    if logo_niro:
        logo_tags.append(img_tag(logo_niro, "NIRO"))
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