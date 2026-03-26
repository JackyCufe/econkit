[![中文](https://img.shields.io/badge/README-中文-red)](README.zh.md)

---
title: EconKit 计量经济学分析工具
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: "1.32.0"
app_file: app.py
pinned: true
license: MIT
tags:
  - econometrics
  - panel-data
  - did
  - causal-inference
  - streamlit
  - python
---

<div align="center">

# 📊 EconKit

**All-in-one Econometrics Toolkit | 一站式计量经济学实证分析工具**

Designed for Chinese economics & management students (undergraduate thesis / master's / PhD) | No coding required | One-click academic charts and PDF reports

专为中国经管类学生设计（本科毕设 / 硕博论文）| 无需写代码 | 一键生成学术级图表与 PDF 报告

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-red.svg)](https://streamlit.io/)
[![HuggingFace](https://img.shields.io/badge/🤗-HuggingFace%20Space-yellow)](https://huggingface.co/spaces/JackyCufe/econkit)
[![ModelScope](https://img.shields.io/badge/🤖-魔搭社区-blueviolet)](https://modelscope.cn/studios/JackyCufe/EconKit/summary)
[![Stars](https://img.shields.io/github/stars/JackyCufe/econkit?style=social)](https://github.com/JackyCufe/econkit)

**[🚀 Live Demo — ModelScope (China)](https://modelscope.cn/studios/JackyCufe/EconKit/summary)** · **[🚀 Live Demo — HuggingFace (Global)](https://huggingface.co/spaces/JackyCufe/econkit)** · **[☕ Support](https://ifdian.net/a/jackycufe)**

> **Keywords**: DID Difference-in-Differences | PSM Propensity Score Matching | RDD Regression Discontinuity | IV Instrumental Variables | Panel Fixed Effects | Dynamic Panel GMM | Mediation | Moderation

</div>

---

## ✨ Features

| Module | Methods |
|--------|---------|
| 🔵 Descriptive & Diagnostics | Descriptive stats, correlation matrix, normality test, VIF, heteroskedasticity, autocorrelation |
| 🟡 Baseline Regression | OLS, individual/time/two-way FE, RE, Hausman test, panel unit root |
| 🔴 Causal Inference | DID (parallel trend + 1000x placebo), staggered DID, PSM, RDD, IV/2SLS, dynamic panel GMM |
| 🟢 Robustness | Winsorize, Bootstrap, placebo test, sample exclusion |
| 🟣 Heterogeneity & Mechanism | Subgroup regression, quantile regression, mediation (Bootstrap), moderation |

**🤖 Smart Recommendation**: Describe your research background, get a matched analysis path automatically.

---

## 🚀 Quick Start

### Online (Recommended — no install)

- 🤖 **ModelScope (China)**: https://modelscope.cn/studios/JackyCufe/EconKit/summary
- 🤗 **HuggingFace (Global)**: https://huggingface.co/spaces/JackyCufe/econkit

### Local

```bash
git clone https://github.com/JackyCufe/econkit.git
cd econkit
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## 📊 Data Format

Supports **Excel / CSV**, panel data in long format:

| firm_id | year | treat | post | did | tfp  | size  | lev  |
|---------|------|-------|------|-----|------|-------|------|
| 1       | 2010 | 0     | 0    | 0   | 2.15 | 10.23 | 0.32 |
| 2       | 2015 | 1     | 1    | 1   | 2.58 | 11.30 | 0.43 |

> Unsure about format? Built-in sample data lets you explore the full workflow first.

---

## ✅ Are the Results Reliable?

EconKit uses academically validated Python libraries:

| Library | Purpose |
|---------|---------|
| `statsmodels` | OLS, panel regression, time series |
| `linearmodels` | FE, RE, IV/2SLS |
| `econml` | DID, causal inference |
| `scikit-learn` | PSM propensity score estimation |
| `rdrobust` | RDD |

**Replication verified**: Classic DID results reproduced with publicly available panel data, coefficient error within 0.01. For critical conclusions, consult a professional econometrician.

---

## ☕ Support

If EconKit helped you, consider buying me a coffee ☕

**👉 [Support on Aifadian](https://ifdian.net/a/jackycufe)**

A ⭐ Star also helps more students discover this tool!

---

## 📝 Changelog

- **v1.0.0** (2026-03-14) — MVP release, full econometrics method suite
