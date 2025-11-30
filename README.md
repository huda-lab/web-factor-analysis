# Feature Extractor

A Python tool that uses Google's Gemini models to extract indexability factors and other salient features from web pages.

## Overview

This tool fetches the content of a specified URL, cleans it, and uses the Gemini API to analyze it based on a comprehensive set of 15 factors (defined in `prompt.py`). The output is a structured JSON object containing the analysis, evidence, and an overall indexability score.

## Prerequisites

- Python 3.8+
- A Google Gemini API Key

## Installation

1.  **Clone the repository** (if applicable) or navigate to the project directory.

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: The core dependencies for this script are `google-generativeai`, `beautifulsoup4`, `requests`, and `python-dotenv`.*

3.  **Set up your API Key**:
    - Create a `.env` file in the project root:
      ```bash
      cp .env.example .env
      ```
    - Edit `.env` and add your Gemini API key:
      ```
      GEMINI_API_KEY=your_api_key_here
      ```
    - Alternatively, you can pass the API key via the command line (see Usage).

## Usage

Run the script using Python:

```bash
python3 extract_features.py <URL>
```

### Examples

**Basic usage:**
```bash
python3 extract_features.py https://www.example.com
```

**Save output to a file:**
```bash
python3 extract_features.py https://www.example.com --output results.json
```

**Provide API key directly:**
```bash
python3 extract_features.py https://www.example.com --api-key AIzaSy...
```

## Output Format

The tool returns a JSON object with the following structure:

```json
{
  "meta": {
    "url": "https://...",
    "timestamp": "ISO-8601 timestamp",
    "language": "en",
    "fetch_status": "success"
  },
  "factors": [
    {
      "id": "F01",
      "name": "Statistics present",
      "present": true,
      "probability": 0.95,
      "evidence": ["Quote from the page..."]
    },
    ...
  ],
  "summary": {
    "indexability_score": 85.5,
    "key_observations": "Brief summary of findings...",
    "content_gaps": ["Missing elements..."]
  }
}
```

## Files

- `extract_features.py`: The main script.
- `prompt.py`: Contains the system prompt and factor definitions used by Gemini.
