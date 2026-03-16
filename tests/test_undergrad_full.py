import matplotlib
matplotlib.use('Agg')

import warnings
warnings.filterwarnings('ignore')

import sys
import os
import traceback

sys.path.insert(0, '/Users/jacky/.openclaw/workspace/econkit')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ─── 全局状态 ───────────────────────────────────────────────────────────────
RESULTS = []       # list of dicts: {status, name, details}
SECTIONS = []      # PDF report sections
FIGS_DIR = '/tmp/econkit_figs'
os.makedirs(FIGS_DIR, exist_ok=True)

PASS_COUNT = 0
FAIL_COUNT = 0
WARN_COUNT = 0


def record(name, status, details='', fig=None, table_headers=None, table_rows=None, note=''):
    global PASS_COUNT, FAIL_COUNT, WARN_COUNT
    status_str = status.upper()
    if status_str == 'PASS':
        PASS_COUNT += 1
        sym = '✅ PASS'
    elif status_str == 'FAIL':
        FAIL_COUNT += 1
        sym = '❌ FAIL'
    else:
        WARN_COUNT += 1
        sym = '⚠️  WARN'
    print(f'  [{sym}] {name}')
    if details:
        for line in str(details).split('\n')[:5]:
            print(f'         {line}')
    RESULTS.append({'status': status_str, 'name': name, 'details': details})
    SECTIONS.append({
        'title': name,
        'content': str(details),
        'table_headers': table_headers,
        'table_rows': table_rows,
        'figure': fig,
        'note': note,
    })


def save_fig(fig, name):
    path = os.path.join(FIGS_DIR, f'{name}.png')
    fig.savefig(path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    return path


# ─── 数据加载 ────────────────────────────────────────────────────────────────
ECONKIT_DIR = '/Users/jacky/.openclaw/workspace/econkit'
TESTS_DIR   = os.path.join(ECONKIT_DIR, 'tests')

print('\n========== 加载测试数据集 ==========')
try:
    df_main    = pd.read_csv(os.path.join(ECONKIT_DIR, 'test_data.csv'))
    df_health  = pd.read_csv(os.path.join(TESTS_DIR,   'data_health.csv'))
    df_digital = pd.read_csv(os.path.join(TESTS_DIR,   'data_digital.csv'))
    df_rdd     = pd.read_csv(os.path.join(TESTS_DIR,   'data_rdd.csv'))
    print(f'  test_data.csv   : {df_main.shape}')
    print(f'  data_health.csv : {df_health.shape}')
    print(f'  data_digital.csv: {df_digital.shape}')
    print(f'  data_rdd.csv    : {df_rdd.shape}')
except Exception as e:
    print(f'  ❌ 数据加载失败: {e}')
    sys.exit(1)

# ─── 1. 描述统计 ─────────────────────────────────────────────────────────────
print('\n========== 1. 描述统计 ==========')
try:
    from analysis.descriptive import compute_descriptive_stats, plot_descriptive_stats
    cols = ['tfp', 'size', 'lev', 'roa', 'score']
    cols = [c for c in cols if c in df_main.columns]
    desc = compute_descriptive_stats(df_main, cols)
    fig = plot_descriptive_stats(df_main, cols)
    save_fig(fig, '01_descriptive')
    headers = ['变量'] + list(desc.columns)
    rows = [[idx] + [str(v) for v in row] for idx, row in desc.iterrows()]
    details = f'变量数: {len(cols)}, 观测数: {len(df_main)}'
    record('1. 描述统计', 'PASS', details, table_headers=headers, table_rows=rows[:8])
except Exception as e:
    record('1. 描述统计', 'FAIL', traceback.format_exc()[:500])

# ─── 2. 相关矩阵 ─────────────────────────────────────────────────────────────
print('\n========== 2. 相关矩阵 ==========')
try:
    from analysis.descriptive import compute_correlation_matrix, plot_correlation_matrix
    cols = [c for c in ['tfp', 'size', 'lev', 'roa', 'score'] if c in df_main.columns]
    corr, pvals = compute_correlation_matrix(df_main, cols)
    fig = plot_correlation_matrix(corr, pvals)
    save_fig(fig, '02_correlation')
    details = f'相关矩阵维度: {corr.shape}, TFP-SIZE相关: {corr.loc["tfp","size"]:.4f}'
    record('2. 相关矩阵', 'PASS', details)
except Exception as e:
    record('2. 相关矩阵', 'FAIL', traceback.format_exc()[:500])

# ─── 3. 正态性检验 ───────────────────────────────────────────────────────────
print('\n========== 3. 正态性检验 ==========')
try:
    from analysis.descriptive import test_normality
    cols = [c for c in ['tfp', 'size', 'lev', 'roa'] if c in df_main.columns]
    norm_df = test_normality(df_main, cols)
    headers = list(norm_df.columns)
    rows = norm_df.values.tolist()
    details = f'检验变量数: {len(norm_df)}'
    record('3. 正态性检验（SW+JB）', 'PASS', details, table_headers=headers, table_rows=rows)
except Exception as e:
    record('3. 正态性检验（SW+JB）', 'FAIL', traceback.format_exc()[:500])

# ─── 4. VIF 多重共线性 ───────────────────────────────────────────────────────
print('\n========== 4. VIF检验 ==========')
try:
    from analysis.descriptive import compute_vif
    cols = [c for c in ['size', 'lev', 'roa', 'score'] if c in df_main.columns]
    vif_df = compute_vif(df_main, cols)
    headers = list(vif_df.columns)
    rows = vif_df.values.tolist()
    details = f'最大VIF: {vif_df["VIF"].max():.4f}'
    record('4. VIF多重共线性检验', 'PASS', details, table_headers=headers, table_rows=rows)
except Exception as e:
    record('4. VIF多重共线性检验', 'FAIL', traceback.format_exc()[:500])

# ─── 5. 异方差检验 ───────────────────────────────────────────────────────────
print('\n========== 5. 异方差检验 ==========')
try:
    from analysis.descriptive import test_heteroskedasticity
    res = test_heteroskedasticity(df_main, 'tfp', ['size', 'lev', 'roa'])
    bp  = res['breusch_pagan']
    wh  = res['white']
    details = (f"BP检验: LM={bp['LM统计量']}, p={bp['p值']}, {bp['结论']}\n"
               f"White检验: LM={wh['LM统计量']}, p={wh['p值']}, {wh['结论']}")
    record('5. 异方差检验（BP+White）', 'PASS', details)
except Exception as e:
    record('5. 异方差检验（BP+White）', 'FAIL', traceback.format_exc()[:500])

# ─── 6. 自相关检验 ───────────────────────────────────────────────────────────
print('\n========== 6. 自相关检验 ==========')
try:
    from analysis.descriptive import test_autocorrelation
    res = test_autocorrelation(df_main, 'tfp', ['size', 'lev', 'roa'])
    dw  = res['durbin_watson']
    details = f"DW统计量: {dw['统计量']}, {dw['结论']}"
    record('6. 自相关检验（DW）', 'PASS', details)
except Exception as e:
    record('6. 自相关检验（DW）', 'FAIL', traceback.format_exc()[:500])

# ─── 7. OLS 普通回归 ─────────────────────────────────────────────────────────
print('\n========== 7. OLS回归（普通标准误）==========')
try:
    from analysis.panel_regression import run_ols
    res = run_ols(df_main, 'tfp', ['size', 'lev', 'roa', 'score'], cov_type='nonrobust')
    s = res['stats']
    headers = list(res['summary_df'].columns)
    rows = res['summary_df'].values.tolist()
    details = f"N={s['n_obs']}, R²={s['r2']}, Adj.R²={s['adj_r2']}, F={s['f_stat']}"
    record('7. OLS回归（普通标准误）', 'PASS', details, table_headers=headers, table_rows=rows)
except Exception as e:
    record('7. OLS回归（普通标准误）', 'FAIL', traceback.format_exc()[:500])

# ─── 8. OLS 稳健标准误 ───────────────────────────────────────────────────────
print('\n========== 8. OLS回归（稳健标准误）==========')
try:
    from analysis.panel_regression import run_ols
    res = run_ols(df_main, 'tfp', ['size', 'lev', 'roa', 'score'], cov_type='HC3')
    s = res['stats']
    headers = list(res['summary_df'].columns)
    rows = res['summary_df'].values.tolist()
    details = f"N={s['n_obs']}, R²={s['r2']}, Adj.R²={s['adj_r2']} （HC3稳健标准误）"
    record('8. OLS回归（稳健标准误HC3）', 'PASS', details, table_headers=headers, table_rows=rows)
except Exception as e:
    record('8. OLS回归（稳健标准误HC3）', 'FAIL', traceback.format_exc()[:500])

# ─── 9. 面板 FE ──────────────────────────────────────────────────────────────
print('\n========== 9. 面板固定效应FE ==========')
try:
    from analysis.panel_regression import run_panel_model
    res = run_panel_model(df_main, 'tfp', ['size', 'lev', 'roa'], 'firm_id', 'year', 'fe')
    s = res['stats']
    headers = list(res['summary_df'].columns)
    rows = res['summary_df'].values.tolist()
    details = f"N={s['n_obs']}, R²_within={s['r2_within']}, F={s['f_stat']}"
    record('9. 面板固定效应FE', 'PASS', details, table_headers=headers, table_rows=rows)
except Exception as e:
    record('9. 面板固定效应FE', 'FAIL', traceback.format_exc()[:500])

# ─── 10. 面板 RE ─────────────────────────────────────────────────────────────
print('\n========== 10. 面板随机效应RE ==========')
try:
    from analysis.panel_regression import run_panel_model
    res = run_panel_model(df_main, 'tfp', ['size', 'lev', 'roa'], 'firm_id', 'year', 're')
    s = res['stats']
    headers = list(res['summary_df'].columns)
    rows = res['summary_df'].values.tolist()
    details = f"N={s['n_obs']}, R²_within={s['r2_within']}"
    record('10. 面板随机效应RE', 'PASS', details, table_headers=headers, table_rows=rows)
except Exception as e:
    record('10. 面板随机效应RE', 'FAIL', traceback.format_exc()[:500])

# ─── 11. 双向固定效应 TWFE ───────────────────────────────────────────────────
print('\n========== 11. 双向固定效应TWFE ==========')
try:
    from analysis.panel_regression import run_panel_model
    res = run_panel_model(df_main, 'tfp', ['size', 'lev', 'roa'], 'firm_id', 'year', 'twfe')
    s = res['stats']
    headers = list(res['summary_df'].columns)
    rows = res['summary_df'].values.tolist()
    details = f"N={s['n_obs']}, R²_within={s['r2_within']} (个体+时间双向FE)"
    record('11. 双向固定效应TWFE', 'PASS', details, table_headers=headers, table_rows=rows)
except Exception as e:
    record('11. 双向固定效应TWFE', 'FAIL', traceback.format_exc()[:500])

# ─── 12. Hausman 检验 ────────────────────────────────────────────────────────
print('\n========== 12. Hausman检验（FE vs RE）==========')
try:
    from analysis.panel_regression import run_hausman_test
    res = run_hausman_test(df_main, 'tfp', ['size', 'lev', 'roa'], 'firm_id', 'year')
    if 'error' in res:
        record('12. Hausman检验', 'WARN', res['error'])
    else:
        details = f"H统计量={res['H统计量']}, df={res['自由度']}, p={res['p值']}, {res['结论']}"
        record('12. Hausman检验（FE vs RE）', 'PASS', details,
               note=res.get('解释', ''))
except Exception as e:
    record('12. Hausman检验', 'FAIL', traceback.format_exc()[:500])

# ─── 13. 面板单位根检验 ──────────────────────────────────────────────────────
print('\n========== 13. 面板单位根检验 ==========')
try:
    from analysis.panel_regression import test_panel_unit_root
    res = test_panel_unit_root(df_main, 'tfp', 'firm_id', 'year')
    if 'error' in res:
        record('13. 面板单位根检验', 'WARN', res['error'])
    else:
        details = (f"检验方法: {res['检验方法']}\n"
                   f"截面数: {res['截面数']}, 平均ADF: {res['平均ADF统计量']}\n"
                   f"拒绝单位根比例: {res['拒绝单位根比例']}, {res['结论']}")
        record('13. 面板单位根检验', 'PASS', details)
except Exception as e:
    record('13. 面板单位根检验', 'FAIL', traceback.format_exc()[:500])

# ─── 14. 基础 DID ────────────────────────────────────────────────────────────
print('\n========== 14. 基础DID双重差分 ==========')
try:
    from analysis.causal_did import run_basic_did
    controls = [c for c in ['income', 'pop_density', 'edu_level'] if c in df_health.columns]
    res = run_basic_did(df_health, 'health_spending', 'treat', 'post', 'did',
                        controls=controls)
    details = (f"DID系数={res['did_coef']}{res['did_stars']}, "
               f"SE={res['did_se']}, p={res['did_pval']}\n"
               f"N={res['n_obs']}, R²={res['r2']}")
    record('14. 基础DID双重差分', 'PASS', details)
except Exception as e:
    record('14. 基础DID双重差分', 'FAIL', traceback.format_exc()[:500])

# ─── 15. TWFE DID ────────────────────────────────────────────────────────────
print('\n========== 15. TWFE-DID ==========')
try:
    from analysis.causal_did import run_twfe_did
    controls = [c for c in ['income', 'pop_density', 'edu_level'] if c in df_health.columns]
    res = run_twfe_did(df_health, 'health_spending', 'did', 'county_id', 'year',
                       controls=controls)
    details = (f"DID系数={res['did_coef']}{res['did_stars']}, "
               f"SE={res['did_se']}, p={res['did_pval']}\n"
               f"N={res['n_obs']}, R²_within={res['r2_within']}")
    record('15. TWFE-DID双向固定效应', 'PASS', details)
except Exception as e:
    record('15. TWFE-DID双向固定效应', 'FAIL', traceback.format_exc()[:500])

# ─── 16. 平行趋势检验 ────────────────────────────────────────────────────────
print('\n========== 16. 平行趋势检验（事件研究法）==========')
try:
    from analysis.causal_did import run_parallel_trend_test
    controls = [c for c in ['income', 'edu_level'] if c in df_health.columns]
    pt_res, pt_fig = run_parallel_trend_test(
        df_health, 'health_spending', 'treat', 'year', 2019,
        'county_id', controls=controls
    )
    save_fig(pt_fig, '16_parallel_trend')
    if 'error' in pt_res:
        record('16. 平行趋势检验', 'WARN', pt_res['error'], fig=pt_fig)
    else:
        details = (f"{pt_res.get('conclusion', '')}\n"
                   f"政策前联合检验: F={pt_res.get('pre_test', {}).get('f_stat', 'N/A')}, "
                   f"p={pt_res.get('pre_test', {}).get('p_value', 'N/A')}")
        record('16. 平行趋势检验（事件研究法）', 'PASS', details, fig=pt_fig)
except Exception as e:
    record('16. 平行趋势检验', 'FAIL', traceback.format_exc()[:500])

# ─── 17. 安慰剂检验 ──────────────────────────────────────────────────────────
print('\n========== 17. 安慰剂检验 ==========')
try:
    from analysis.causal_did import run_placebo_test
    placebo_res, placebo_fig = run_placebo_test(
        df_health, 'health_spending', 'treat', 'post',
        controls=[c for c in ['income', 'edu_level'] if c in df_health.columns],
        n_sim=500,
        real_coef=0.45
    )
    save_fig(placebo_fig, '17_placebo')
    details = (f"{placebo_res['conclusion']}\n"
               f"安慰剂系数均值={placebo_res['placebo_mean']:.4f}, "
               f"std={placebo_res['placebo_std']:.4f}, p={placebo_res['p_value']}")
    record('17. 安慰剂检验（随机置换）', 'PASS', details, fig=placebo_fig)
except Exception as e:
    record('17. 安慰剂检验', 'FAIL', traceback.format_exc()[:500])

# ─── 18. PSM - KNN ───────────────────────────────────────────────────────────
print('\n========== 18. PSM倾向得分匹配（KNN）==========')
try:
    from analysis.causal_psm import (estimate_propensity_score, knn_matching,
                                      kernel_matching, check_covariate_balance,
                                      plot_psm_distributions)
    covariates = [c for c in ['income', 'pop_density', 'edu_level'] if c in df_health.columns]
    df_h2019 = df_health[df_health['year'] == 2019].copy().reset_index(drop=True)
    df_ps = estimate_propensity_score(df_h2019, 'treat', covariates)
    outcome = df_h2019.loc[df_ps.index, 'health_spending']

    # KNN
    knn_res = knn_matching(df_ps, outcome, 'treat', k=1)
    details_knn = (f"ATT={knn_res['att']}{knn_res['stars']}, SE={knn_res['att_se']}, "
                   f"p={knn_res['p_value']}, 匹配数={knn_res['n_matched']}")

    # 倾向得分分布图
    psm_fig = plot_psm_distributions(df_ps, 'treat')
    save_fig(psm_fig, '18_psm_distribution')

    record('18. PSM-KNN最近邻匹配', 'PASS', details_knn, fig=psm_fig)
except Exception as e:
    record('18. PSM-KNN最近邻匹配', 'FAIL', traceback.format_exc()[:500])

# ─── 19. PSM - 核匹配 ────────────────────────────────────────────────────────
print('\n========== 19. PSM倾向得分匹配（核匹配）==========')
try:
    # 使用上节的 df_ps 和 outcome
    kern_res = kernel_matching(df_ps, outcome, 'treat', bandwidth=0.06)
    details_k = (f"ATT={kern_res['att']}{kern_res['stars']}, SE={kern_res['att_se']}, "
                 f"p={kern_res['p_value']}, 带宽={kern_res['bandwidth']}")

    # 平衡性检验
    matched_t = knn_res['matched_df']
    matched_c_idx = knn_res['matched_df'].index
    df_c_full = df_ps[df_ps['treat'] == 0]
    bal_df, bal_fig = check_covariate_balance(
        df_ps, df_ps[df_ps['treat'] == 1], df_c_full, 'treat', covariates
    )
    save_fig(bal_fig, '19_psm_balance')

    record('19. PSM核匹配+平衡性检验', 'PASS', details_k, fig=bal_fig,
           table_headers=list(bal_df.columns), table_rows=bal_df.values.tolist())
except Exception as e:
    record('19. PSM核匹配+平衡性检验', 'FAIL', traceback.format_exc()[:500])

# ─── 20. RDD 断点回归 ────────────────────────────────────────────────────────
print('\n========== 20. RDD断点回归 ==========')
try:
    from analysis.causal_rdd import run_rdd_local_linear, plot_rdd, select_optimal_bandwidth
    cutoff = 0.0
    res_rdd = run_rdd_local_linear(df_rdd, 'outcome', 'score', cutoff, bandwidth=3.0)
    rdd_fig = plot_rdd(df_rdd, 'outcome', 'score', cutoff, bandwidth=5.0)
    save_fig(rdd_fig, '20_rdd_plot')

    bw_res = select_optimal_bandwidth(df_rdd, 'outcome', 'score', cutoff)

    details = (f"断点效应={res_rdd['coef']}{res_rdd['stars']}, "
               f"SE={res_rdd['se']}, p={res_rdd['pval']}\n"
               f"N={res_rdd['n_obs']}, 最优带宽≈{bw_res['optimal_bandwidth']}")
    record('20. RDD断点回归（局部线性）', 'PASS', details, fig=rdd_fig)
except Exception as e:
    record('20. RDD断点回归', 'FAIL', traceback.format_exc()[:500])

# ─── 21. McCrary 密度检验 ────────────────────────────────────────────────────
print('\n========== 21. McCrary密度检验 ==========')
try:
    from analysis.causal_rdd import mccrary_density_test
    mcc_res, mcc_fig = mccrary_density_test(df_rdd, 'score', 0.0)
    save_fig(mcc_fig, '21_mccrary')
    details = (f"t统计量={mcc_res['t统计量']}, p={mcc_res['p值']}\n"
               f"左侧={mcc_res['左侧样本']}, 右侧={mcc_res['右侧样本']}\n"
               f"{mcc_res['结论']}")
    record('21. McCrary密度检验', 'PASS', details, fig=mcc_fig)
except Exception as e:
    record('21. McCrary密度检验', 'FAIL', traceback.format_exc()[:500])

# ─── 22. IV/2SLS 工具变量 ────────────────────────────────────────────────────
print('\n========== 22. IV/2SLS工具变量 ==========')
try:
    from analysis.causal_iv import run_iv_2sls
    # 在 df_main 中构造一个工具变量（score 的滞后值近似）
    df_iv = df_main.copy().sort_values(['firm_id', 'year'])
    df_iv['score_lag'] = df_iv.groupby('firm_id')['score'].shift(1)
    df_iv = df_iv.dropna(subset=['score_lag'])

    res_iv = run_iv_2sls(
        df_iv,
        dep_var='tfp',
        endog_var='score',
        instruments=['score_lag'],
        exog_controls=['size', 'lev'],
    )
    details = (f"IV系数={res_iv['coef']}{res_iv['stars']}, SE={res_iv['se']}, p={res_iv['pval']}\n"
               f"第一阶段F={res_iv['first_stage_f']} ({'强' if res_iv['weak_iv_pass'] else '弱'}工具变量)\n"
               f"Wu-Hausman: {res_iv['wu_hausman']['结论']}")
    record('22. IV/2SLS工具变量', 'PASS', details)
except Exception as e:
    record('22. IV/2SLS工具变量', 'FAIL', traceback.format_exc()[:500])

# ─── 23. Bootstrap 置信区间 ──────────────────────────────────────────────────
print('\n========== 23. Bootstrap置信区间 ==========')
try:
    from analysis.robustness import bootstrap_confidence_interval
    boot_res, boot_fig = bootstrap_confidence_interval(
        df_main, 'tfp', ['size', 'lev', 'roa'], 'size',
        n_bootstrap=500, ci_level=0.95
    )
    save_fig(boot_fig, '23_bootstrap')
    details = (f"Bootstrap均值={boot_res['mean']}, SE={boot_res['se']}\n"
               f"95% CI=[{boot_res['ci_lo']}, {boot_res['ci_hi']}]\n"
               f"{boot_res['conclusion']}")
    record('23. Bootstrap置信区间', 'PASS', details, fig=boot_fig)
except Exception as e:
    record('23. Bootstrap置信区间', 'FAIL', traceback.format_exc()[:500])

# ─── 24. 剔除特殊样本稳健性 ─────────────────────────────────────────────────
print('\n========== 24. 剔除特殊样本稳健性 ==========')
try:
    from analysis.robustness import exclude_special_samples
    excl_conditions = [
        {'label': '剔除规模最大10%', 'query': 'size > size.quantile(0.9)'},
        {'label': '剔除ROA极端值', 'query': 'roa < roa.quantile(0.01) or roa > roa.quantile(0.99)'},
        {'label': '仅保留后处理期', 'query': 'post == 0'},
    ]
    rob_df = exclude_special_samples(
        df_main, 'tfp', ['size', 'lev', 'roa'], 'size', excl_conditions
    )
    headers = list(rob_df.columns)
    rows = rob_df.values.tolist()
    details = f'共{len(rob_df)}组稳健性检验（含基准组）'
    record('24. 剔除特殊样本稳健性', 'PASS', details,
           table_headers=headers, table_rows=rows)
except Exception as e:
    record('24. 剔除特殊样本稳健性', 'FAIL', traceback.format_exc()[:500])

# ─── 25. 分组回归 ────────────────────────────────────────────────────────────
print('\n========== 25. 分组回归 ==========')
try:
    from analysis.heterogeneity import run_subgroup_regression
    sub_df, sub_fig = run_subgroup_regression(
        df_main, 'tfp', ['size', 'lev', 'roa'], 'size', 'treat'
    )
    save_fig(sub_fig, '25_subgroup')
    headers = list(sub_df.columns)
    rows = sub_df.values.tolist()
    details = f'分组数: {len(sub_df)}'
    record('25. 分组回归', 'PASS', details, fig=sub_fig,
           table_headers=headers, table_rows=rows)
except Exception as e:
    record('25. 分组回归', 'FAIL', traceback.format_exc()[:500])

# ─── 26. 分位数回归 ──────────────────────────────────────────────────────────
print('\n========== 26. 分位数回归 ==========')
try:
    from analysis.heterogeneity import run_quantile_regression
    qr_df, qr_fig = run_quantile_regression(
        df_main, 'tfp', ['size', 'lev', 'roa'], 'size',
        quantiles=[0.1, 0.25, 0.5, 0.75, 0.9]
    )
    save_fig(qr_fig, '26_quantile')
    headers = list(qr_df.columns)
    rows = qr_df.values.tolist()
    details = '分位数: Q0.1 ~ Q0.9'
    record('26. 分位数回归', 'PASS', details, fig=qr_fig,
           table_headers=headers, table_rows=rows)
except Exception as e:
    record('26. 分位数回归', 'FAIL', traceback.format_exc()[:500])

# ─── 27. 中介效应（Bootstrap）────────────────────────────────────────────────
print('\n========== 27. 中介效应（Bootstrap）==========')
try:
    from analysis.heterogeneity import run_mediation_analysis
    med_res, med_fig = run_mediation_analysis(
        df_main, 'tfp', 'roa', 'size',
        controls=['lev'],
        n_bootstrap=500
    )
    save_fig(med_fig, '27_mediation')
    details = (f"路径a={med_res['path_a']}, b={med_res['path_b']}\n"
               f"间接效应={med_res['indirect_effect']}, 直接效应={med_res['direct_effect']}\n"
               f"中介占比={med_res['pct_mediated']}%\n"
               f"Bootstrap CI=[{med_res['bootstrap_ci_lo']}, {med_res['bootstrap_ci_hi']}]\n"
               f"{med_res['conclusion']}")
    record('27. 中介效应（Bootstrap法）', 'PASS', details, fig=med_fig)
except Exception as e:
    record('27. 中介效应（Bootstrap法）', 'FAIL', traceback.format_exc()[:500])

# ─── 28. 调节效应 ────────────────────────────────────────────────────────────
print('\n========== 28. 调节效应 ==========')
try:
    from analysis.heterogeneity import run_moderation_analysis
    mod_res, mod_fig = run_moderation_analysis(
        df_main, 'tfp', 'size', 'lev', controls=['roa']
    )
    save_fig(mod_fig, '28_moderation')
    details = (f"交互项系数={mod_res['interaction_coef']}{mod_res['stars']}, "
               f"SE={mod_res['interaction_se']}, p={mod_res['interaction_pval']}\n"
               f"N={mod_res['n_obs']}, R²={mod_res['r2']}\n"
               f"{mod_res['conclusion']}")
    record('28. 调节效应（交互项）', 'PASS', details, fig=mod_fig)
except Exception as e:
    record('28. 调节效应（交互项）', 'FAIL', traceback.format_exc()[:500])

# ─── 29. 生成 PDF 报告 ───────────────────────────────────────────────────────
print('\n========== 29. 生成PDF报告 ==========')
try:
    from core.report_generator import generate_pdf_report
    pdf_bytes = generate_pdf_report(
        title='本科毕业论文实证分析报告',
        sections=SECTIONS,
        metadata={
            'author': 'EconKit 自动测试',
            'data_desc': 'test_data / data_health / data_digital / data_rdd 四套数据集',
            'date': '2026年03月16日',
        }
    )
    pdf_path = os.path.join(TESTS_DIR, 'undergrad_report.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(pdf_bytes)
    size_kb = len(pdf_bytes) / 1024
    print(f'  PDF 报告已保存: {pdf_path} ({size_kb:.1f} KB)')
    record('29. PDF报告生成', 'PASS',
           f'PDF路径: {pdf_path}\n大小: {size_kb:.1f} KB\n包含章节: {len(SECTIONS)}个')
except Exception as e:
    record('29. PDF报告生成', 'FAIL', traceback.format_exc()[:500])

# ─── 测试汇总 ────────────────────────────────────────────────────────────────
print('\n' + '='*55)
print('  测试汇总')
print('='*55)
total = PASS_COUNT + FAIL_COUNT + WARN_COUNT
print(f'  总计: {total} 项')
print(f'  ✅ PASS: {PASS_COUNT}')
print(f'  ❌ FAIL: {FAIL_COUNT}')
print(f'  ⚠️  WARN: {WARN_COUNT}')
print('='*55)

if FAIL_COUNT > 0:
    print('\n失败项目:')
    for r in RESULTS:
        if r['status'] == 'FAIL':
            print(f"  - {r['name']}")
