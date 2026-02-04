# Feature Analysis Workflow Documentation

This document outlines the complete workflow used to analyze the credibility factors of URLs found in conversation logs, comparing those that were "cited" (used as references) versus those that were "uncited" (mentioned in text but not used as a primary source).

## 1. Data Collection & Extraction

### URL Extraction
We began by processing the raw conversation logs (JSON format) to identify valid URLs.

*   **Script**: `extract_urls_from_conversations.py`
*   **Process**: 
    1.  Parsed conversation logs.
    2.  Extracted URLs from the `content_references` (labeled as **Cited**).
    3.  extracted all other URLs from the raw message text (labeled as **Uncited**).
*   **Refinement**: We further refined the uncited list to only include URLs appearing in conversations that *also* contained at least one citation to ensure comparable contexts.
    *   **Script**: `extract_uncited_urls_in_cited_conversations.py`

### Filtering
To ensure meaningful analysis, we filtered out low-quality or irrelevant URLs.

*   **Script**: `filter_substantial_urls.py`
*   **Criteria**:  
    *   Excluded file extensions like `.pdf`, `.png`, `.jpg`.
    *   **Included** major social media domains (Facebook, Twitter, Reddit) to capture the full breadth of conversation sources.
    *   Excluded specific video platforms (YouTube, TikTok) and document hosts (Google Docs).
*   **Output**: `filtered_uncited_urls.csv`

## 2. Feature Extraction (AI Agent)

We utilized an OpenAI-powered Agent to evaluate each URL against 15 specific factors.

### The Agent
*   **Script**: `extract_features_with_agent.py`
*   **Model**: GPT-5.2 (configured via `agents` SDK).
*   **Task**: Visit a URL and determine the presence (True/False) of 15 factors (F01–F15), such as "Statistics present", "Expert quote", "Fluent prose", etc.
*   **Output format**: JSON file per URL containing factor booleans and confidence scores.

### Batch Processing
 To process the lists efficiently, we built a batch runner.
 
*   **Script**: `batch_run_agent.py`
*   **Features**:
    *   Parallel processing (AsyncIO/Semaphore).
    *   Skip logic for already processed URLs.
    *   Support for custom output directories.
*   **Execution**:
    *   **Cited Cohort**: Processed `cited_urls.csv` -> Output to `agent_results_cited/`.
    *   **Uncited Cohort**: Processed `filtered_uncited_urls.csv` -> Output to `agent_results_uncited/`.

## 3. Data Compilation & Cleaning

### Aggregation
We merged the individual JSON result files into a single structured dataset.

*   **Script**: `compile_analysis_csv.py`
*   **Process**:
    *   Reads all JSONs from `agent_results_cited/` and `agent_results_uncited/`.
    *   Extracts metadata (fetch status, language).
    *   Extracts Factor Boolean (True/False) AND Confidence Score (0.0 - 1.0).
*   **Output**: `analysis_dataset.csv` (Raw data).

### Cleaning & Encoding
We prepared the data for statistical analysis.

*   **Script**: `clean_analysis_data.py`
*   **Process**:
    1.  **Filter**: Kept only rows where `fetch_status == 'success'`.
    2.  **Encode**: Converted Boolean True/False to Integer 1/0.
    3.  **Threshold (Important)**: Applied a confidence threshold (e.g., 0.7). If the Agent marked a factor as Present (True) but the confidence score was < 0.7, it was coerced to 0 (False) to reduce false positives.
*   **Output**: `analysis_dataset_cleaned.csv`

## 4. Statistical Analysis

Finally, we performed a multivariate logistic regression to determine which factors predict whether a URL is cited.

*   **Script**: `analyze_factors_regression.py`
*   **Method**: Multivariate Logistic Regression (`is_cited ~ F01 + F02 + ... + F15`).
*   **Checks**:
    *   **Perfect Separation**: Automatically drops factors that are 0% or 100% present in either group (as they break the regression model).
    *   **Variance**: Drops constant columns.
*   **Metrics Calculated**:
    *   **Prevalence**: % presence in Cited vs. Uncited groups.
    *   **Odds Ratio (OR)**: The strength of association (>1 means more likely to be cited, <1 means less likely).
    *   **P-Value**: Statistical significance.
    *   **95% Confidence Interval**.
*   **Output**: `factor_analysis_results.csv`

## Summary of Results
The final results table (`factor_analysis_results.csv`) highlights which credibility markers are most strongly associated with the AI's decision to cite a source.

### Regression Analysis Table

| Factor | Name | Count Cited | Count Uncited | Prev Cited | Prev Uncited | Coefficient | Odds Ratio | CI 95% | P Value |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| F01 | Statistics present | 229 | 9299 | 100.0% | 99.4% | 0.0000 | 0.0000 | [0.0000, 0.0000] | 1.0000 |
| F02 | Expert quote | 84 | 3539 | 36.7% | 37.8% | -0.1119 | 0.8941 | [0.6740, 1.1861] | 0.4375 |
| F03 | Inline citations | 161 | 6055 | 70.3% | 64.7% | 0.1947 | 1.2150 | [0.8918, 1.6552] | 0.2171 |
| F04 | Fluent prose | 228 | 9297 | 99.6% | 99.3% | 0.0099 | 1.0099 | [0.1325, 7.6977] | 0.9924 |
| F05 | Plain language | 20 | 1485 | 8.7% | 15.9% | -0.6034 | 0.5469 | [0.3406, 0.8781] | 0.0125 |
| F06 | Accurate technical terms | 227 | 9132 | 99.1% | 97.6% | 0.8836 | 2.4196 | [0.5763, 10.1591] | 0.2274 |
| F07 | Early summary block | 138 | 4845 | 60.3% | 51.8% | 0.2728 | 1.3137 | [0.9940, 1.7361] | 0.0551 |
| F08 | Authoritative tone | 61 | 3078 | 26.6% | 32.9% | -0.2921 | 0.7467 | [0.5382, 1.0359] | 0.0804 |
| F09 | Safety guidance | 36 | 1415 | 15.7% | 15.1% | 0.2033 | 1.2255 | [0.8283, 1.8131] | 0.3090 |
| F10 | Transparent provenance | 224 | 9125 | 97.8% | 97.5% | 0.0522 | 1.0536 | [0.4259, 2.6063] | 0.9100 |
| F11 | Keyword stuffing | 1 | 52 | 0.4% | 0.6% | -0.0168 | 0.9833 | [0.1342, 7.2078] | 0.9868 |
| F12 | Novelty without facts | 0 | 17 | 0.0% | 0.2% | 0.0000 | 0.0000 | [0.0000, 0.0000] | 1.0000 |
| F13 | Unverified exclusivity | 3 | 168 | 1.3% | 1.8% | -0.1996 | 0.8190 | [0.2584, 2.5957] | 0.7345 |
| F14 | Credential harvesting | 5 | 161 | 2.2% | 1.7% | 0.3575 | 1.4298 | [0.5767, 3.5444] | 0.4402 |
| F15 | Unverified downloads or scripts | 12 | 572 | 5.2% | 6.1% | -0.1418 | 0.8678 | [0.4805, 1.5671] | 0.6381 |

**Key Files Inventory:**
- `batch_run_agent.py`: Principal script for data collection.
- `clean_analysis_data.py`: Pre-processing pipeline.
- `analyze_factors_regression.py`: Statistical engine.
- `analysis_dataset_cleaned.csv`: The final dataset used for the model.
- `factor_analysis_results.csv`: The final output table.
