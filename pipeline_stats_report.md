# Dataset Pipeline Statistics

## 1. Source Data
*   **Total Original Conversations**: 282
    *   Source: `conversations_files/` directory
*   **Total Cited URLs**: 251
    *   Source: `cited_urls.csv`
*   **Total Uncited URLs (Raw)**: 25,194
    *   Source: `uncited_urls.csv`
*   **Unique Cited Conversations**: 172
    *   Source: `unique_cited_conversations.csv`
    *   *Note: These are conversations that contain at least one cited link.*

## 2. Filtration Process (Uncited URLs)
We filtered the raw uncited URLs to ensure relevance and quality.

### Stage 1: Context Relevance
We restricted the dataset to uncited URLs that appeared in **cited conversations only**.
*   **Input**: 25,194 Raw URLs
*   **Output**: 16,180 URLs
*   **Source**: `uncited_in_cited_conversations.csv`

### Stage 2: Substantial Content Filter
We removed URLs unlikely to contain parseable text content based on file extensions and specific domains.
*   **Criteria**:
    *   **Excluded Extensions**: `.pdf`, `.jpg`, `.png`, `.gif`, `.doc/x`, `.xls/x`, `.ppt/x`, `.zip`, `.mp3/4`.
    *   **Excluded Domains**: `youtube.com`, `vimeo.com`, `tiktok.com`, `docs.google.com` (and variants), `notion.so`, `scribd.com`, `pinterest.com`.
*   **Input**: 16,180 URLs
*   **Output**: 12,892 URLs
*   **Source**: `filtered_uncited_urls.csv`

## 3. Data Collection Status
Agents attempted to visit and extract features for all survival URLs.
*   **Cited URLs Processed**: 251 (100% of target)
*   **Uncited URLs Processed**: 12,892 (100% of filtered target)
*   **Total Records**: 13,143 (`analysis_dataset.csv`)

## 4. Final Analyzed Dataset
For the regression analysis, we only included pages that were **successfully fetched** by the agent.
*   **Filter Condition**: `fetch_status == 'success'`
*   **Total Final Rows**: 9,587
*   **Source**: `analysis_dataset_cleaned.csv`
    *   *Drop-off from failed fetches: ~3,556 URLs (27%)*
