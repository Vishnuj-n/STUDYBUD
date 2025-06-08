# StudyBud

StudyBud is an AI-powered learning tool that extracts key concepts from PDFs or text and finds relevant educational videos on YouTube.

## Features

- Upload PDFs or enter text to analyze
- Extract key concepts using Google's Gemini AI
- Find relevant YouTube videos for each concept
- User-friendly Streamlit interface

## Setup

1. Install dependencies:
   ```
   pip install -e .
   ```
   
2. Set up your Gemini API key:
   ```
   # On Windows
   $env:GEMINI_API_KEY = "your-api-key"
   
   # On Linux/macOS
   export GEMINI_API_KEY="your-api-key"
   ```

3. Run the app:
   ```
   streamlit run main.py
   ```

## How to Use

1. Use the "Upload PDF" tab to analyze a PDF document or "Enter Text" to analyze your own text
2. The app will extract key concepts using Google's Gemini AI
3. Click "Find YouTube Videos" to search for relevant educational content
4. View and watch recommended videos directly in the app

## Components

- **KeyConceptExtractor**: Uses Gemini AI to identify key concepts in documents
- **StringExtractor**: Extracts structured data from AI outputs
- **YouTubeSearcher**: Finds relevant videos for each concept