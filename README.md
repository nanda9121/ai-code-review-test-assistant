# AI Code Review & Test Generation Assistant

A Streamlit project that combines local Python AST checks with Gemini-powered
code review and test generation for source code across programming languages.

## Features

- Paste code in any language or upload a text-based source file. Common language
  extensions are detected automatically; select a language manually when needed.
- Run local Python checks for syntax errors, mutable default arguments, broad or ignored
  exceptions, and dynamic `eval`/`exec` calls.
- Request a Gemini review with prioritized findings, improvement suggestions, and
  tests drafted in the language's common testing framework.
- Download generated tests or validation examples.
- Review submitted and generated code without executing either one.

Local AST checks are currently Python-only. Other languages can be reviewed and
have tests generated through Gemini.

## Requirements

- Python 3.10 or newer
- A Gemini API key for AI reviews (local checks work without one)

## Setup

From the project directory, create and activate a virtual environment, then install
dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).
Google offers a free tier for some Gemini models, subject to model availability,
region, and usage limits. Check the current terms and quotas in AI Studio.

Create a `.env` file in the project root (next to `app.py`) and add your key:

```text
GEMINI_API_KEY=your-api-key
```

The app loads `.env` automatically. The file is excluded from Git, so your key
won't be committed. The app defaults to `gemini-3.5-flash-lite`; optionally add
`GEMINI_MODEL` to `.env` to override it.

Start the app:

```powershell
streamlit run app.py
```

Without a key in `.env`, use **Run local checks**. AI reviews send the submitted
source code to Google's Gemini API. Do not submit code containing secrets or code
you are not permitted to share. Keep your API key private and out of source control.

## Run tests

```powershell
python -m pytest
```

## Project layout

```text
app.py                       Streamlit user interface
code_review_assistant/
  analyzer.py                Local, non-executing Python checks
  llm.py                     LLM request and response validation
tests/                       Unit tests
```
