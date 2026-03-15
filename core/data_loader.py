"""
数据上传、清洗、验证模块
支持 CSV / Excel 格式，自动检测面板数据结构
"""
from __future__ import annotations

import io
import warnings
from typing import Optional

import numpy as np
import pandas as pd


# ── 常量 ──────────────────────────────────────────────────────────────────────
MAX_FILE_MB   = 50
REQUIRED_COLS = {"id", "year", "time", "entity", "firm_id", "code", "province"}
ID_CANDIDATES = ["firm_id", "id", "entity", "code", "province", "county"]
TIME_CANDIDATES = ["year", "time", "date", "period", "t"]


# ── 主加载函数 ─────────────────────────────────────────────────────────────────
def load_dataframe(file_obj: io.BytesIO, filename: str) -> pd.DataFrame:
    """
    从上传文件对象加载 DataFrame
    支持 .csv / .xlsx / .xls
    """
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "csv":
        df = _load_csv(file_obj)
    elif ext in {"xlsx", "xls"}:
        df = _load_excel(file_obj, ext)
    else:
        raise ValueError(f"不支持的文件格式：{ext}，请上传 CSV 或 Excel 文件")

    df = _basic_clean(df)
    return df


def _load_csv(file_obj: io.BytesIO) -> pd.DataFrame:
    """尝试多种编码加载 CSV"""
    for encoding in ("utf-8", "gbk", "utf-8-sig", "latin-1"):
        try:
            file_obj.seek(0)
            return pd.read_csv(file_obj, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("CSV 文件编码无法识别，请转存为 UTF-8 格式")


def _load_excel(file_obj: io.BytesIO, ext: str) -> pd.DataFrame:
    """加载 Excel 文件"""
    engine = "openpyxl" if ext == "xlsx" else "xlrd"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return pd.read_excel(file_obj, engine=engine)


def _basic_clean(df: pd.DataFrame) -> pd.DataFrame:
    """基础清洗：列名规范化、去除全空行"""
    # 列名：去除空格、转小写（保留中文列名原样）
    df.columns = [
        str(c).strip().replace(" ", "_") if str(c).isascii() else str(c).strip()
        for c in df.columns
    ]
    # 去除全空行
    df = df.dropna(how="all").reset_index(drop=True)
    return df


# ── 面板结构检测 ──────────────────────────────────────────────────────────────
def detect_panel_structure(df: pd.DataFrame) -> dict:
    """
    自动检测面板数据的个体变量和时间变量
    返回：{"id_col": str, "time_col": str, "n_entities": int, "n_periods": int}
    """
    cols_lower = {c.lower(): c for c in df.columns}

    id_col   = _find_col(cols_lower, ID_CANDIDATES)
    time_col = _find_col(cols_lower, TIME_CANDIDATES)

    result: dict = {
        "id_col":     id_col,
        "time_col":   time_col,
        "n_entities": df[id_col].nunique() if id_col else None,
        "n_periods":  df[time_col].nunique() if time_col else None,
        "n_rows":     len(df),
        "columns":    list(df.columns),
    }
    return result


def _find_col(cols_lower: dict[str, str], candidates: list[str]) -> Optional[str]:
    """在列名字典中按候选列表顺序查找匹配列"""
    for c in candidates:
        if c in cols_lower:
            return cols_lower[c]
    return None


# ── 数据验证 ──────────────────────────────────────────────────────────────────
def validate_panel_data(
    df: pd.DataFrame,
    id_col: str,
    time_col: str,
) -> dict:
    """
    验证面板数据质量，返回诊断报告
    """
    issues: list[str] = []
    warnings_list: list[str] = []

    # 基础检查
    if id_col not in df.columns:
        issues.append(f"个体变量列 '{id_col}' 不存在")
    if time_col not in df.columns:
        issues.append(f"时间变量列 '{time_col}' 不存在")

    if issues:
        return {"valid": False, "issues": issues, "warnings": warnings_list, "stats": {}}

    # 面板平衡性
    panel_counts = df.groupby(id_col)[time_col].count()
    is_balanced  = panel_counts.nunique() == 1
    if not is_balanced:
        warnings_list.append("面板数据不平衡（各个体观测期数不同）")

    # 缺失值
    missing_pct = df.isnull().mean() * 100
    high_missing = missing_pct[missing_pct > 20].to_dict()
    if high_missing:
        for col, pct in high_missing.items():
            warnings_list.append(f"列 '{col}' 缺失率 {pct:.1f}%")

    # 重复观测
    dup_count = df.duplicated(subset=[id_col, time_col]).sum()
    if dup_count > 0:
        issues.append(f"存在 {dup_count} 条重复的 (个体, 时间) 观测")

    # 数值列统计
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()

    stats = {
        "n_obs":        len(df),
        "n_entities":   df[id_col].nunique(),
        "n_periods":    df[time_col].nunique(),
        "is_balanced":  is_balanced,
        "missing_pct":  missing_pct.to_dict(),
        "numeric_cols": numeric_cols,
        "cat_cols":     [c for c in df.columns
                         if c not in numeric_cols and c not in [id_col, time_col]],
    }

    return {
        "valid":    len(issues) == 0,
        "issues":   issues,
        "warnings": warnings_list,
        "stats":    stats,
    }


# ── 数据预处理 ────────────────────────────────────────────────────────────────
def preprocess_data(
    df: pd.DataFrame,
    id_col: str,
    time_col: str,
    fill_na_method: str = "none",
    winsorize_pct: float = 0.0,
    drop_missing_cols: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    数据预处理：缺失值处理、缩尾处理、删除特定列缺失行

    Args:
        df: 原始 DataFrame
        id_col: 个体列
        time_col: 时间列
        fill_na_method: "none" / "mean" / "median" / "ffill"
        winsorize_pct: 缩尾百分比（0~0.5），0 表示不缩尾
        drop_missing_cols: 指定这些列有缺失时删除整行
    """
    df = df.copy()
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    feature_cols = [c for c in numeric_cols if c not in [id_col, time_col]]

    # 缺失值处理
    if fill_na_method == "mean":
        df[feature_cols] = df[feature_cols].fillna(df[feature_cols].mean())
    elif fill_na_method == "median":
        df[feature_cols] = df[feature_cols].fillna(df[feature_cols].median())
    elif fill_na_method == "ffill":
        df = df.sort_values([id_col, time_col])
        df[feature_cols] = df.groupby(id_col)[feature_cols].ffill()

    # 删除指定列缺失行
    if drop_missing_cols:
        valid_cols = [c for c in drop_missing_cols if c in df.columns]
        if valid_cols:
            df = df.dropna(subset=valid_cols)

    # 缩尾处理
    if 0 < winsorize_pct < 0.5:
        df = _winsorize_dataframe(df, feature_cols, winsorize_pct)

    df = df.reset_index(drop=True)
    return df


def _winsorize_dataframe(
    df: pd.DataFrame,
    cols: list[str],
    pct: float,
) -> pd.DataFrame:
    """对指定列做 Winsorize 缩尾处理"""
    for col in cols:
        lo = df[col].quantile(pct)
        hi = df[col].quantile(1 - pct)
        df[col] = df[col].clip(lo, hi)
    return df


# ── 样本数据生成 ──────────────────────────────────────────────────────────────
def generate_sample_data() -> pd.DataFrame:
    """
    生成用于演示的标准面板数据（200家企业，2010-2020年）
    包含 DID、FE、RDD、PSM 等所有分析需要的变量
    """
    rng = np.random.default_rng(42)
    n_firms = 200
    years   = list(range(2010, 2021))
    treat_year = 2015
    true_effect = 0.15

    firms = pd.DataFrame({
        "firm_id":  range(1, n_firms + 1),
        "treat":    rng.binomial(1, 0.5, n_firms),
        "size":     rng.normal(10, 2, n_firms).round(2),
        "age":      rng.integers(5, 30, n_firms),
        "lev":      rng.uniform(0.1, 0.8, n_firms).round(3),
        "roa":      rng.normal(0.05, 0.03, n_firms).round(4),
        "province": rng.choice(["北京", "上海", "广东", "浙江", "江苏"], n_firms),
        "industry": rng.choice(["制造", "服务", "科技"], n_firms),
        "score":    rng.uniform(40, 80, n_firms).round(1),  # RDD运行变量
    })

    rows = []
    for _, firm in firms.iterrows():
        firm_fe = rng.normal(0, 0.3)
        for year in years:
            post = int(year >= treat_year)
            did_effect = true_effect if (firm["treat"] == 1 and post == 1) else 0
            time_trend = (year - 2010) * 0.02
            tfp = (2.0 + firm_fe + time_trend
                   + 0.05 * firm["size"]
                   - 0.3 * firm["lev"]
                   + did_effect
                   + rng.normal(0, 0.1))
            rows.append({
                "firm_id":  int(firm["firm_id"]),
                "year":     year,
                "treat":    int(firm["treat"]),
                "post":     post,
                "did":      int(firm["treat"]) * post,
                "tfp":      round(float(tfp), 4),
                "ln_tfp":   round(float(np.log(max(tfp, 0.1))), 4),
                "size":     float(firm["size"]),
                "age":      int(firm["age"]),
                "lev":      float(firm["lev"]),
                "roa":      float(firm["roa"]),
                "province": firm["province"],
                "industry": firm["industry"],
                "score":    float(firm["score"]),
            })

    return pd.DataFrame(rows)
