---
title: EconKit 计量经济学分析工具
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: true
license: mit
---

# 📊 EconKit - 计量经济学在线分析工具

> 一站式实证分析平台，专为中国经管类硕博生设计

## ✨ 功能概览

| 模块 | 分析方法 |
|------|---------|
| 🔵 描述与诊断 | 描述统计、相关矩阵、正态性检验、VIF、异方差、自相关 |
| 🟡 基准回归 | OLS、FE/RE/TWFE、Hausman 检验、面板单位根 |
| 🔴 因果推断 | DID（含平行趋势+安慰剂）、PSM、RDD、IV/2SLS、GMM |
| 🟢 稳健性检验 | Winsorize、Bootstrap、安慰剂检验、剔除特殊样本 |
| 🟣 异质性与机制 | 分组回归、分位数回归、中介效应、调节效应 |

## 🚀 快速开始

### 环境要求

- Python 3.11+
- pip

### 安装依赖

```bash
cd /Users/jacky/.openclaw/workspace/econkit
pip install -r requirements.txt
```

### 启动应用

```bash
streamlit run app.py
```

应用将在浏览器中自动打开（默认地址：http://localhost:8501）

## 📁 目录结构

```
econkit/
├── app.py                    # Streamlit 主入口
├── requirements.txt          # Python 依赖
├── README.md
├── core/
│   ├── data_loader.py        # 数据上传、清洗、验证
│   ├── smart_recommender.py  # 智能方法推荐引擎
│   └── report_generator.py  # PDF 报告生成
├── analysis/
│   ├── descriptive.py        # 描述统计 + 诊断检验
│   ├── panel_regression.py   # OLS/FE/RE/TWFE/Hausman
│   ├── causal_did.py         # DID + 平行趋势 + 安慰剂
│   ├── causal_psm.py         # PSM 倾向得分匹配
│   ├── causal_rdd.py         # RDD 断点回归
│   ├── causal_iv.py          # IV/2SLS + 内生性检验
│   ├── robustness.py         # 稳健性检验
│   └── heterogeneity.py      # 异质性 + 中介 + 调节
├── ui/
│   ├── pages/
│   │   ├── home.py           # 首页 + 数据上传
│   │   ├── smart_guide.py    # 智能引导页
│   │   ├── analysis.py       # 分析执行页
│   │   └── report.py         # 报告下载页
│   └── components/
│       ├── sidebar.py        # 侧边栏导航
│       ├── variable_selector.py
│       └── chart_display.py
└── assets/
    ├── style.css             # 自定义样式
    └── academic_theme.py     # 学术图表主题
```

## 📊 数据格式要求

面板数据格式（长格式）：

| firm_id | year | treat | post | did  | tfp  | size  | lev   |
|---------|------|-------|------|------|------|-------|-------|
| 1       | 2010 | 0     | 0    | 0    | 2.15 | 10.23 | 0.32  |
| 1       | 2015 | 0     | 1    | 0    | 2.28 | 10.45 | 0.30  |
| 2       | 2010 | 1     | 0    | 0    | 2.33 | 11.10 | 0.45  |
| 2       | 2015 | 1     | 1    | 1    | 2.58 | 11.30 | 0.43  |

**必要列**：
- 个体ID（如 `firm_id`、`id`、`entity`）
- 时间变量（如 `year`、`time`）
- 数值型分析变量

**DID 特需**：`treat`（0/1）、`post`（0/1）、`did`（=treat×post）

## 🎯 分析流程建议

1. **首页** → 上传数据，检查数据结构
2. **智能引导** → 描述研究背景，获取方法推荐
3. **实证分析** → 按推荐顺序执行各分析
4. **下载报告** → 生成 PDF 汇总报告

## ⚙️ 主要依赖

- `streamlit` - Web UI 框架
- `statsmodels` - OLS、检验统计量
- `linearmodels` - 面板模型、IV/2SLS
- `scikit-learn` - PSM 倾向得分匹配
- `scipy` - 统计检验
- `matplotlib` / `seaborn` - 学术图表
- `reportlab` - PDF 报告生成
- `pingouin` - 额外统计检验

## 📝 版本历史

- v1.0.0 (2026-03-14) - MVP 版本发布

---

*EconKit 由 AI 辅助构建，适合学术研究参考使用。重要结论请咨询专业计量经济学家。*
