"""
EconKit 国际化支持
用法：from i18n import t
     t("key")           → 返回当前语言对应文字
     t("key", n=3)      → 支持 format 参数
"""
from __future__ import annotations


def get_lang() -> str:
    """获取当前语言（从 streamlit session_state）"""
    try:
        import streamlit as st
        return st.session_state.get("lang", "zh")
    except Exception:
        return "zh"


def t(key: str, **kwargs) -> str:
    """
    翻译函数

    Args:
        key:    语言包 key
        kwargs: 格式化参数（如 n=3, rows=100）

    Returns:
        翻译后的文字，找不到 key 时返回 key 本身
    """
    lang = get_lang()
    try:
        if lang == "en":
            from i18n.en import STRINGS
        else:
            from i18n.zh import STRINGS
        text = STRINGS.get(key, key)
    except Exception:
        text = key

    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text
