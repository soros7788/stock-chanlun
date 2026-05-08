from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ai.llm_client import set_llm_model
from stores.local_json import load_settings, save_settings

router = APIRouter()


@router.get("/health", tags=["系统"])
def health_check():
    return {"status": "ok", "version": "0.2.0"}


@router.get("/api/settings", tags=["系统"])
def get_settings():
    return load_settings()


@router.put("/api/settings", tags=["系统"])
def update_settings(model: str = Query(..., description="AI 模型 deepseek / gemini")):
    if model not in ("deepseek", "gemini"):
        raise HTTPException(status_code=400, detail="只支持 deepseek 和 gemini")
    set_llm_model(model)
    s = load_settings()
    s["ai_model"] = model
    save_settings(s)
    return {"ai_model": model, "ok": True}
