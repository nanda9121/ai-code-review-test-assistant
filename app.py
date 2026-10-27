import streamlit as st
from openai import OpenAIError

from code_review_assistant.analyzer import Finding, analyze_python
from code_review_assistant.llm import (
    AssistantConfigurationError,
    AssistantResponseError,
    MAX_SOURCE_CHARS,
    review_code,
)

LANGUAGES = [
    "Auto-detect",
    "Python",
    "JavaScript",
    "TypeScript",
    "Java",
    "C",
    "C++",
    "C#",
    "Go",
    "Rust",
    "PHP",
    "Ruby",
    "Swift",
    "Kotlin",
    "Dart",
    "SQL",
    "HTML",
    "CSS",
    "Shell / Bash",
    "JSON",
    "YAML",
    "Other",
]

EXTENSION_LANGUAGES = {
    ".py": "Python",
    ".pyw": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".c": "C",
    ".h": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".php": "PHP",
    ".rb": "Ruby",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".dart": "Dart",
    ".sql": "SQL",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".sh": "Shell / Bash",
    ".bash": "Shell / Bash",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
}

CODE_FORMATS = {
    "Python": "python",
    "JavaScript": "javascript",
    "TypeScript": "typescript",
    "Java": "java",
    "C": "c",
    "C++": "cpp",
    "C#": "csharp",
    "Go": "go",
    "Rust": "rust",
    "PHP": "php",
    "Ruby": "ruby",
    "Swift": "swift",
    "Kotlin": "kotlin",
    "Dart": "dart",
    "SQL": "sql",
    "HTML": "html",
    "CSS": "css",
    "Shell / Bash": "bash",
    "JSON": "json",
    "YAML": "yaml",
}


st.set_page_config(page_title="AI Code Review Assistant", page_icon="🧪", layout="wide")
st.title("AI Code Review & Test Generation Assistant")
st.caption("Review code across programming languages and generate tests for relevant edge cases.")

with st.sidebar:
    st.subheader("What this app does")
    st.markdown(
        "- Uses Google Gemini to review source code in any programming language.\n"
        "- Generates test suggestions using language-appropriate conventions.\n"
        "- Runs local AST checks for Python only.\n"
        "- Never executes submitted code or generated tests."
    )
    st.info("AI reviews send your source code to Google Gemini. Free-tier access and limits vary.")

uploaded_file = st.file_uploader("Upload a source-code file (text-based)")
uploaded_source = ""
detected_language = "Auto-detect"
if uploaded_file is not None:
    suffix = "." + uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else ""
    detected_language = EXTENSION_LANGUAGES.get(suffix, "Auto-detect")
    try:
        uploaded_source = uploaded_file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        st.error("Could not read this file as UTF-8 text. Upload a text-based source-code file.")

language = st.selectbox(
    "Code language",
    LANGUAGES,
    index=LANGUAGES.index(detected_language),
    help="Detected from the uploaded file extension when possible. Choose a language for pasted code.",
)
source = st.text_area(
    "Source code",
    value=uploaded_source,
    height=320,
    placeholder="Paste code in any language here, or upload a source file above...",
)

local_column, ai_column = st.columns(2)
with local_column:
    run_local = st.button("Run local Python checks", use_container_width=True)
with ai_column:
    run_ai = st.button("Review with AI + generate tests", type="primary", use_container_width=True)

if run_local or run_ai:
    st.session_state.pop("local_findings", None)
    st.session_state.pop("local_check_language", None)
    st.session_state.pop("ai_review", None)
    if not source.strip():
        st.error("Paste or upload source code before starting an analysis.")
    elif len(source) > MAX_SOURCE_CHARS:
        st.error(f"Source code exceeds the {MAX_SOURCE_CHARS:,}-character limit.")
    else:
        effective_language = language
        if effective_language == "Auto-detect":
            effective_language = detected_language
        elif effective_language == "Other":
            effective_language = "Auto-detect"
        if (run_local or run_ai) and effective_language == "Python":
            st.session_state["local_findings"] = analyze_python(source)
            st.session_state["local_check_language"] = effective_language
        elif run_local or run_ai:
            st.session_state["local_check_language"] = effective_language
        if run_ai:
            try:
                st.session_state["ai_review"] = review_code(source, effective_language)
            except AssistantConfigurationError as error:
                st.error(str(error))
            except AssistantResponseError as error:
                st.error(f"Could not use the AI response: {error}")
            except OpenAIError as error:
                st.error(f"The AI provider request failed: {error}")
            except ValueError as error:
                st.error(str(error))

findings: list[Finding] = st.session_state.get("local_findings", [])
if "local_check_language" in st.session_state:
    st.subheader("Local checks")
    if st.session_state["local_check_language"] != "Python":
        st.info("Local AST checks currently support Python only. Use AI review for other languages.")
    elif not findings:
        st.success("No issues were found by the local heuristic checks.")
    else:
        for finding in findings:
            st.markdown(
                f"**{finding.severity.upper()} — {finding.title}** "
                f"(line {finding.line})\n\n"
                f"{finding.explanation}\n\n"
                f"Suggestion: {finding.suggestion}"
            )

ai_review = st.session_state.get("ai_review")
if ai_review:
    st.subheader("AI review")
    st.write(ai_review["summary"])
    if not ai_review["findings"]:
        st.success("The AI did not identify specific issues.")
    for finding in ai_review["findings"]:
        line = f" — line {finding['line']}" if finding["line"] is not None else ""
        st.markdown(
            f"**{finding['severity'].upper()} — {finding['title']}**{line}\n\n"
            f"{finding['explanation']}\n\n"
            f"Suggestion: {finding['suggestion']}"
        )

    effective_language = st.session_state.get("local_check_language", "Auto-detect")
    st.subheader("Generated tests")
    st.warning("Review generated tests before use. They have not been executed.")
    st.code(ai_review["tests"], language=CODE_FORMATS.get(effective_language, "text"))
    extension = {
        "Python": "py",
        "JavaScript": "js",
        "TypeScript": "ts",
        "Java": "java",
        "Go": "go",
        "Rust": "rs",
        "C#": "cs",
        "Ruby": "rb",
        "PHP": "php",
        "Kotlin": "kt",
        "Swift": "swift",
        "Dart": "dart",
    }.get(effective_language, "txt")
    st.download_button(
        "Download generated tests",
        data=ai_review["tests"],
        file_name=f"generated_tests.{extension}",
        mime="text/plain",
    )
