# Feature Analysis Workflow Documentation

This document outlines the complete workflow used to analyze the credibility factors of URLs found in conversation logs, comparing those that were "cited" (used as references) versus those that were "uncited" (mentioned in text but not used as a primary source).

## Dataset Statistics Overview

### Source Data
*   **Total Original Conversations**: 282
*   **Unique Cited Conversations**: 172 (Conversations containing at least one citation)

### URL Counts
| Category | Total Found | Filtered (Relevant) | Content Filtered | Successfully Analyzed |
| :--- | :--- | :--- | :--- | :--- |
| **Cited URLs** | 251 | - | - | **229** |
| **Uncited URLs** | 25,194 | 16,180 | 12,892 | **9,358** |

*   **Context Relevance**: We restricted uncited URLs to those appearing in the 172 cited conversations.
*   **Content Filter**: We removed non-content files (PDFs, Images) and non-content domains (YouTube, Docs).
*   **Successfully Analyzed**: URLs that were successfully fetched and processed by the AI Agent (excluding 404s, timeouts).

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
| F07 | Early summary block | 138 | 4845 | 60.3% | 51.8% | 0.2888 | 1.3348 | [1.0115, 1.7616] | 0.0413 |
| F03 | Inline citations | 161 | 6055 | 70.3% | 64.7% | 0.1863 | 1.2048 | [0.8864, 1.6376] | 0.2341 |
| F06 | Accurate technical terms | 227 | 9132 | 99.1% | 97.6% | 0.8355 | 2.3059 | [0.5490, 9.6853] | 0.2539 |
| F14 | Credential harvesting | 5 | 161 | 2.2% | 1.7% | 0.3527 | 1.4228 | [0.5748, 3.5222] | 0.4457 |
| F02 | Expert quote | 84 | 3539 | 36.7% | 37.8% | -0.1012 | 0.9037 | [0.6813, 1.1987] | 0.4825 |
| F15 | Unverified downloads or scripts | 12 | 572 | 5.2% | 6.1% | -0.2063 | 0.8136 | [0.4512, 1.4670] | 0.4927 |
| F13 | Unverified exclusivity | 3 | 168 | 1.3% | 1.8% | -0.2387 | 0.7876 | [0.2489, 2.4930] | 0.6847 |
| F11 | Keyword stuffing | 1 | 52 | 0.4% | 0.6% | -0.1030 | 0.9022 | [0.1234, 6.5943] | 0.9192 |
| F10 | Transparent provenance | 224 | 9125 | 97.8% | 97.5% | 0.0225 | 1.0227 | [0.4138, 2.5274] | 0.9612 |
| F04 | Fluent prose | 228 | 9297 | 99.6% | 99.3% | -0.0478 | 0.9533 | [0.1252, 7.2575] | 0.9632 |
| F09 | Safety guidance | 36 | 1415 | 15.7% | 15.1% | 0.0023 | 1.0023 | [0.6972, 1.4409] | 0.9899 |
| F01 | Statistics present | 229 | 9299 | 100.0% | 99.4% | 0.0000 | 0.0000 | [0.0000, 0.0000] | 1.0000 |
| F12 | Novelty without facts | 0 | 17 | 0.0% | 0.2% | 0.0000 | 0.0000 | [0.0000, 0.0000] | 1.0000 |
| F05 | Plain language | 20 | 1485 | 8.7% | 15.9% | 0.0000 | 0.0000 | [0.0000, 0.0000] | 1.0000 (Excluded) |
| F08 | Authoritative tone | 61 | 3078 | 26.6% | 32.9% | 0.0000 | 0.0000 | [0.0000, 0.0000] | 1.0000 (Excluded) |

*Note: F05 and F08 were manually excluded from this analysis iteration. F01 and F12 were dropped due to perfect separation.*

**Key Files Inventory:**
- `batch_run_agent.py`: Principal script for data collection.
- `clean_analysis_data.py`: Pre-processing pipeline.
- `analyze_factors_regression.py`: Statistical engine.
- `analysis_dataset_cleaned.csv`: The final dataset used for the model.
- `factor_analysis_results.csv`: The final output table.
