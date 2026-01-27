# pages/00_Start.py
from __future__ import annotations

from pathlib import Path
import base64
import html as _html

import streamlit as st

from core.state import init_session_state
from core.model_loader import load_tool_meta

TU_GREEN = "#639A00"
TU_ORANGE = "#CA7406"
TD_BLUE = "#2F3DB8"
OG_ORANGE = "#F28C28"

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"


@st.cache_data(show_spinner=False)
def _img_b64(path_str: str) -> str | None:
    path = Path(path_str)
    if not path.exists():
        return None
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def _mail_icon_link(email: str | None) -> str:
    safe_email = _html.escape((email or "").strip())
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


def _name_with_mail(name: str | None, email: str | None) -> str:
    safe_name = _html.escape(name or "-")
    if email and isinstance(email, str) and "@" in email:
        return f'<span class="rgm-mail"><span>{safe_name}</span>{_mail_icon_link(email)}</span>'
    return safe_name


def _inject_start_css(dark: bool) -> None:
    # Farben robust je nach Darkmode
    border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.10)"
    soft_bg = "rgba(255,255,255,0.06)" if dark else "rgba(0,0,0,0.03)"
    hover_bg = "rgba(255,255,255,0.08)" if dark else "rgba(0,0,0,0.045)"
    shadow = "0 12px 28px rgba(0,0,0,0.40)" if dark else "0 10px 24px rgba(0,0,0,0.06)"
    card_bg = "var(--rgm-card-bg, #111)" if dark else "var(--rgm-card-bg, #ffffff)"
    text_col = "var(--rgm-text, rgba(250,250,250,0.92))" if dark else "var(--rgm-text, #111)"

    footer_bg = "rgba(16,16,16,0.92)" if dark else "#ffffff"
    footer_border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.08)"

    css = r"""
<style>
  :root{
    --tu-green: __TU_GREEN__;
    --tu-orange: __TU_ORANGE__;
  }

  /* Links im TU-Grün */
  a { color: var(--tu-green) !important; }

  /* Primary Buttons (TU-Grün / Hover Orange) */
  div.stButton > button,
  button[kind="primary"],
  button[data-testid="baseButton-primary"]{
    background: var(--tu-green) !important;
    border: 1px solid var(--tu-green) !important;
    color: #ffffff !important;
    border-radius: 10px !important;
    font-weight: 650 !important;
  }
  div.stButton > button:hover,
  button[kind="primary"]:hover,
  button[data-testid="baseButton-primary"]:hover{
    background: var(--tu-orange) !important;
    border-color: var(--tu-orange) !important;
  }
  div.stButton > button:focus{
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(99,154,0,0.25) !important;
  }

  /* Layout: Platz für Footer */
  .block-container{
    padding-top: 2.3rem;
    --rgm-footer-h: 108px;
    padding-bottom: calc(var(--rgm-footer-h) + env(safe-area-inset-bottom) + 20px);
    max-width: 1200px;
    margin: 0 auto;
  }
  @media (max-width: 900px){ .block-container{ --rgm-footer-h: 100px; } }
  @media (max-width: 600px){ .block-container{ --rgm-footer-h: 94px; } }

  /* Page */
  .rgm-page{
    max-width: 1200px;
    margin: 0 auto;
  }

  /* HERO */
  .rgm-hero{
    background: __CARD_BG__;
    border: 1px solid __BORDER__;
    border-radius: 16px;
    padding: 18px 18px 14px 18px;
    box-shadow: __SHADOW__;
  }

  .rgm-hero-top{
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
  }

  .rgm-h1{
    font-size: 34px;
    font-weight: 900;
    line-height: 1.12;
    margin: 0 0 8px 0;
    color: __TEXT__;
  }

  .rgm-lead{
    font-size: 15px;
    line-height: 1.75;
    margin: 0;
    color: __TEXT__;
    opacity: 0.92;
    max-width: 880px;
  }

  .rgm-pill{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px solid __BORDER__;
    background: __SOFT_BG__;
    color: __TEXT__;
    font-size: 13px;
    font-weight: 750;
    white-space: nowrap;
  }
  .rgm-dot{
    width: 10px;
    height: 10px;
    border-radius: 999px;
    background: var(--tu-green);
    box-shadow: 0 0 0 3px rgba(99,154,0,0.18);
  }

  .rgm-accent-line{
    height: 3px;
    width: 140px;
    border-radius: 999px;
    margin: 10px 0 14px 0;
    background: linear-gradient(90deg, __TD_BLUE__, __OG_ORANGE__);
  }

  /* GRID */
  .rgm-grid{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin-top: 16px;
  }
  @media (max-width: 900px){
    .rgm-grid{ grid-template-columns: 1fr; }
  }

  .rgm-card{
    background: __CARD_BG__;
    border: 1px solid __BORDER__;
    border-radius: 16px;
    padding: 14px 16px;
    box-shadow: __SHADOW__;
    min-height: 96px;
  }

  .rgm-card-h{
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 0 0 8px 0;
  }

  .rgm-ico{
    width: 34px;
    height: 34px;
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border: 1px solid __BORDER__;
    background: __SOFT_BG__;
    color: __TEXT__;
  }
  .rgm-ico svg{ width: 18px; height: 18px; }

  .rgm-card-title{
    font-weight: 900;
    font-size: 15px;
    color: __TEXT__;
    margin: 0;
  }

  .rgm-card-text{
    margin: 0;
    color: __TEXT__;
    opacity: 0.90;
    font-size: 13.5px;
    line-height: 1.65;
  }

  /* META */
  .rgm-meta{
    margin-top: 16px;
    background: __CARD_BG__;
    border: 1px solid __BORDER__;
    border-radius: 16px;
    padding: 14px 16px;
    box-shadow: __SHADOW__;
  }
  .rgm-meta-row{
    display: grid;
    grid-template-columns: 180px 1fr;
    gap: 14px;
    padding: 8px 0;
    border-bottom: 1px solid __BORDER__;
  }
  .rgm-meta-row:last-child{ border-bottom: none; }

  .rgm-k{
    font-weight: 850;
    color: __TEXT__;
    opacity: 0.92;
    font-size: 13.5px;
  }
  .rgm-v{
    color: __TEXT__;
    font-size: 13.5px;
  }

  /* Mail mini */
  .rgm-mail{ display: inline-flex; align-items: center; gap: 8px; }
  .rgm-mail a{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    border-radius: 9px;
    border: 1px solid __BORDER__;
    text-decoration: none;
    color: inherit;
    opacity: 0.95;
  }
  .rgm-mail a:hover{
    opacity: 1;
    transform: translateY(-0.5px);
    border-color: var(--tu-green);
  }
  .rgm-mail svg{ width: 15px; height: 15px; }

  .rgm-btn-wrap{ margin-top: 14px; margin-bottom: 10px; }

  /* FOOTER (Logos) */
  .rgm-footer{
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;

    background: __FOOTER_BG__;
    padding: 10px 18px;

    border-top: 1px solid __FOOTER_BORDER__;
    z-index: 9999;
    backdrop-filter: blur(8px);
  }

  .rgm-footer-inner{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 18px;
    flex-wrap: nowrap;

    overflow-x: auto;
    overflow-y: hidden;
    -webkit-overflow-scrolling: touch;

    padding: 0 12px;
    box-sizing: border-box;

    scrollbar-width: thin;
  }

  .rgm-footer-inner.is-overflow{ justify-content: flex-start; }

  .rgm-footer-logo{
    flex: 0 0 auto;
    display: inline-flex;
    align-items: center;
    justify-content: center;

    background: rgba(255,255,255,0.92);
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 14px;

    padding: 8px 10px;
    text-decoration: none;
    color: inherit;

    box-shadow: 0 10px 22px rgba(0,0,0,0.10);
  }

  .rgm-footer-logo:hover{ opacity: 0.96; transform: translateY(-0.5px); }

  .rgm-footer-logo img{
    height: 52px;
    width: auto;
    object-fit: contain;
    display: block;
  }

  @media (max-width: 900px){
    .rgm-h1{ font-size: 28px; }
    .rgm-footer-logo img{ height: 46px; }
    .rgm-meta-row{ grid-template-columns: 150px 1fr; }
  }
  @media (max-width: 600px){
    .rgm-footer-logo img{ height: 42px; }
  }

  .rgm-footer-inner::-webkit-scrollbar{ height: 6px; }
  .rgm-footer-inner::-webkit-scrollbar-thumb{ border-radius: 999px; }
</style>
"""
    css = (
        css.replace("__TU_GREEN__", TU_GREEN)
        .replace("__TU_ORANGE__", TU_ORANGE)
        .replace("__TD_BLUE__", TD_BLUE)
        .replace("__OG_ORANGE__", OG_ORANGE)
        .replace("__BORDER__", border)
        .replace("__SOFT_BG__", soft_bg)
        .replace("__HOVER_BG__", hover_bg)
        .replace("__SHADOW__", shadow)
        .replace("__CARD_BG__", card_bg)
        .replace("__TEXT__", text_col)
        .replace("__FOOTER_BG__", footer_bg)
        .replace("__FOOTER_BORDER__", footer_border)
    )
    st.markdown(css, unsafe_allow_html=True)

    # Footer Centering Helper
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
        """.strip(),
        unsafe_allow_html=True,
    )


def _feature_card(title: str, text: str, icon_svg: str) -> str:
    return f"""
<div class="rgm-card">
  <div class="rgm-card-h">
    <span class="rgm-ico" aria-hidden="true">{icon_svg}</span>
    <div class="rgm-card-title">{_html.escape(title)}</div>
  </div>
  <p class="rgm-card-text">{_html.escape(text)}</p>
</div>
""".strip()

def main() -> None:
    init_session_state()
    dark = bool(st.session_state.get("ui_dark_mode", st.session_state.get("dark_mode", False)))
    _inject_start_css(dark)

    # --- Meta laden ---
    try:
        meta = load_tool_meta()
    except Exception as e:
        st.error("Metadaten konnten nicht geladen werden.")
        st.exception(e)
        meta = {}

    support_name = meta.get("support_name", "Mouaiad Aldebs")
    support_email = meta.get("support_email", "mouaiad.aldebs@tu-dortmund.de")

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
        img_html = f'<img src="data:image/png;base64,{b64}" alt="{_html.escape(alt)}"/>'
        if url:
            return (
                f'<a class="rgm-footer-logo" href="{_html.escape(url)}" '
                f'target="_blank" rel="noopener noreferrer">{img_html}</a>'
            )
        return f'<span class="rgm-footer-logo">{img_html}</span>'

    logo_tags: list[str] = []
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

    # Icons
    ICON_LIST = """
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <line x1="8" y1="6" x2="21" y2="6"></line>
  <line x1="8" y1="12" x2="21" y2="12"></line>
  <line x1="8" y1="18" x2="21" y2="18"></line>
  <circle cx="4" cy="6" r="1"></circle>
  <circle cx="4" cy="12" r="1"></circle>
  <circle cx="4" cy="18" r="1"></circle>
</svg>
"""
    ICON_CHART = """
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M3 3v18h18"></path>
  <path d="M7 14l4-4 4 3 5-7"></path>
</svg>
"""
    ICON_TARGET = """
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="9"></circle>
  <circle cx="12" cy="12" r="5"></circle>
  <circle cx="12" cy="12" r="1"></circle>
</svg>
"""
    ICON_FILE = """
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
  <path d="M14 2v6h6"></path>
</svg>
"""
    st.markdown(
        f"""
    <div class="rgm-hero">
      <div class="rgm-hero-top">
        <div>
          <div class="rgm-h1">Reifegradmodell für die Technische Dokumentation</div>
          <div class="rgm-accent-line"></div>
          <p class="rgm-lead">
            Fragebasiertes Tool zur Bewertung und Weiterentwicklung der technischen Dokumentation – mit Auswertung,
            Priorisierung und Exportfunktionen (PDF/CSV).
          </p>
        </div>
        <div class="rgm-pill"><span class="rgm-dot"></span>Version {_html.escape(str(version))} • Stand {_html.escape(str(last_change))}</div>
      </div>
    </div>
        """.strip(),
        unsafe_allow_html=True,
    )

    # Reihenfolge: Erhebung → Ergebnis → Priorisierung → Export
    CARD1 = _feature_card(
        "Erhebung",
        "Beantworten Sie die Fragen je Subdimension und ermitteln Sie den Reifegrad stufenweise.",
        ICON_LIST,
    )

    CARD2 = _feature_card(
        "Ergebnis",
        "Transparente Ist-/Soll-Sicht mit visueller Auswertung und strukturierter Maßnahmenübersicht.",
        ICON_CHART,
    )

    CARD3 = _feature_card(
        "Priorisierung",
        "Bewerten Sie Maßnahmen nach Wirkung und Umsetzbarkeit – Fokus auf die wichtigsten Hebel.",
        ICON_TARGET,
    )

    CARD4 = _feature_card(
        "Export",
        "Exportieren Sie Ergebnisse zur Dokumentation und Weitergabe (PDF/CSV).",
        ICON_FILE,
    )

    st.markdown(
        f"""
    <div class="rgm-grid">
      {CARD1}
      {CARD2}
      {CARD3}
      {CARD4}
    </div>
    """.strip(),
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
<div class="rgm-meta">
  <div class="rgm-meta-row"><div class="rgm-k">Erstellt durch</div><div class="rgm-v">{_name_with_mail(created_by, created_by_email)}</div></div>
  <div class="rgm-meta-row"><div class="rgm-k">Credit</div><div class="rgm-v">{_name_with_mail(credit, credit_email)}</div></div>
  <div class="rgm-meta-row"><div class="rgm-k">Technischer Support</div><div class="rgm-v">{_name_with_mail(support_name, support_email)}</div></div>
</div>
        """.strip(),
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)

    if st.button("Weiter zu Einführung", type="primary", use_container_width=True):
        st.session_state["nav_request"] = "Einführung"
        st.rerun()

    st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)

    # Footer Logos (fixed)
    st.markdown(
        f"""
<div class="rgm-footer">
  <div class="rgm-footer-inner">
    {''.join(logo_tags)}
  </div>
</div>
        """.strip(),
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
