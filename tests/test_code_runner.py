from nexum_core.tools.code_runner import CodeRunner

def test_code_runner():
    result = CodeRunner().execute("print(2 + 2)")
    assert result["exit_code"] == 0
    assert result["stdout"].strip() == "4"
