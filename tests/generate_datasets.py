"""
生成4组测试数据集
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, '/Users/jacky/.openclaw/workspace/econkit')

rng = np.random.default_rng(42)

# ── 数据集1：企业教育政策干预（test_data.csv）────────────────────────────────
def gen_dataset1():
    n_firms = 50
    years = list(range(2015, 2021))  # 6年
    treat_year = 2018
    real_did = 0.2

    rows = []
    firm_effects = rng.normal(0, 0.5, n_firms)
    treat_ids = rng.choice(n_firms, 25, replace=False)

    for i in range(n_firms):
        for y in years:
            treat = 1 if i in treat_ids else 0
            post = 1 if y >= treat_year else 0
            did = treat * post
            firm_fe = firm_effects[i]
            year_fe = (y - 2015) * 0.05
            noise = rng.normal(0, 0.1)
            tfp = 1.0 + 0.3 * treat + 0.1 * post + real_did * did + firm_fe + year_fe + noise
            size = rng.normal(5 + 0.5 * treat, 1)
            lev = rng.beta(2, 5)
            roa = rng.normal(0.08 + 0.02 * treat, 0.05)
            score = rng.normal(60 + 10 * treat, 15)
            rows.append({
                'firm_id': i + 1,
                'year': y,
                'treat': treat,
                'post': post,
                'did': did,
                'tfp': round(tfp, 4),
                'size': round(size, 4),
                'lev': round(lev, 4),
                'roa': round(roa, 4),
                'score': round(score, 2),
            })

    df = pd.DataFrame(rows)
    df.to_csv('/Users/jacky/.openclaw/workspace/econkit/test_data.csv', index=False)
    print(f"Dataset1 saved: {len(df)} rows, DID truth={real_did}")
    return df


# ── 数据集2：医疗补贴政策（data_health.csv）──────────────────────────────────
def gen_dataset2():
    n_counties = 300
    years = list(range(2015, 2023))  # 8年
    treat_year = 2019
    real_did = 0.3
    n_provinces = 10

    rows = []
    county_effects = rng.normal(0, 0.8, n_counties)
    year_effects = rng.normal(0, 0.2, len(years))
    province_effects = rng.normal(0, 0.5, n_provinces)
    treat_ids = set(rng.choice(n_counties, 150, replace=False))
    province_assign = rng.integers(0, n_provinces, n_counties)

    for i in range(n_counties):
        for j, y in enumerate(years):
            treat = 1 if i in treat_ids else 0
            post = 1 if y >= treat_year else 0
            did = treat * post
            prov = province_assign[i]
            county_fe = county_effects[i]
            year_fe = year_effects[j]
            prov_fe = province_effects[prov]
            noise = rng.normal(0, 0.15)
            health_spending = (
                10.0 + 0.5 * treat + 0.2 * post
                + real_did * did
                + county_fe + year_fe + prov_fe + noise
            )
            income = rng.normal(50 + 10 * treat, 15)
            pop_density = rng.lognormal(5, 1)
            edu_level = rng.normal(10 + 1 * treat, 2)
            rows.append({
                'county_id': i + 1,
                'year': y,
                'treat': treat,
                'post': post,
                'did': did,
                'health_spending': round(health_spending, 4),
                'income': round(income, 2),
                'pop_density': round(pop_density, 2),
                'edu_level': round(edu_level, 2),
                'region': prov + 1,
            })

    df = pd.DataFrame(rows)
    df.to_csv('/Users/jacky/.openclaw/workspace/econkit/tests/data_health.csv', index=False)
    print(f"Dataset2 saved: {len(df)} rows, DID truth={real_did}")
    return df


# ── 数据集3：企业数字化转型（data_digital.csv）────────────────────────────────
def gen_dataset3():
    n_firms = 200
    years = list(range(2018, 2023))  # 5年
    treat_year = 2020
    real_did = 0.15
    n_industries = 5
    n_provinces = 8

    rows = []
    treat_ids = set(rng.choice(n_firms, 100, replace=False))
    firm_effects = rng.normal(0, 0.6, n_firms)
    sizes = rng.lognormal(3, 1, n_firms)  # 企业规模（异质性）
    industry_assign = rng.integers(0, n_industries, n_firms)
    province_assign = rng.integers(0, n_provinces, n_firms)

    for i in range(n_firms):
        for y in years:
            treat = 1 if i in treat_ids else 0
            post = 1 if y >= treat_year else 0
            did = treat * post
            size_i = sizes[i]
            # 大企业DID效果更强（异质性）
            size_factor = 1.0 + 0.5 * (size_i > np.median(sizes))
            het_did = real_did * size_factor * did
            firm_fe = firm_effects[i]
            year_fe = (y - 2018) * 0.02
            noise = rng.normal(0, 0.12)
            digital_index = (
                2.0 + 0.3 * treat + 0.1 * post
                + het_did
                + firm_fe + year_fe + noise
            )
            age = 2020 - rng.integers(2000, 2018)
            rd_ratio = rng.beta(2, 8) * (1 + 0.3 * treat)
            rows.append({
                'firm_id': i + 1,
                'year': y,
                'treat': treat,
                'post': post,
                'did': did,
                'digital_index': round(digital_index, 4),
                'size': round(size_i, 4),
                'age': int(age),
                'rd_ratio': round(rd_ratio, 4),
                'industry': industry_assign[i] + 1,
                'province': province_assign[i] + 1,
            })

    df = pd.DataFrame(rows)
    df.to_csv('/Users/jacky/.openclaw/workspace/econkit/tests/data_digital.csv', index=False)
    print(f"Dataset3 saved: {len(df)} rows, DID truth={real_did} (with heterogeneity)")
    return df


# ── 数据集4：RDD专用数据（data_rdd.csv）─────────────────────────────────────
def gen_dataset4():
    n_obs = 2000
    cutoff = 0.0
    true_jump = 1.5

    score = rng.uniform(-5, 5, n_obs)
    above_cutoff = (score >= cutoff).astype(int)
    covariate1 = rng.normal(0, 1, n_obs)  # 协变量连续（断点处无跳跃）
    covariate2 = rng.normal(1, 2, n_obs)

    # 结果变量：线性趋势 + 断点跳跃 + 噪声
    outcome = (
        2.0
        + 0.5 * score  # 线性趋势
        - 0.05 * score**2  # 轻微非线性
        + true_jump * above_cutoff  # 断点跳跃
        + 0.3 * covariate1
        + rng.normal(0, 0.5, n_obs)  # 噪声
    )

    df = pd.DataFrame({
        'obs_id': np.arange(1, n_obs + 1),
        'score': np.round(score, 4),
        'above_cutoff': above_cutoff,
        'outcome': np.round(outcome, 4),
        'covariate1': np.round(covariate1, 4),
        'covariate2': np.round(covariate2, 4),
    })
    df.to_csv('/Users/jacky/.openclaw/workspace/econkit/tests/data_rdd.csv', index=False)
    print(f"Dataset4 saved: {len(df)} rows, true jump={true_jump}")
    return df


if __name__ == '__main__':
    df1 = gen_dataset1()
    df2 = gen_dataset2()
    df3 = gen_dataset3()
    df4 = gen_dataset4()
    print("\nAll datasets generated!")
