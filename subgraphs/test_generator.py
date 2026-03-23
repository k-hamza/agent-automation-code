from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END

from state import TestState
from tools.code_executor import run_pytest, strip_markdown
from tools.code_analyzer import analyze_code
from config import config


llm = ChatOllama(model=config.model, temperature=config.temperature)


# ── Nœuds ────────────────────────────────────────────────────────────────────

def generate_tests(state: TestState) -> dict:
    """Demande au LLM de générer des tests pytest pour le code source."""
    analysis = analyze_code(state["source_code"])

    prompt = f"""Tu es un expert Python. Génère des tests pytest pour le code suivant.

Contexte :
{analysis.to_prompt_context()}

Code source :
{state["source_code"]}

Règles strictes :
- Retourne UNIQUEMENT le code Python des tests, sans explication
- Pas de balises markdown
- Les fonctions de test commencent par test_
- Tu peux appeler directement les fonctions du code source
- Couvre les cas nominaux ET les cas limites
"""
    response = llm.invoke(prompt)
    return {"generated_code": strip_markdown(response.content)}


def execute_tests(state: TestState) -> dict:
    """
    Injecte le code source avant les tests puis exécute pytest.
    Le LLM n'a pas à recopier le code source — on le fait nous-mêmes.
    """
    # Injection garantie du code source en tête du fichier de tests
    full_code = f"{state['source_code']}\n\n{state['generated_code']}"

    result = run_pytest(full_code, timeout=config.test_execution_timeout)
    return {
        "execution_stdout": result.stdout,
        "execution_stderr": result.stderr,
        "execution_success": result.success,
        "current_error": "" if result.success else result.summary(),
    }


def fix_tests(state: TestState) -> dict:
    """Demande au LLM de corriger les tests en s'appuyant sur l'erreur pytest."""
    prompt = f"""Tu es un expert Python. Les tests pytest suivants échouent.

Tests :
{state["generated_code"]}

Sortie pytest :
{state["current_error"]}

Règles strictes :
- Retourne UNIQUEMENT le code Python des tests corrigés, sans explication
- Pas de balises markdown
- Corrige uniquement ce qui cause l'échec
- Ne recopie pas le code source, uniquement les tests
"""
    response = llm.invoke(prompt)
    return {
        "generated_code": strip_markdown(response.content),
        "retry_count": state["retry_count"] + 1,
    }


# ── Routeur ───────────────────────────────────────────────────────────────────

def should_retry_tests(state: TestState) -> str:
    if state["execution_success"]:
        return "end"
    if state["retry_count"] < state["max_retries"]:
        return "fix"
    return "abort"


# ── Construction ──────────────────────────────────────────────────────────────

def build_test_subgraph() -> StateGraph:
    graph = StateGraph(TestState)

    graph.add_node("generate_tests", generate_tests)
    graph.add_node("execute_tests", execute_tests)
    graph.add_node("fix_tests", fix_tests)

    graph.set_entry_point("generate_tests")
    graph.add_edge("generate_tests", "execute_tests")
    graph.add_edge("fix_tests", "execute_tests")

    graph.add_conditional_edges(
        "execute_tests",
        should_retry_tests,
        {"end": END, "fix": "fix_tests", "abort": END}
    )

    return graph.compile()


test_subgraph = build_test_subgraph()