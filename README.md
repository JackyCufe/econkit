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

**一站式计量经济学实证分析工具**

专为中国经管类学生设计（本科 / 硕士 / 博士）| 无需写代码 | 一键生成学术级图表

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-red.svg)](https://streamlit.io/)
[![HuggingFace](https://img.shields.io/badge/🤗-HuggingFace%20Space-yellow)](https://huggingface.co/spaces/JackyCufe/econkit)
[![ModelScope](https://img.shields.io/badge/🤖-魔搭社区-blueviolet)](https://modelscope.cn/studios/JackyCufe/EconKit/summary)

**[🚀 在线体验（魔搭）](https://modelscope.cn/studios/JackyCufe/EconKit/summary)** · **[🚀 在线体验（HuggingFace）](https://huggingface.co/spaces/JackyCufe/econkit)** · **[📖 使用文档](#-分析流程建议)** · **[☕ 支持作者](https://ifdian.net/a/jackycufe)**

</div>

---

## ✨ 功能概览

| 模块 | 分析方法 |
|------|---------|
| 🔵 描述与诊断 | 描述统计、相关矩阵、正态性检验、VIF、异方差检验、自相关检验 |
| 🟡 基准回归 | OLS、个体/时间/双向固定效应、随机效应、Hausman 检验、面板单位根 |
| 🔴 因果推断 | DID（含平行趋势+1000次安慰剂）、交错DID、PSM、RDD、IV/2SLS、动态面板GMM |
| 🟢 稳健性检验 | Winsorize/缩尾、Bootstrap、安慰剂检验、剔除特殊样本 |
| 🟣 异质性与机制 | 分组回归、分位数回归、中介效应（Bootstrap）、调节效应 |

**🤖 智能推荐**：输入研究背景，自动匹配最合适的分析路径

---

## 🚀 快速开始

### 在线使用（推荐）

- 🤖 **魔搭社区（国内访问首选）**：https://modelscope.cn/studios/JackyCufe/EconKit/summary
- 🤗 **HuggingFace Space（国际版）**：https://huggingface.co/spaces/JackyCufe/econkit

### 本地运行

```bash
git clone https://github.com/JackyCufe/econkit.git
cd econkit
pip install -r requirements.txt
streamlit run app.py
```

浏览器打开 http://localhost:8501 即可使用

---

## 📊 数据格式要求

支持 **Excel / CSV**，面板数据长格式：

| firm_id | year | treat | post | did | tfp  | size  | lev  |
|---------|------|-------|------|-----|------|-------|------|
| 1       | 2010 | 0     | 0    | 0   | 2.15 | 10.23 | 0.32 |
| 1       | 2015 | 0     | 1    | 0   | 2.28 | 10.45 | 0.30 |
| 2       | 2010 | 1     | 0    | 0   | 2.33 | 11.10 | 0.45 |
| 2       | 2015 | 1     | 1    | 1   | 2.58 | 11.30 | 0.43 |

> 不确定格式？上传后可直接使用内置示例数据体验完整流程

---

## 🎯 分析流程建议

1. **首页** → 上传数据，检查数据结构
2. **智能引导** → 描述研究背景，获取方法推荐路径
3. **实证分析** → 按顺序执行各分析，实时查看图表
4. **下载报告** → 一键生成 PDF 汇总报告

---

## 📁 项目结构

```
econkit/
├── app.py                    # Streamlit 主入口
├── requirements.txt
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
└── ui/
    ├── pages/                # 四大页面
    └── components/           # 公共组件
```

---

## ☕ 支持作者

如果 EconKit 帮到了你，欢迎请我喝杯咖啡 ☕

**👉 [爱发电支持](https://ifdian.net/a/jackycufe)**

也欢迎点个 ⭐ Star，让更多同学发现这个工具！

---

## 📝 版本历史

- **v1.0.0** (2026-03-14) - MVP 版本发布，支持全套计量经济学分析方法

---

<div align="center">
<sub>EconKit 由 AI 辅助构建，适合学术研究参考使用。重要结论请咨询专业计量经济学家。</sub>
</div>
