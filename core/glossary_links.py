# core/glossary_links.py
from __future__ import annotations

import html
import re
import urllib.parse
from typing import Dict, Optional


def linkify_glossary(
    text: str,
    glossary: Dict[str, str],
    from_page: str,
    aid: Optional[str] = None,
) -> str:
    """
    Ersetzt Vorkommen von Glossar-Begriffen im Text durch Links.

    Wir nutzen Query-Params für Custom-Navigation:
      ?page=Glossar&g=<TERM>&from=<PAGE>&aid=<AID>

    Hinweis: pre-wrap, damit Newlines wie Excel wirken.
    """
    raw = text or ""
    if not raw.strip() or not glossary:
        return f'<div style="white-space: pre-wrap;">{html.escape(raw)}</div>'

    # längste Begriffe zuerst
    terms = [t for t in glossary.keys() if isinstance(t, str) and t.strip()]
    terms = sorted(terms, key=len, reverse=True)
    if not terms:
        return f'<div style="white-space: pre-wrap;">{html.escape(raw)}</div>'

    word_chars = r"A-Za-z0-9ÄÖÜäöüß_"

    parts = []
    for t in terms:
        esc = re.escape(t)
        # einfache Wortgrenzen (verhindert Matches mitten im Wort)
        if re.match(rf"^[{word_chars}]", t):
            esc = rf"(?<![{word_chars}]){esc}"
        if re.match(rf".*[{word_chars}]$", t):
            esc = rf"{esc}(?![{word_chars}])"
        parts.append(esc)

    try:
        pattern = re.compile("|".join(parts), flags=re.IGNORECASE)
    except Exception:
        return f'<div style="white-space: pre-wrap;">{html.escape(raw)}</div>'

    def repl(m: re.Match) -> str:
        term = m.group(0)
        term_q = urllib.parse.quote_plus(term)
        from_q = urllib.parse.quote_plus(from_page or "")
        aid_q = urllib.parse.quote_plus(aid) if aid else ""

        href = f"?page=Glossar&g={term_q}&from={from_q}"
        if aid_q:
            href += f"&aid={aid_q}"

        return (
            f'<a class="rgm-glossary-link" href="{href}" target="_self" rel="noopener noreferrer">'
            f"{html.escape(term)}"
            f"</a>"
        )

    # wir bauen HTML-safe zusammen: ersetze auf RAW, aber escape Stücke
    out = []
    last = 0
    for m in pattern.finditer(raw):
        s, e = m.start(), m.end()
        if s > last:
            out.append(html.escape(raw[last:s]))
        out.append(repl(m))
        last = e
    if last < len(raw):
        out.append(html.escape(raw[last:]))

    return f'<div style="white-space: pre-wrap;">{"".join(out)}</div>'
