"""
English language pack
"""
from __future__ import annotations

STRINGS: dict[str, str] = {
    # ── App basics ────────────────────────────────────────────────────────────
    "app.title": "EconKit - Econometric Analysis Toolkit",
    "app.icon": "📊",
    "lang.toggle": "🌐 中文",

    # ── Step bar ──────────────────────────────────────────────────────────────
    "step.1.label": "Upload Data",
    "step.2.label": "Smart Guide",
    "step.3.label": "Empirical Analysis",
    "step.4.label": "Download Report",

    "page.home": "🏠 Home",
    "page.smart_guide": "🤖 Smart Guide",
    "page.analysis": "📈 Empirical Analysis",
    "page.report": "📄 Download Report",

    # ── Sidebar ───────────────────────────────────────────────────────────────
    "sidebar.subtitle": "Econometric Empirical Analysis Toolkit",
    "sidebar.current_step": "📍 Current: {label}",
    "sidebar.step_label.1": "Step 1/4",
    "sidebar.step_label.2": "Step 2/4",
    "sidebar.step_label.3": "Step 3/4",
    "sidebar.step_label.4": "Step 4/4",
    "sidebar.nav_label": "🧭 Navigation",
    "sidebar.data_loaded": "✅ Data Loaded\n{rows} rows × {cols} columns",
    "sidebar.no_data": "💡 Please upload data first",
    "sidebar.analysis_done": "🔬 {n} analyses completed",
    "sidebar.version": "EconKit v1.0.0",
    "sidebar.desc": "Designed for economics & management graduate research",

    # ── Home page ─────────────────────────────────────────────────────────────
    "home.title": "📊 EconKit",
    "home.subtitle": "All-in-one Econometric Empirical Analysis Toolkit · Built for Economics & Management Graduate Students",
    "home.feature.describe": "🔵 **Descriptive Statistics & Diagnostics**\n\nCorrelation matrix, VIF, Heteroskedasticity, Autocorrelation",
    "home.feature.baseline": "🟡 **Baseline Regression**\n\nOLS, FE/RE, TWFE, Hausman",
    "home.feature.causal": "🔴 **Causal Inference**\n\nDID, PSM, RDD, IV/2SLS, GMM",
    "home.feature.mechanism": "🟣 **Mechanism Analysis**\n\nMediation, Moderation, Subgroup Regression, Quantile Regression",

    "home.step1.title": "## 📁 Step 1: Upload Data",
    "home.tab.upload": "📤 Upload Data File",
    "home.tab.sample": "📋 Use Sample Data",

    "home.upload.label": "Drag and drop or click to upload CSV / Excel file (max 50MB)",
    "home.upload.help": "Supports UTF-8 / GBK encoded CSV and Excel 2007+ (.xlsx) formats",
    "home.upload.parsing": "Parsing data...",
    "home.upload.success": "✅ Data loaded successfully: {rows} rows × {cols} columns",
    "home.upload.error": "❌ Data loading failed: {error}",

    "home.sample.info": "Sample data: 200 firms × 2010–2020 panel data, including variables for DID/PSM/RDD/IV analyses",
    "home.sample.btn.load": "🎯 Load Sample Data",
    "home.sample.btn.download": "⬇️ Download Sample Data CSV",
    "home.sample.generating": "Generating sample data...",
    "home.sample.success": "✅ Sample data loaded: {rows} rows × {cols} columns",

    "home.detect.info": "🔍 Auto-detected: Entity=`{id_col}`, Time=`{time_col}` ({n_entities} entities, {n_periods} periods)",
    "home.detect.warning": "⚠️ Panel structure could not be auto-detected. Please select entity/time variables manually during analysis.",

    "home.preview.title": "## 👀 Data Preview",
    "home.preview.rows": "Total Rows",
    "home.preview.cols": "Total Columns",
    "home.preview.numeric": "Numeric Columns",
    "home.preview.missing": "Overall Missing Rate",
    "home.preview.col_details": "📋 View Column Details",
    "home.preview.col.name": "Column Name",
    "home.preview.col.type": "Type",
    "home.preview.col.notnull": "Non-null Count",
    "home.preview.col.missing": "Missing Rate",
    "home.preview.col.unique": "Unique Values",

    "home.panel_config.title": "### ⚙️ Configure Panel Structure",
    "home.panel_config.id": "Entity Variable",
    "home.panel_config.time": "Time Variable",
    "home.panel_config.next": "✅ Next: Smart Guide →",
    "home.panel_config.success": "✅ Panel structure configured successfully! Redirecting to Smart Guide...",

    # ── Smart guide page ───────────────────────────────────────────────────────
    "guide.title": "## 🤖 Step 2: Smart Method Recommendation Engine",
    "guide.subtitle": "Describe your research background, and the system will automatically recommend the most appropriate econometric analysis path.",

    "guide.input.label": "📝 Research Background Description (Chinese or English)",
    "guide.input.placeholder": (
        "Example: This paper studies the effect of an environmental policy introduced by a province in 2015 "
        "on firm total factor productivity, using firm-level panel data from 2010–2020. "
        "The treatment and control groups should satisfy the parallel trends assumption prior to policy implementation. "
        "We also address endogeneity concerns and aim to test the transmission mechanism of the policy effect."
    ),
    "guide.keywords.title": "**💡 Keyword Trigger Rules**",
    "guide.keywords.content": (
        "- Policy / shock / natural experiment → **DID**\n"
        "- Endogeneity / simultaneity → **IV/GMM**\n"
        "- Panel data → **FE/RE**\n"
        "- Cutoff / eligibility threshold → **RDD**\n"
        "- Mechanism / pathway → **Mediation Analysis**\n"
        "- Heterogeneous groups → **Heterogeneity Analysis**"
    ),

    "guide.btn.recommend": "🔍 Smart Recommend",
    "guide.recommending": "Analyzing...",
    "guide.recommend.success": "✅ {n} analysis methods recommended",

    "guide.results.title": "### 🎯 Recommended Analysis Path",
    "guide.results.subtitle": "Execute the following steps in order for the most complete empirical results:",

    "guide.priority.1": "🔴 Required",
    "guide.priority.2": "🟡 Recommended",
    "guide.priority.3": "🟢 Optional",

    "guide.sub_steps.expander": "📋 Detailed Analysis Steps",

    "guide.btn.start_analysis": "🚀 Start Empirical Analysis →",
    "guide.tip.methods_saved": "💡 Recommended methods saved. You can quickly jump to them from the analysis page.",

    "guide.catalog.title": "## 📚 Full Analysis Method Catalog",

    "guide.category.describe": "🔵 Descriptive Diagnostics",
    "guide.category.panel": "🟡 Panel Regression",
    "guide.category.causal": "🔴 Causal Inference",
    "guide.category.robust": "🟢 Robustness Checks",
    "guide.category.hetero": "🟣 Heterogeneity & Mechanisms",

    # ── Analysis page ─────────────────────────────────────────────────────────
    "analysis.no_data.warning": "⚠️ Please upload data on the Home page first",
    "analysis.no_data.back": "← Back to Upload Data",
    "analysis.title": "## 📈 Step 3: Empirical Analysis",

    "analysis.done_count": "✅ {n} analyses completed",
    "analysis.tip": "💡 Select an analysis method below and run it. When done, click the button on the right to generate the report.",
    "analysis.btn.to_report": "📄 Finish Analysis, Generate Report →",

    "analysis.recommended.info": "🎯 Smart Guide recommended **{n}** analysis methods. Click to jump:",
    "analysis.method.select": "🔬 Select Analysis Method",
    "analysis.method.placeholder": "👆 Please select a specific analysis method from the dropdown",

    # Analysis method names (dropdown options)
    "method.descriptive": "Descriptive Statistics",
    "method.correlation": "Correlation Matrix",
    "method.normality": "Normality Test",
    "method.vif": "VIF Multicollinearity",
    "method.heterosked": "Heteroskedasticity Test",
    "method.autocorrelation": "Autocorrelation Test",
    "method.ols": "OLS Regression",
    "method.panel_fe": "Panel Fixed Effects (FE/RE/TWFE)",
    "method.hausman": "Hausman Test",
    "method.unit_root": "Panel Unit Root Test",
    "method.did": "DID Difference-in-Differences",
    "method.psm": "PSM Propensity Score Matching",
    "method.rdd": "RDD Regression Discontinuity",
    "method.iv": "IV / 2SLS",
    "method.gmm": "Dynamic Panel GMM",
    "method.bootstrap": "Bootstrap Confidence Interval",
    "method.exclude_samples": "Sample Exclusion / Robustness to Outliers",
    "method.subgroup": "Subgroup Regression",
    "method.quantile": "Quantile Regression",
    "method.mediation": "Mediation Analysis",
    "method.moderation": "Moderation Analysis",

    # Group labels
    "group.describe": "── 🔵 Descriptive Statistics & Diagnostics ──",
    "group.baseline": "── 🟡 Baseline Regression ──",
    "group.causal": "── 🔴 Causal Inference ──",
    "group.robust": "── 🟢 Robustness Checks ──",
    "group.hetero": "── 🟣 Heterogeneity & Mechanisms ──",

    # ── Descriptive Statistics ────────────────────────────────────────────────
    "desc.vars.label": "Select Variables for Analysis",
    "desc.btn.run": "▶ Run Descriptive Statistics",
    "desc.result.title": "Descriptive Statistics Results",
    "desc.result.note": "Mean / Std. Dev. / Quantiles / Skewness / Kurtosis",
    "desc.fig.title": "Variable Distribution Plots",

    # ── Correlation Matrix ─────────────────────────────────────────────────────
    "corr.vars.label": "Select Variables",
    "corr.method.label": "Correlation Coefficient Method",
    "corr.btn.run": "▶ Run Correlation Matrix",
    "corr.result.title": "{method} Correlation Matrix",
    "corr.result.note": "Lower triangle: correlation coefficients; ***p<0.01, **p<0.05, *p<0.1",
    "corr.fig.title": "Correlation Matrix Heatmap",

    # ── Normality Test ────────────────────────────────────────────────────────
    "norm.vars.label": "Select Variables for Testing",
    "norm.btn.run": "▶ Run Normality Test",
    "norm.result.title": "Normality Test Results (Shapiro-Wilk / Jarque-Bera)",

    # ── VIF ───────────────────────────────────────────────────────────────────
    "vif.vars.label": "Select Variables (pairwise VIF will be computed)",
    "vif.vars.min": "Please select at least 2 variables",
    "vif.btn.run": "▶ Compute VIF",
    "vif.result.title": "VIF Multicollinearity Test",
    "vif.result.note": "VIF > 10: severe multicollinearity; VIF > 5: moderate multicollinearity",

    # ── Autocorrelation Test ──────────────────────────────────────────────────
    "autocorr.title": "### Autocorrelation Test (Durbin-Watson)",
    "autocorr.dep.label": "Dependent Variable",
    "autocorr.indep.label": "Independent Variables",
    "autocorr.indep.min": "Please select at least one independent variable",
    "autocorr.btn.run": "▶ Run Autocorrelation Test",
    "autocorr.test.name": "Durbin-Watson Test",
    "autocorr.recommend.prefix": "💡 Recommendation: ",

    # ── Heteroskedasticity Test ───────────────────────────────────────────────
    "het.dep.label": "Dependent Variable",
    "het.indep.label": "Independent Variables",
    "het.btn.run": "▶ Run Heteroskedasticity Test",
    "het.bp.title": "**Breusch-Pagan Test**",
    "het.bp.name": "BP Test",
    "het.white.title": "**White Test**",
    "het.white.name": "White Test",
    "het.recommend.prefix": "💡 Recommendation: ",

    # ── Unit Root ─────────────────────────────────────────────────────────────
    "unit_root.title": "### Panel Unit Root Test (ADF Summary)",
    "unit_root.col.label": "Variable to Test",
    "unit_root.id.label": "Entity Variable",
    "unit_root.time.label": "Time Variable",
    "unit_root.btn.run": "▶ Run Unit Root Test",
    "unit_root.result.name": "Panel Unit Root Test (ADF Summary)",

    # ── OLS ───────────────────────────────────────────────────────────────────
    "ols.title": "### OLS Ordinary Least Squares Regression",
    "ols.dep.label": "Dependent Variable (Y)",
    "ols.cov.label": "Standard Error Type",
    "ols.cov.robust": "HC3 (Robust)",
    "ols.cov.plain": "Nonrobust (Plain)",
    "ols.indep.label": "Independent Variables (X)",
    "ols.indep.min": "Please select at least one independent variable",
    "ols.btn.run": "▶ Run OLS Regression",

    # ── Panel Fixed Effects ───────────────────────────────────────────────────
    "panel.title": "### Panel Fixed / Random Effects Regression",
    "panel.id.label": "Entity Variable",
    "panel.dep.label": "Dependent Variable (Y)",
    "panel.time.label": "Time Variable",
    "panel.model.label": "Model Type",
    "panel.indep.label": "Independent Variables (X)",
    "panel.indep.min": "Please select at least one independent variable",
    "panel.btn.run": "▶ Run Panel Model",

    # ── Hausman ───────────────────────────────────────────────────────────────
    "hausman.title": "### Hausman Test (FE vs RE)",
    "hausman.id.label": "Entity Variable",
    "hausman.dep.label": "Dependent Variable",
    "hausman.time.label": "Time Variable",
    "hausman.indep.label": "Independent Variables",
    "hausman.btn.run": "▶ Run Hausman Test",
    "hausman.result.name": "Hausman Test (FE vs RE)",

    # ── DID ───────────────────────────────────────────────────────────────────
    "did.title": "### DID Difference-in-Differences Analysis",
    "did.dep.label": "Dependent Variable (Y)",
    "did.treat.label": "Treatment Indicator (treat)",
    "did.post.label": "Post-treatment Dummy (post)",
    "did.did.label": "Interaction Term (did = treat × post)",
    "did.id.label": "Entity Variable (Panel ID)",
    "did.time.label": "Time Variable",
    "did.treat_year.label": "Policy Implementation Year (for event study)",
    "did.controls.label": "Control Variables",
    "did.config.title": "**📌 DID Variable Configuration**",
    "did.steps.label": "Select Analysis Steps",
    "did.step.basic": "Baseline DID (OLS)",
    "did.step.twfe": "Two-Way Fixed Effects DID",
    "did.step.parallel": "Parallel Trends Test",
    "did.step.placebo": "Placebo Test",
    "did.nsim.label": "Number of Placebo Simulations",
    "did.btn.run": "▶ Run DID Analysis",
    "did.running": "Analyzing (may take 1–3 minutes)...",

    "did.basic.title": "#### Baseline DID",
    "did.twfe.title": "#### Two-Way Fixed Effects DID",
    "did.parallel.title": "#### Parallel Trends Test (Event Study)",
    "did.parallel.fig.title": "Parallel Trends Test Plot",
    "did.parallel.error": "Parallel trends test failed: {error}",
    "did.placebo.title": "#### Placebo Test (Random Treatment Group Permutation)",
    "did.placebo.progress": "Placebo test in progress ({done}/{n})...",
    "did.placebo.fig.title": "Placebo Test ({n} Permutations)",

    "did.display.basic": "Baseline DID (OLS + Robust SE)",
    "did.display.twfe": "TWFE DID (Entity + Time Two-Way FE)",

    # ── PSM ───────────────────────────────────────────────────────────────────
    "psm.title": "### PSM Propensity Score Matching",
    "psm.treat.label": "Treatment Variable (0/1)",
    "psm.dep.label": "Outcome Variable (Y)",
    "psm.covs.label": "Matching Covariates",
    "psm.method.label": "Matching Method",
    "psm.method.knn": "KNN (Nearest Neighbor)",
    "psm.method.kernel": "Kernel Matching",
    "psm.k.label": "Number of KNN Neighbors",
    "psm.covs.min": "Please select matching covariates",
    "psm.btn.run": "▶ Run PSM Matching",
    "psm.matching": "Matching...",
    "psm.dist.fig.title": "Propensity Score Distribution Plot",
    "psm.att.title": "#### ATT Estimate ({method})",
    "psm.att.label": "ATT (Average Treatment Effect on the Treated)",
    "psm.se.label": "Standard Error",
    "psm.pval.label": "p-value",

    # ── RDD ───────────────────────────────────────────────────────────────────
    "rdd.title": "### RDD Regression Discontinuity Design",
    "rdd.dep.label": "Dependent Variable (Y)",
    "rdd.run.label": "Running Variable (Score / Index)",
    "rdd.cutoff.label": "Cutoff Value",
    "rdd.bw.label": "Bandwidth (0 = auto-select)",
    "rdd.poly.label": "Polynomial Order",
    "rdd.btn.run": "▶ Run RDD Analysis",
    "rdd.analyzing": "Analyzing...",
    "rdd.fig.title": "RDD Discontinuity Plot",
    "rdd.bw.info": "📏 Suggested bandwidth: {bw} (score std. dev. × 1.0)",
    "rdd.bw.sens.title": "Bandwidth Sensitivity Analysis",
    "rdd.coef.label": "Jump at Cutoff (RDD Coefficient)",
    "rdd.se.label": "Standard Error",
    "rdd.pval.label": "p-value",
    "rdd.n.label": "N within Bandwidth",
    "rdd.density.title": "#### McCrary Density Test",
    "rdd.density.fig.title": "Density Continuity Test",
    "rdd.density.result.title": "Density Test Results",

    # ── IV/2SLS ───────────────────────────────────────────────────────────────
    "iv.title": "### IV / 2SLS Instrumental Variables Regression",
    "iv.dep.label": "Dependent Variable (Y)",
    "iv.endog.label": "Endogenous Variable (X)",
    "iv.instruments.label": "Instrumental Variables (Z)",
    "iv.controls.label": "Exogenous Control Variables",
    "iv.instruments.min": "Please select instrumental variables",
    "iv.btn.run": "▶ Run IV/2SLS",
    "iv.estimating": "Estimating...",
    "iv.coef.label": "IV Coefficient",
    "iv.se.label": "Standard Error",
    "iv.f.label": "First-Stage F-statistic",
    "iv.weak_iv": "⚠️ Weak Instruments",
    "iv.wu_hausman.name": "Wu-Hausman Endogeneity Test",
    "iv.sargan.name": "Sargan Over-identification Test",

    # ── GMM ───────────────────────────────────────────────────────────────────
    "gmm.title": "### Dynamic Panel GMM (Arellano-Bond)",
    "gmm.dep.label": "Dependent Variable (Y)",
    "gmm.id.label": "Entity Variable",
    "gmm.indep.label": "Independent Variables (one-period lag of Y is automatically included)",
    "gmm.time.label": "Time Variable",
    "gmm.type.label": "GMM Type",
    "gmm.type.diff": "Difference GMM (Arellano-Bond)",
    "gmm.type.sys": "System GMM (Blundell-Bond)",
    "gmm.info": (
        "✅ Uses **pydynpd** for genuine Arellano-Bond (Difference GMM) / Blundell-Bond (System GMM) estimation, "
        "including Windmeijer (2005) finite-sample corrected standard errors + AR(1)/AR(2) tests + Hansen over-identification test."
    ),
    "gmm.indep.min": "Please select at least one independent variable",
    "gmm.btn.run": "▶ Run GMM Estimation",
    "gmm.running": "Estimating (genuine Arellano-Bond / Blundell-Bond GMM)...",
    "gmm.ar.title": "#### Arellano-Bond Serial Correlation Tests",
    "gmm.ar.caption": "Criterion: AR(1) should be significant (p<0.05); AR(2) should be insignificant (p>0.1)",
    "gmm.hansen.title": "#### Hansen Over-identification Test",
    "gmm.hansen.chi2.label": "Chi² Statistic",
    "gmm.hansen.df.label": "Degrees of Freedom",
    "gmm.hansen.pval.label": "p-value",

    # ── Bootstrap ─────────────────────────────────────────────────────────────
    "boot.title": "### Bootstrap Confidence Interval",
    "boot.dep.label": "Dependent Variable",
    "boot.key.label": "Key Variable (for CI computation)",
    "boot.n.label": "Number of Bootstrap Replications",
    "boot.indep.label": "All Independent Variables",
    "boot.btn.run": "▶ Run Bootstrap",
    "boot.progress": "Bootstrap in progress ({done}/{n})...",
    "boot.fig.title": "Bootstrap Distribution",

    # ── Sample Exclusion ──────────────────────────────────────────────────────
    "excl.title": "### Sample Exclusion Robustness Check",
    "excl.dep.label": "Dependent Variable",
    "excl.key.label": "Key Independent Variable",
    "excl.indep.label": "All Independent Variables",
    "excl.conditions.title": "**Exclusion Conditions (pandas query syntax)**",
    "excl.n_conditions.label": "Number of Conditions",
    "excl.condition.label_prefix": "Condition {i} Description",
    "excl.condition.default_label": "Exclusion Condition {i}",
    "excl.condition.query_label": "Query (e.g. industry=='Tech')",
    "excl.btn.run": "▶ Run Robustness Check",
    "excl.running": "Running check...",
    "excl.result.title": "Sample Exclusion Robustness Results",

    # ── Subgroup Regression ───────────────────────────────────────────────────
    "subgroup.title": "### Subgroup Regression (Heterogeneity Analysis)",
    "subgroup.dep.label": "Dependent Variable",
    "subgroup.key.label": "Key Independent Variable",
    "subgroup.group.label": "Grouping Variable",
    "subgroup.indep.label": "Independent Variables (including key variable)",
    "subgroup.btn.run": "▶ Run Subgroup Regression",
    "subgroup.running": "Running regression...",
    "subgroup.fig.title": "Subgroup Regression Coefficient Comparison",
    "subgroup.result.title": "Subgroup Regression Results Comparison",

    # ── Quantile Regression ───────────────────────────────────────────────────
    "quantile.title": "### Quantile Regression",
    "quantile.dep.label": "Dependent Variable",
    "quantile.key.label": "Key Independent Variable",
    "quantile.indep.label": "All Independent Variables (including key variable)",
    "quantile.indep.min": "Please include the key independent variable in the regressor list",
    "quantile.btn.run": "▶ Run Quantile Regression",
    "quantile.running": "Running regression...",
    "quantile.fig.title": "Quantile Regression Coefficient Plot",
    "quantile.result.title": "Quantile Regression Results",

    # ── Mediation Analysis ────────────────────────────────────────────────────
    "mediation.title": "### Mediation Analysis (Bootstrap)",
    "mediation.x.label": "Treatment / Cause Variable (X)",
    "mediation.m.label": "Mediator Variable (M)",
    "mediation.y.label": "Outcome Variable (Y)",
    "mediation.controls.label": "Control Variables",
    "mediation.boot.label": "Number of Bootstrap Replications",
    "mediation.btn.run": "▶ Run Mediation Analysis",
    "mediation.progress": "Bootstrap mediation test in progress ({done}/{n})...",
    "mediation.fig.title": "Mediation Path Diagram & Bootstrap Distribution",
    "mediation.indirect.label": "Indirect Effect (a × b)",
    "mediation.direct.label": "Direct Effect (c')",
    "mediation.pct.label": "Mediation Proportion",

    # ── Moderation Analysis ───────────────────────────────────────────────────
    "moderation.title": "### Moderation Analysis",
    "moderation.x.label": "Independent Variable (X)",
    "moderation.m.label": "Moderator Variable (M)",
    "moderation.y.label": "Dependent Variable (Y)",
    "moderation.controls.label": "Control Variables",
    "moderation.btn.run": "▶ Run Moderation Analysis",
    "moderation.analyzing": "Analyzing...",
    "moderation.fig.title": "Moderation Simple Slope Plot",
    "moderation.coef.label": "Interaction Term Coefficient",
    "moderation.se.label": "Standard Error",
    "moderation.pval.label": "p-value",

    # ── Variable selector ─────────────────────────────────────────────────────
    "var.id.label": "🏢 Entity Variable (Panel ID)",
    "var.time.label": "📅 Time Variable",
    "var.dep.label": "📌 Dependent Variable (Y)",
    "var.indep.label": "📋 Independent Variables (X)",

    "panel_var.id.label": "Entity Variable",
    "panel_var.dep.label": "Dependent Variable (Y)",
    "panel_var.time.label": "Time Variable",
    "panel_var.model.label": "Model Type",
    "panel_var.indep.label": "Independent Variables (X)",

    # ── Chart display ─────────────────────────────────────────────────────────
    "chart.download.png": "⬇️ Download Chart PNG (300DPI)",
    "chart.download.table.png": "⬇️ Download Table PNG",
    "chart.download.csv": "⬇️ Download Table CSV",
    "chart.note.default": "Note: Standard errors in parentheses; *** p<0.01, ** p<0.05, * p<0.1",
    "chart.note.robust": "Note: Robust standard errors in parentheses; *** p<0.01, ** p<0.05, * p<0.1",

    "reg.n_obs": "Observations N",
    "reg.r2": "R²",
    "reg.adj_r2": "Adj. R²",
    "reg.f_stat": "F-statistic",
    "reg.coef_table": "{name} Coefficient Table",

    "did.display.coef": "DID Coefficient",
    "did.display.se": "Standard Error",
    "did.display.pval": "p-value",
    "did.display.ci": "📐 95% Confidence Interval: [{lower:.4f}, {upper:.4f}]",
    "did.display.sig1": "✅ DID estimate is significant at the 1% level",
    "did.display.sig5": "✅ DID estimate is significant at the 5% level",
    "did.display.sig10": "⚡ DID estimate is significant at the 10% level",
    "did.display.insig": "❌ DID estimate is insignificant (p ≥ 0.1)",

    # ── Report page ───────────────────────────────────────────────────────────
    "report.title": "## 📄 Download Analysis Report",
    "report.subtitle": "Compile the analysis results into a PDF report for use as a thesis appendix or presentation.",
    "report.input.title": "Report Title",
    "report.input.title.default": "Econometric Empirical Analysis Report",
    "report.input.author": "Author / Institution",
    "report.input.data_desc": "Data Description",
    "report.section.title": "### 📋 Select Report Content",
    "report.section.select": "Select analysis results to include",
    "report.no_results": "💡 No analysis results yet. Please run analyses on the 'Empirical Analysis' page first.",
    "report.btn.generate": "📄 Generate PDF Report",
    "report.generating": "Generating report...",
    "report.success": "✅ PDF report generated successfully!",
    "report.error": "❌ Report generation failed: {error}",
    "report.btn.download": "⬇️ Download PDF Report",
    "report.preview.title": "### 📊 Analysis Results Preview",
    "report.empty.title": "### 📋 Generate Template Report",
    "report.empty.btn": "📄 Generate Empty Template Report",
    "report.empty.download": "⬇️ Download Template PDF",
    "report.empty.content": "This is a template report. Please complete the analyses and regenerate.",

    # Report section names
    "report.section.data": "Data Overview",
    "report.result.descriptive": "Descriptive Statistics",
    "report.result.ols": "OLS Regression",
    "report.result.panel_fe": "Panel Fixed Effects Regression",
    "report.result.did": "DID Difference-in-Differences",
    "report.result.psm": "PSM Propensity Score Matching",
    "report.result.rdd": "RDD Regression Discontinuity Design",
    "report.result.iv": "IV/2SLS Instrumental Variables",
    "report.result.bootstrap": "Bootstrap Confidence Interval",
    "report.result.mediation": "Mediation Analysis",
    "report.result.moderation": "Moderation Analysis",

    # Report content summary
    "report.summary.model": "Model: {name}",
    "report.summary.n_obs": "Observations: {n}",
    "report.summary.r2": "R²: {r2}",
    "report.summary.coefs": "Key coefficients:",
    "report.summary.did": "DID coefficient = {coef}{stars}, p = {pval}, N = {n}",
    "report.summary.vars": "Variables: {n}, descriptive statistics completed",
    "report.summary.done": "{key} analysis completed, coefficient = {coef}",

    # PDF report content
    "pdf.data.rows_cols": "Data dimensions: {rows} rows × {cols} columns",
    "pdf.data.id": "Entity variable: {col}",
    "pdf.data.time": "Time variable: {col}",
    "pdf.data.entities": "Number of entities: {n}",
    "pdf.data.periods": "Number of periods: {n}",
    "pdf.data.numeric": "Numeric variables: {cols}",
    "pdf.data.unknown": "Unknown",
    "pdf.data.na": "N/A",
    "pdf.default_data_desc": "{rows} rows × {cols} columns panel data, entity: {id}, time: {time}",
}
