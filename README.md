# StudyBud

StudyBud is an AI-powered learning tool that extracts key concepts from PDFs or text and finds relevant educational videos on YouTube.

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Database](#database)
- [Module Overview](#module-overview)
- [Usage](#usage)
- [Dependencies](#dependencies)

## Features

- Upload PDFs to extract key concepts
- Enter custom text for analysis
- Extract key concepts using Google Gemini AI
- Search for relevant YouTube videos per concept
- Cache results and avoid duplicate processing with SQLite

## Project Structure

```text
c:\Users\vishn\PROJECT\STUDYBUD
├── gemini.py            # KeyConceptExtractor for AI concept extraction
├── stringextractor.py   # StringExtractor for parsing AI output
├── youtube.py           # YouTubeSearcher for finding videos via yt-dlp
├── hash_check.py        # PDFDuplicateChecker for deduplication and key concepts caching
├── video_storage.py     # VideoStorage for storing and retrieving video links
├── main.py              # Streamlit web interface application
├── file_hashes.db       # SQLite database for file hashes and data (auto-generated)
├── pyproject.toml       # Project metadata and dependencies
├── uv.lock              # Dependency lock file for uv package manager
├── .env.example         # Example environment variables file
└── README.md            # Project documentation
```




### Using uv

1. Install `uv` (if not already installed):
   ```powershell
   pip install uv

   ```
2. Install dependencies in pyproject.toml via `uv`:
   ```powershell
   uv run pyproject.toml
   ```

## Environment Variables

Rename `.env.example` to `.env` and provide your Gemini API key:

```powershell
Rename-Item .env.example .env
```

Edit `.env`:

```ini
GEMINI_API_KEY="your-api-key-here"
```

## Database

The application uses SQLite (`file_hashes.db`) to cache:
- Processed PDF file hashes
- Extracted key concepts for each file
- Retrieved YouTube video links per file

This avoids re-processing duplicate files and speeds up repeated analyses.

## Module Overview

- **gemini.py**: Defines `KeyConceptExtractor` which uses Google Gemini AI to extract key concepts from PDFs or text.
- **stringextractor.py**: Defines `StringExtractor` which parses AI output to extract a Python list of concepts.
- **youtube.py**: Defines `YouTubeSearcher` using `yt-dlp` to search YouTube for videos matching each concept.
- **hash_check.py**: Defines `PDFDuplicateChecker` which computes SHA-256 hashes and caches key concepts in SQLite.
- **video_storage.py**: Defines `VideoStorage` which stores and retrieves video URLs in SQLite.
- **main.py**: Streamlit application combining all modules, handling the user interface, file upload, and session state.

## Usage

Run the Streamlit app:

```powershell
streamlit run main.py
```

1. In the web interface, select **Upload PDF** or **Enter Text**.
2. For PDFs, upload a file; the app checks for duplicates.
3. Extract concepts and click **Find YouTube Videos**.
4. View or re-run searches; cached results are retrieved instantly if available.

## Dependencies

Managed via `pyproject.toml` and `uv.lock`. Key packages:
- `google-genai`: Google Gemini AI client
- `yt-dlp`: YouTube video downloader for search
- `streamlit`: Web app framework
- `python-dotenv`: Environment variable loader
- `uv`: Dependency manager (optional)