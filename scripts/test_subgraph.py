import sys
sys.path.insert(0, ".")

from subgraphs.improvement import improvement_subgraph

# Code source intentionnellement simple pour un premier test
source = """
def add(a, b):
    return a + b

print(add(2, 3))
"""

initial_state = {
    "source_code": source,
    "generated_code": "",
    "execution_success": False,
    "retry_count": 0,
    "max_retries": 3,
    "execution_stdout": "",
    "execution_stderr": "",
    "current_error": "",
}

print("=== Lancement du subgraph ===")
result = improvement_subgraph.invoke(initial_state)

print(f"\n--- Code généré ---\n{result['generated_code']}")
print(f"\n--- Succès : {result['execution_success']}")
print(f"--- Tentatives : {result['retry_count']}")
print(f"--- Stdout : {result['execution_stdout'].strip()}")


print("\n\n=== Test avec code volontairement cassé ===")

broken_source = """
def divide(a, b):
    return a / b      # bug : pas de gestion division par zéro

print(divide(10, 0))  # va lever ZeroDivisionError
"""

broken_state = {
    "source_code": broken_source,
    "generated_code": "",
    "execution_success": False,
    "retry_count": 0,
    "max_retries": 3,
    "execution_stdout": "",
    "execution_stderr": "",
    "current_error": "",
}

result = improvement_subgraph.invoke(broken_state)

print(f"\n--- Code généré ---\n{result['generated_code']}")
print(f"\n--- Succès : {result['execution_success']}")
print(f"--- Tentatives : {result['retry_count']}")
print(f"--- Stdout : {result['execution_stdout'].strip()}")
print(f"--- Stderr : {result['execution_stderr'].strip()}")

print("\n\n=== Test forçant le retry ===")

# Bug caché : le LLM ne peut pas deviner que `data` sera vide à l'exécution
runtime_error_source = """
import json

data = json.loads('{}')
print(data["missing_key"])
"""

retry_state = {
    "source_code": runtime_error_source,
    "generated_code": "",
    "execution_success": False,
    "retry_count": 0,
    "max_retries": 3,
    "execution_stdout": "",
    "execution_stderr": "",
    "current_error": "",
}

result = improvement_subgraph.invoke(retry_state)

print(f"\n--- Code généré ---\n{result['generated_code']}")
print(f"\n--- Succès : {result['execution_success']}")
print(f"--- Tentatives : {result['retry_count']}")
print(f"--- Stdout : {result['execution_stdout'].strip()}")
print(f"--- Stderr : {result['execution_stderr'].strip()}")

# test_subgraph.py — ajoute ce bloc à la toute fin

print("\n\n=== Test unitaire de fix_code ===")
from subgraphs.improvement import fix_code

state_with_error = {
    "source_code": "# original",
    "generated_code": """import os
result = os.environ["VARIABLE_QUI_NEXISTE_PAS"]
print(result)""",
    "execution_success": False,
    "retry_count": 0,
    "max_retries": 3,
    "execution_stdout": "",
    "execution_stderr": "KeyError: 'VARIABLE_QUI_NEXISTE_PAS'",
    "current_error": "ERREUR (code 1) :\nKeyError: 'VARIABLE_QUI_NEXISTE_PAS'",
}

result = fix_code(state_with_error)
print(f"retry_count après fix : {result['retry_count']}")
print(f"Code corrigé :\n{result['generated_code']}")

