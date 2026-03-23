# subgraphs/improvement.py
from langchain_ollama import ChatOllama
from config import config
from langgraph.graph import StateGraph, END

from state import ImprovementState
from tools.code_executor import run_code, strip_markdown
from tools.code_analyzer import analyze_code


# ── LLM ──────────────────────────────────────────────────────────────────────

llm = ChatOllama(model=config.model, temperature=config.temperature)

# ── Nœuds ────────────────────────────────────────────────────────────────────

def generate_improvement(state: ImprovementState) -> dict:
    """
    Demande au LLM de produire une version améliorée du code source.
    Premier appel : améliore le code original.
    Appels suivants (retry) : ce nœud n'est PAS rappelé — c'est fix_code.
    """
    analysis = analyze_code(state["source_code"])

    prompt = f"""Tu es un expert Python. Améliore le code suivant.

Contexte de l'analyse statique :
{analysis.to_prompt_context()}

Code source :
```python
{state["source_code"]}
```

Règles strictes :
- Retourne UNIQUEMENT le code Python amélioré, sans explication
- Pas de balises markdown, pas de ```python
- Le code doit être exécutable tel quel
"""
    response = llm.invoke(prompt)
    return {"generated_code": strip_markdown(response.content)}


def execute_code(state: ImprovementState) -> dict:
    """
    Exécute le code généré dans un subprocess isolé.
    Appelé après generate_improvement ET après fix_code.
    """
    result = run_code(state["generated_code"], timeout=config.code_execution_timeout)
    return {
        "execution_stdout": result.stdout,
        "execution_stderr": result.stderr,
        "execution_success": result.success,
        "current_error": "" if result.success else result.summary(),
    }


def fix_code(state: ImprovementState) -> dict:
    """
    Demande au LLM de corriger le code en s'appuyant sur l'erreur.
    Appelé uniquement quand execution_success est False.
    """
    prompt = f"""Tu es un expert Python. Le code suivant produit une erreur.

Code :
```python
{state["generated_code"]}
```

Erreur obtenue :
{state["current_error"]}

Règles strictes :
- Retourne UNIQUEMENT le code Python corrigé, sans explication
- Pas de balises markdown, pas de ```python
- Le code doit être exécutable tel quel
"""
    response = llm.invoke(prompt)
    return {
        "generated_code": strip_markdown(response.content),
        "retry_count": state["retry_count"] + 1,
    }


# ── Routeur conditionnel ──────────────────────────────────────────────────────

def should_retry(state: ImprovementState) -> str:
    """
    Décide quelle arête emprunter après execute_code.

    Retourne :
        "end"   → succès, on sort du subgraph
        "fix"   → erreur ET retry disponibles
        "abort" → erreur ET max_retries atteint
    """
    if state["execution_success"]:
        return "end"
    if state["retry_count"] < state["max_retries"]:
        return "fix"
    return "abort"


# ── Construction du subgraph ──────────────────────────────────────────────────

def build_improvement_subgraph() -> StateGraph:
    graph = StateGraph(ImprovementState)

    # Nœuds
    graph.add_node("generate_improvement", generate_improvement)
    graph.add_node("execute_code", execute_code)
    graph.add_node("fix_code", fix_code)

    # Arêtes fixes
    graph.set_entry_point("generate_improvement")
    graph.add_edge("generate_improvement", "execute_code")
    graph.add_edge("fix_code", "execute_code")   # boucle : fix retourne à execute

    # Arête conditionnelle après execute_code
    graph.add_conditional_edges(
        "execute_code",          # nœud source
        should_retry,            # fonction de routage
        {
            "end":   END,        # clé retournée → destination
            "fix":   "fix_code",
            "abort": END,
        }
    )

    return graph.compile()


# Instance compilée — importée par le graphe principal
improvement_subgraph = build_improvement_subgraph()

