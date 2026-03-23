from tools.code_analyzer import analyze_code

source = """
import os
from pathlib import Path

def add(a, b):
    return a + b

class Calculator:
    pass

if __name__ == "__main__":
    print(add(1, 2))
"""

a = analyze_code(source)
print(a.functions)           # ['add']
print(a.classes)             # ['Calculator']
print(a.imports)             # ['os', 'pathlib']
print(a.has_main)            # True
print(a.to_prompt_context()) # résumé pour le LLM
