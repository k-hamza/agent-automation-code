# debug_pytest.py
import sys
sys.path.insert(0, ".")

from tools.code_executor import run_pytest

source_code = """def multiply(a, b):
    return a * b

def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)

print(factorial(5))
"""

# Ce que le LLM génère réellement en première tentative
generated_tests = """def test_multiply():
    assert multiply(2, 3) == 6
    assert multiply(0, 5) == 0
    assert multiply(-2, 3) == -6

def test_factorial_nominal():
    assert factorial(0) == 1
    assert factorial(5) == 120
"""

full_code = f"{source_code}\n\n{generated_tests}"
print("=== Code complet envoyé à pytest ===")
print(full_code)
print("=" * 40)

result = run_pytest(full_code)
print(f"returncode : {result.returncode}")
print(f"--- stdout ---\n{result.stdout}")