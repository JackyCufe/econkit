# EconKit 自动化测试

本目录包含 EconKit 的核心模块自动化测试脚本和最新测试报告。

## 文件说明

| 文件 | 说明 |
|------|------|
| `run_tests.py` | 全模块自动化测试脚本（4个数据集 × 12个模块，共43项） |
| `test_report.md` | 最新一次运行生成的测试报告 |
| `README.md` | 本文档 |

## 测试数据

测试数据集均位于 [`../examples/`](../examples/) 目录，`run_tests.py` 自动读取，无需手动配置。

## 运行测试

```bash
# 在仓库根目录执行
python tests/run_tests.py
```

运行完成后，`tests/test_report.md` 会被覆盖更新。

## 覆盖范围

- 4个数据集：企业教育政策DID / 医疗补贴政策DID / 企业数字化转型DID / RDD断点回归
- 12个分析模块：描述统计、OLS、面板FE、基础DID、TWFE、平行趋势、安慰剂检验、PSM、IV/2SLS、分位数回归、中介效应、调节效应

## 最新结果

**43/43 通过（0失败，0警告）** — 详见 [`test_report.md`](./test_report.md)
