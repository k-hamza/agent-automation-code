import sys
sys.path.insert(0, ".")

from tools.code_executor import run_pytest

# Le code généré par le LLM sans les imports
broken_tests = """
def test_multiply():
    assert multiply(2, 3) == 6
"""

result = run_pytest(broken_tests)
print(f"returncode : {result.returncode}")
print(f"stdout :\n{result.stdout}")
print(f"stderr :\n{result.stderr}")


