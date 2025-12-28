# core/persist.py
from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

import streamlit as st


# ============================================================
# Query-Params: EINHEITLICH über Wrapper (niemals direkt mischen)
# ============================================================
_QP_MODE_KEY = "_rgm_qp_mode"  # "prod" oder "exp"


def _qp_mode() -> str:
    """
    Entscheidet EINMAL pro Session, ob wir:
    - "prod" = st.query_params
    - "exp"  = st.experimental_get_query_params / st.experimental_set_query_params
    nutzen.

    Wichtig: Wir fangen StreamlitAPIException ab, falls bereits die andere API
    verwendet wurde, und bleiben dann konsistent.
    """
    mode = st.session_state.get(_QP_MODE_KEY)
    if mode in ("prod", "exp"):
        return mode

    # Prefer prod API, wenn vorhanden und nicht im Konflikt
    if hasattr(st, "query_params"):
        try:
            _ = st.query_params  # kann Exception werfen, wenn exp bereits genutzt wurde
            st.session_state[_QP_MODE_KEY] = "prod"
            return "prod"
        except Exception:
            pass

    st.session_state[_QP_MODE_KEY] = "exp"
    return "exp"


def qp_get(name: str) -> str | None:
    """
    Gibt ersten Wert eines Query-Params zurück.
    """
    mode = _qp_mode()

    if mode == "prod":
        v = st.query_params.get(name)
        if isinstance(v, list):
            return v[0] if v else None
        return v

    # exp
    params = st.experimental_get_query_params()
    v = params.get(name)
    if isinstance(v, list):
        return v[0] if v else None
    return v


def qp_set(name: str, value: str) -> None:
    """
    Setzt/überschreibt einen Query-Param.
    """
    mode = _qp_mode()

    if mode == "prod":
        try:
            st.query_params[name] = value
        except Exception:
            try:
                st.query_params.update({name: value})
            except Exception:
                pass
        return

    # exp
    try:
        params = st.experimental_get_query_params()
        params[name] = [value]
        st.experimental_set_query_params(**params)
    except Exception:
        pass


def qp_del(name: str) -> None:
    """
    Löscht einen Query-Param.
    """
    mode = _qp_mode()

    if mode == "prod":
        try:
            if name in st.query_params:
                del st.query_params[name]
        except Exception:
            # fallback: "None" setzen (je nach Version)
            try:
                st.query_params.update({name: None})
            except Exception:
                pass
        return

    # exp
    try:
        params = st.experimental_get_query_params()
        if name in params:
            params.pop(name, None)
            st.experimental_set_query_params(**params)
    except Exception:
        pass


def qp_keys() -> list[str]:
    mode = _qp_mode()
    if mode == "prod":
        try:
            return list(st.query_params.keys())
        except Exception:
            return []
    try:
        return list(st.experimental_get_query_params().keys())
    except Exception:
        return []


def clear_query_params_keep_aid(aid: str | None = None) -> None:
    """
    Entfernt nur unsere App-Keys, lässt Streamlit-interne Keys in Ruhe.
    AID bleibt erhalten.
    """
    aid = str(aid or qp_get("aid") or st.session_state.get("_rgm_aid") or "").strip()

    # Keys, die wir in Links verwenden / die Navigation triggern
    drop_keys = [
        "page",
        "g",
        "glossary",
        "term",
        "from",
        "ret",
        "ret_step",
        "ret_idx",
        "ret_code",
    ]

    for k in drop_keys:
        qp_del(k)

    if aid:
        qp_set("aid", aid)


# -----------------------------
# File-basierter Snapshot Store
# -----------------------------
def _state_dir() -> Path:
    """
    Persistente Ablage für Snapshots.
    - Windows: %TEMP%/rgm_state
    - Linux: /tmp/rgm_state
    Kann per ENV RGM_STATE_DIR überschrieben werden.
    """
    base = os.getenv("RGM_STATE_DIR")
    if base:
        p = Path(base)
    else:
        p = Path(tempfile.gettempdir()) / "rgm_state"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _snap_path(aid: str) -> Path:
    safe = "".join(ch for ch in (aid or "") if ch.isalnum())[:32] or "unknown"
    return _state_dir() / f"rgm_{safe}.json"


def get_or_create_aid() -> str:
    """
    Stabile Assessment-ID (aid) in URL + Session-State.
    """
    aid = (qp_get("aid") or st.session_state.get("_rgm_aid") or "").strip()
    if not aid:
        aid = uuid.uuid4().hex[:12]

    aid = str(aid)
    st.session_state["_rgm_aid"] = aid
    qp_set("aid", aid)
    return aid


def save(aid: str | None = None) -> None:
    """
    Snapshot speichern (file-basiert, atomar).
    """
    aid = str(aid or get_or_create_aid()).strip()
    if not aid:
        return

    meta = st.session_state.get("meta")
    if not isinstance(meta, dict):
        meta = {}

    snap: dict[str, Any] = {
        "schema": "rgm_snapshot_v2",
        "updated_at": int(time.time()),
        "aid": aid,
        "answers": dict(st.session_state.get("answers", {}) or {}),
        "meta": dict(meta),
        "dimension_targets": dict(st.session_state.get("dimension_targets", {}) or {}),
        "priorities": dict(st.session_state.get("priorities", {}) or {}),
        "global_target_level": float(st.session_state.get("global_target_level", 3.0) or 3.0),
        "erhebung_step": int(st.session_state.get("erhebung_step", 0) or 0),
        "erhebung_dim_idx": int(st.session_state.get("erhebung_dim_idx", 0) or 0),
        "erhebung_dim_idx_ui": int(st.session_state.get("erhebung_dim_idx_ui", 0) or 0),
        "erhebung_own_target_defined": bool(st.session_state.get("erhebung_own_target_defined", False)),
        "nav_page": st.session_state.get("nav_page", None),
    }

    path = _snap_path(aid)
    tmp = path.with_suffix(".tmp")

    try:
        tmp.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)  # atomar auf den meisten OS
    except Exception:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass


def restore(aid: str | None = None) -> None:
    """
    Snapshot wiederherstellen.
    - answers/meta/targets/priorities: nur wenn aktuell leer/fehlt
    - scalars: nur wenn Key fehlt
    """
    aid = str(aid or get_or_create_aid()).strip()
    if not aid:
        return

    path = _snap_path(aid)
    if not path.exists():
        return

    try:
        snap = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return

    if not isinstance(snap, dict):
        return

    # answers: nur wenn aktuell leer/ungültig
    cur_answers = st.session_state.get("answers")
    if not isinstance(cur_answers, dict) or len(cur_answers) == 0:
        saved_answers = snap.get("answers", {})
        if isinstance(saved_answers, dict):
            st.session_state["answers"] = dict(saved_answers)

    # meta: merge, bevorzuge bestehende nicht-leere Werte
    saved_meta = snap.get("meta")
    if isinstance(saved_meta, dict):
        if "meta" not in st.session_state or not isinstance(st.session_state.get("meta"), dict):
            st.session_state["meta"] = dict(saved_meta)
        else:
            for k, v in saved_meta.items():
                if k not in st.session_state["meta"] or st.session_state["meta"].get(k) in ("", None):
                    st.session_state["meta"][k] = v

    # dimension_targets / priorities: wenn aktuell leer
    for key in ["dimension_targets", "priorities"]:
        saved = snap.get(key)
        cur = st.session_state.get(key)
        if isinstance(saved, dict) and (not isinstance(cur, dict) or len(cur) == 0):
            st.session_state[key] = dict(saved)

    # scalar defaults (nur wenn nicht vorhanden)
    for key in [
        "global_target_level",
        "erhebung_step",
        "erhebung_dim_idx",
        "erhebung_dim_idx_ui",
        "erhebung_own_target_defined",
        "nav_page",
    ]:
        if key not in st.session_state and key in snap:
            st.session_state[key] = snap.get(key)


def rerun_with_save(aid: str | None = None) -> None:
    """
    Vor st.rerun() immer speichern (wichtig bei Navigation).
    """
    save(aid)
    st.rerun()
