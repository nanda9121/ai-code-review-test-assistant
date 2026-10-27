from code_review_assistant.analyzer import analyze_python


def test_flags_mutable_default_argument() -> None:
    findings = analyze_python("def add_item(item, items=[]):\n    items.append(item)\n    return items\n")

    assert len(findings) == 1
    assert findings[0].title == "Mutable default argument"
    assert findings[0].line == 1


def test_flags_bare_and_ignored_exception() -> None:
    findings = analyze_python("try:\n    work()\nexcept:\n    pass\n")

    assert {finding.title for finding in findings} == {
        "Bare except clause",
        "Exception is ignored",
    }


def test_flags_dynamic_execution() -> None:
    findings = analyze_python("result = eval(expression)\n")

    assert len(findings) == 1
    assert findings[0].title == "Dynamic execution with eval"


def test_reports_syntax_error() -> None:
    findings = analyze_python("def broken(:\n    pass\n")

    assert len(findings) == 1
    assert findings[0].title == "Python syntax error"


def test_clean_code_has_no_findings() -> None:
    assert analyze_python("def add(left, right):\n    return left + right\n") == []
