[![English](https://img.shields.io/badge/README-English-blue)](README.md)

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

浏览器打开 http://localhost:8501 即可使用。

---

## 📊 数据格式要求

支持 **Excel / CSV**，面板数据长格式：

| firm_id | year | treat | post | did | tfp  | size  | lev  |
|---------|------|-------|------|-----|------|-------|------|
| 1       | 2010 | 0     | 0    | 0   | 2.15 | 10.23 | 0.32 |
| 2       | 2015 | 1     | 1    | 1   | 2.58 | 11.30 | 0.43 |

> 不确定格式？上传后可直接使用内置示例数据体验完整流程。

---

## ✅ 结果可信吗？

EconKit 底层使用经过学术界广泛验证的 Python 库（statsmodels / linearmodels / econml / scikit-learn / rdrobust），计算逻辑本身可信。

**实测复现验证**：用连享会公开面板数据复现经典 DID 论文系数，误差在 0.01 以内。重要结论仍建议咨询专业计量经济学家。

---

## ☕ 支持作者

如果 EconKit 帮到了你，欢迎请我喝杯咖啡 ☕

**👉 [爱发电支持](https://ifdian.net/a/jackycufe)**

也欢迎点个 ⭐ Star，让更多同学发现这个工具！

---

<div align="center">
<sub>EconKit 由 AI 辅助构建，适合学术研究参考使用。重要结论请咨询专业计量经济学家。</sub>
</div>
