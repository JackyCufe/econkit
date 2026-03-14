"""
智能方法推荐引擎
根据用户描述的研究背景，自动推荐计量经济学分析方法路径
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MethodRecommendation:
    """分析方法推荐结果"""
    method_id:   str
    method_name: str
    category:    str            # causal / panel / robust / hetero / describe
    reason:      str
    priority:    int            # 1=必须 2=推荐 3=可选
    sub_steps:   list[str] = field(default_factory=list)


# ── 关键词映射规则 ─────────────────────────────────────────────────────────────
_KEYWORD_RULES: list[dict] = [
    # 因果推断 - DID
    {
        "keywords": ["政策", "冲击", "自然实验", "改革", "实施", "处理组", "对照组",
                     "双重差分", "did", "difference"],
        "methods": [
            MethodRecommendation(
                method_id="did_basic", method_name="DID 双重差分",
                category="causal", priority=1,
                reason="研究描述涉及政策冲击或自然实验，DID 是标准因果识别策略",
                sub_steps=["基准DID回归", "平行趋势检验", "安慰剂检验(1000次置换)"]
            ),
            MethodRecommendation(
                method_id="twfe", method_name="双向固定效应 (TWFE)",
                category="panel", priority=1,
                reason="DID 通常配合个体+时间双向固定效应以控制不随时间/个体变化的干扰因素",
                sub_steps=["个体固定效应", "时间固定效应", "聚类标准误"]
            ),
        ]
    },
    # 交错DID
    {
        "keywords": ["交错", "渐进", "staggered", "不同时间", "各地时间不同", "分期"],
        "methods": [
            MethodRecommendation(
                method_id="staggered_did", method_name="交错DID (Callaway-Sant'Anna)",
                category="causal", priority=1,
                reason="政策实施时间不统一时，经典TWFE存在偏误，需用交错DID修正",
                sub_steps=["估计群组平均处理效应(ATT(g,t))", "汇总动态效应", "与TWFE对比"]
            ),
        ]
    },
    # 内生性 / IV / GMM
    {
        "keywords": ["内生", "双向因果", "遗漏变量", "工具变量", "iv", "2sls",
                     "gmm", "动态", "滞后", "arellano"],
        "methods": [
            MethodRecommendation(
                method_id="iv_2sls", method_name="IV / 2SLS 工具变量",
                category="causal", priority=1,
                reason="存在内生性问题时，需要工具变量进行因果识别",
                sub_steps=["弱工具变量检验(F>10)", "Wu-Hausman内生性检验",
                           "Sargan过度识别检验", "第一阶段回归"]
            ),
            MethodRecommendation(
                method_id="gmm", method_name="动态面板 GMM (Arellano-Bond)",
                category="causal", priority=2,
                reason="动态面板或无合适工具变量时，GMM 利用滞后变量作为内部工具",
                sub_steps=["差分GMM", "系统GMM", "AR(2)检验", "Sargan/Hansen检验"]
            ),
        ]
    },
    # 断点回归 RDD
    {
        "keywords": ["断点", "资格线", "阈值", "cutoff", "rdd", "得分", "分数",
                     "discontinuity", "regression discontinuity"],
        "methods": [
            MethodRecommendation(
                method_id="rdd", method_name="RDD 断点回归",
                category="causal", priority=1,
                reason="存在明确分配规则断点时，RDD 是准实验识别的首选方法",
                sub_steps=["最优带宽选择(CCT/IK)", "局部线性回归",
                           "McCrary密度检验", "带宽敏感性分析"]
            ),
        ]
    },
    # PSM 倾向得分匹配
    {
        "keywords": ["匹配", "psm", "倾向得分", "选择偏误", "样本匹配",
                     "propensity", "matching"],
        "methods": [
            MethodRecommendation(
                method_id="psm", method_name="PSM 倾向得分匹配",
                category="causal", priority=1,
                reason="存在样本选择偏差时，PSM 构造可比对照组",
                sub_steps=["估计倾向得分(Logit)", "K近邻匹配",
                           "核匹配", "标准化偏差检验", "ATT估计"]
            ),
        ]
    },
    # 面板数据 FE/RE
    {
        "keywords": ["面板", "panel", "固定效应", "随机效应", "fe", "re",
                     "hausman", "个体效应", "时间效应"],
        "methods": [
            MethodRecommendation(
                method_id="panel_fe", method_name="固定效应模型 (FE)",
                category="panel", priority=1,
                reason="面板数据分析需要控制个体固定效应以消除遗漏变量偏误",
                sub_steps=["个体固定效应", "时间固定效应", "双向固定效应",
                           "Hausman检验(FE vs RE)", "聚类标准误"]
            ),
        ]
    },
    # 机制分析 - 中介效应
    {
        "keywords": ["机制", "路径", "中介", "传导", "mediati", "pathway", "渠道"],
        "methods": [
            MethodRecommendation(
                method_id="mediation", method_name="中介效应分析",
                category="hetero", priority=1,
                reason="研究关注作用机制路径，需要中介效应分析",
                sub_steps=["Baron-Kenny三步法", "Bootstrap置信区间(1000次)",
                           "直接效应/间接效应分解", "Sobel检验"]
            ),
        ]
    },
    # 调节效应
    {
        "keywords": ["调节", "异质性", "交互", "moderat", "interact",
                     "不同群体", "分组"],
        "methods": [
            MethodRecommendation(
                method_id="moderation", method_name="调节效应分析",
                category="hetero", priority=1,
                reason="研究关注条件效应，需要调节效应分析",
                sub_steps=["交互项回归", "简单斜率图", "Johnson-Neyman区域"]
            ),
            MethodRecommendation(
                method_id="subgroup", method_name="分组回归",
                category="hetero", priority=2,
                reason="比较不同子群体的效应大小差异",
                sub_steps=["子样本分组回归", "组间系数差异检验(Chow Test)"]
            ),
        ]
    },
    # 稳健性检验
    {
        "keywords": ["稳健", "robust", "安慰剂", "缩尾", "bootstrap",
                     "敏感性", "替换变量"],
        "methods": [
            MethodRecommendation(
                method_id="robustness", method_name="稳健性检验",
                category="robust", priority=2,
                reason="学术论文必须进行稳健性检验以增强结论可信度",
                sub_steps=["Winsorize缩尾处理", "安慰剂检验",
                           "替换核心变量", "Bootstrap自助法", "剔除特殊样本"]
            ),
        ]
    },
]


# ── 默认推荐（描述统计和基础诊断总是推荐）─────────────────────────────────────
_DEFAULT_METHODS: list[MethodRecommendation] = [
    MethodRecommendation(
        method_id="descriptive", method_name="描述统计分析",
        category="describe", priority=1,
        reason="任何实证分析的第一步，了解数据基本特征",
        sub_steps=["均值/标准差/分位数", "相关矩阵", "正态性检验", "VIF多重共线性"]
    ),
    MethodRecommendation(
        method_id="ols", method_name="OLS 基准回归",
        category="panel", priority=1,
        reason="建立基准模型，为后续因果识别提供对比基准",
        sub_steps=["OLS回归（含稳健SE）", "异方差检验", "自相关检验"]
    ),
]


# ── 主推荐函数 ─────────────────────────────────────────────────────────────────
def recommend_methods(description: str) -> list[MethodRecommendation]:
    """
    根据研究描述推荐分析方法

    Args:
        description: 用户输入的研究背景描述（中英文均可）

    Returns:
        按优先级排序的方法推荐列表
    """
    desc_lower = description.lower()
    matched: dict[str, MethodRecommendation] = {}

    for rule in _KEYWORD_RULES:
        if any(kw in desc_lower for kw in rule["keywords"]):
            for method in rule["methods"]:
                if method.method_id not in matched:
                    matched[method.method_id] = method

    # 始终包含默认方法
    results = list(_DEFAULT_METHODS)
    for method in matched.values():
        if method.method_id not in {m.method_id for m in results}:
            results.append(method)

    # 按优先级排序
    results.sort(key=lambda m: (m.priority, m.category))
    return results


def get_method_categories() -> dict[str, list[dict]]:
    """返回所有可用分析方法的分类目录（用于UI展示）"""
    return {
        "🔵 描述与诊断": [
            {"id": "descriptive",    "name": "描述统计"},
            {"id": "correlation",    "name": "相关矩阵"},
            {"id": "normality",      "name": "正态性检验"},
            {"id": "vif",            "name": "多重共线性（VIF）"},
            {"id": "heterosked",     "name": "异方差检验"},
            {"id": "autocorr",       "name": "自相关检验"},
        ],
        "🟡 基准回归": [
            {"id": "ols",            "name": "OLS 普通最小二乘"},
            {"id": "panel_fe",       "name": "固定效应（FE）"},
            {"id": "panel_re",       "name": "随机效应（RE）"},
            {"id": "twfe",           "name": "双向固定效应（TWFE）"},
            {"id": "hausman",        "name": "Hausman 检验"},
            {"id": "unit_root",      "name": "面板单位根检验"},
        ],
        "🔴 因果推断": [
            {"id": "did_basic",      "name": "DID 双重差分"},
            {"id": "staggered_did",  "name": "交错DID（C&S）"},
            {"id": "psm",            "name": "PSM 倾向得分匹配"},
            {"id": "rdd",            "name": "RDD 断点回归"},
            {"id": "iv_2sls",        "name": "IV / 2SLS"},
            {"id": "gmm",            "name": "动态面板 GMM"},
        ],
        "🟢 稳健性检验": [
            {"id": "robustness",     "name": "稳健性检验套件"},
            {"id": "bootstrap",      "name": "Bootstrap 自助法"},
            {"id": "placebo",        "name": "安慰剂检验"},
        ],
        "🟣 异质性与机制": [
            {"id": "subgroup",       "name": "分组回归"},
            {"id": "quantile_reg",   "name": "分位数回归"},
            {"id": "mediation",      "name": "中介效应"},
            {"id": "moderation",     "name": "调节效应"},
            {"id": "mod_mediation",  "name": "有调节的中介"},
        ],
    }
