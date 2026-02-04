# Feature Extraction & Analysis Report

**Date:** February 4, 2026

## 1. Dataset Statistics

### Source Data
*   **Total Original Conversations**: 282
*   **Total Cited URLs**: 251
*   **Total Uncited URLs**: 25,194
*   **Unique Cited Conversations**: 172

### Filtration Pipeline (Uncited URLs)
1.  **Context Relevance**: Retained only 16,180 URLs appearing in conversations that contained at least one cited link.
2.  **Substantial Content**: Retained 12,892 URLs after removing non-content files (PDF/Images) and non-content domains (YouTube, Google Docs, etc.).

### Feature Extraction
*   **Total Attempted**: 13,143 (251 Cited + 12,892 Uncited)
*   **Successful Fetches**: 9,587 (73.0% Success Rate)
    *   **Cited**: 229 (91.2% Success)
    *   **Uncited**: 9,358 (72.6% Success)
*   **Excluded (Fetch Failures)**: 3,556 (404s, Timeouts, Bot Protection)

---

## 2. Factor Analysis Results

We performed a multivariate logistic regression to predict citation status based on 15 quality factors.

### Significant Findings

**1. "Plain Language" is negatively associated with Citation**
*   **Odds Ratio**: 0.55 (p = 0.013)
*   **Interpretation**: Pages identified as using "Plain Language" were **45% less likely** to be cited by the model.
*   **Prevalence**: 8.7% in Cited vs 15.9% in Uncited.
*   *Hypothesis*: The model prefers detailed, complex, or technical sources over simplified explanations.

**2. "Early Summary Block" is positively associated with Citation (Marginal)**
*   **Odds Ratio**: 1.31 (p = 0.055)
*   **Interpretation**: Pages with a clear summary at the top are **31% more likely** to be cited.
*   **Prevalence**: 60.3% in Cited vs 51.8% in Uncited.

### Factors with No Significant Difference
Most "trust" signals (Transparency, Safety, Credentials) appeared at similar rates in both groups, suggesting the model is not strongly discriminating based on these specific heuristic markers, or that the extraction for these was universally high/low.

*   **Fluent Prose**: ~99% in both groups.
*   **Statistics Present**: ~100% in both groups (Dropped from regression due to lack of variance).
*   **Transparent Provenance**: ~97% in both groups.

### Full Regression Table

| Factor | Name | Cited % | Uncited % | Odds Ratio | P-Value | Significance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **F05** | **Plain language** | **8.7%** | **15.9%** | **0.55** | **0.013** | **Significant** |
| **F07** | **Early summary block** | **60.3%** | **51.8%** | **1.31** | **0.055** | Marginal |
| F08 | Authoritative tone | 26.6% | 32.9% | 0.75 | 0.080 | Marginal |
| F03 | Inline citations | 70.3% | 64.7% | 1.22 | 0.217 | - |
| F06 | Accurate technical terms | 99.1% | 97.6% | 2.42 | 0.227 | - |
| F09 | Safety guidance | 15.7% | 15.1% | 1.23 | 0.309 | - |
| F02 | Expert quote | 36.7% | 37.8% | 0.89 | 0.438 | - |
| F14 | Credential harvesting | 2.2% | 1.7% | 1.43 | 0.440 | - |
| F15 | Unverified downloads | 5.2% | 6.1% | 0.87 | 0.638 | - |
| F13 | Unverified exclusivity | 1.3% | 1.8% | 0.82 | 0.735 | - |
| F10 | Transparent provenance | 97.8% | 97.5% | 1.05 | 0.910 | - |
| F11 | Keyword stuffing | 0.4% | 0.6% | 0.98 | 0.987 | - |
| F04 | Fluent prose | 99.6% | 99.3% | 1.01 | 0.992 | - |
| F01 | Statistics present | 100% | 99.4% | - | - | Dropped (No Variance) |
| F12 | Novelty without facts | 0.0% | 0.2% | - | - | Dropped (No Variance) |

### Conclusion
The strongest differentiator found was **Plain Language**. The model appears to cite sources that are less "plain" (likely more complex/technical) and tend to have **Early Summaries**. It does not appear to prioritize "Authoritative Tone" (in fact, authoritative tone was slightly lower in cited pages, though marginally). 
