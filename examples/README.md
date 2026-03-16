# EconKit 样例数据集与测试脚本

本目录包含 EconKit 的完整示例数据集、测试脚本和生成的分析报告，可直接用于功能验证和教学演示。

## 目录结构

```
examples/
├── 数据集
│   ├── test_data.csv         企业教育政策干预面板（50企业×6年，DID真实系数=0.20）
│   ├── data_health.csv       医疗补贴政策面板（300县×8年，DID真实系数=0.30）
│   ├── data_digital.csv      企业数字化转型面板（200企业×5年，含规模异质性）
│   └── data_rdd.csv          RDD断点回归专用（2000obs，断点处真实跳跃=1.50）
│
├── 脚本
│   ├── generate_datasets.py  生成全部测试数据集
│   ├── test_undergrad_full.py  本科生水平完整测试（29项）
│   └── test_masters_full.py    硕士研究生水平完整测试（34项）
│
└── 报告
    ├── undergrad_report.pdf  本科级别分析报告（866KB，29章节）
    └── masters_report.pdf    硕士级别分析报告（549KB，34章节）
```

## 快速开始

```bash
# 1. 重新生成数据集（可选，数据集已预置）
python examples/generate_datasets.py

# 2. 运行本科生水平测试
python examples/test_undergrad_full.py

# 3. 运行硕士研究生水平测试
python examples/test_masters_full.py
```

## 覆盖的分析方法

### 本科生水平（29项）
| 类别 | 方法 |
|------|------|
| 描述统计 | 描述统计、相关矩阵、正态性检验、VIF、异方差检验、自相关检验 |
| 基准回归 | OLS（普通/稳健SE）、面板FE/RE/TWFE、Hausman检验、单位根检验 |
| 因果推断 | 基础DID、TWFE-DID、平行趋势检验、安慰剂检验 |
| PSM | KNN匹配、核匹配、协变量平衡性检验（Love图）|
| RDD | 局部线性回归、最优带宽、McCrary密度检验 |
| IV/2SLS | 2SLS、弱工具变量检验、Wu-Hausman内生性检验、Sargan过度识别检验 |
| 稳健性 | Bootstrap置信区间、剔除特殊样本 |
| 异质性 | 分组回归、分位数回归、中介效应、调节效应 |

### 硕士研究生水平（34项）
| 类别 | 方法 |
|------|------|
| 进阶诊断 | Winsorize缩尾、条件数诊断、RESET检验、ARCH检验、面板平衡性 |
| 面板进阶 | 三模型联合对比、DK标准误（近似）、真正AB/BB GMM（pydynpd）、Chow检验 |
| DID进阶 | 渐进DID（Staggered）、DDD三重差分、DID敏感性分析 |
| IV进阶 | Stock-Yogo弱IV检验、LIML估计、多工具变量Sargan检验 |
| RDD进阶 | 带宽敏感性分析、多项式阶数对比、协变量平滑性检验 |
| PSM进阶 | 核匹配带宽敏感性、Love图SMD对比、IPW/IPTW估计ATE |
| 稳健性进阶 | 聚类Bootstrap（1000次）、替换被解释变量 |
| 机制进阶 | 分组Wald系数差异检验、中介+调节效应进阶版 |
| ML辅助 | LASSO变量选择、Ridge回归 |
| 综合 | AIC/BIC模型选择、5模型并排发表级三线表 |

## 依赖包

```
pip install linearmodels pydynpd scikit-learn scipy statsmodels reportlab matplotlib
```
