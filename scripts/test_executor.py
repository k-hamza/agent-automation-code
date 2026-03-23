import sys
sys.path.insert(0, ".")

from tools.code_executor import run_code

# Cas 1 — code valide
r = run_code("print('hello world')")
print(r.success)    # True
print(r.stdout)     # hello world\n
print(r.summary())  # Succès.\nhello world

# Cas 2 — erreur de syntaxe
r = run_code("def foo(\n  print('oops')")
print(r.success)    # False
print(r.stderr)     # SyntaxError: ...
print(r.summary())  # ERREUR (code 1) : ...

# Cas 3 — timeout (boucle infinie)
r = run_code("while True: pass", timeout=2)
print(r.timed_out)  # True
print(r.success)    # False
print(r.summary())  # ERREUR : timeout — boucle infinie probable