from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from config import config
from state import AgentState
from tools.code_analyzer import analyze_code
from subgraphs.improvement import improvement_subgraph
from subgraphs.test_generator import test_subgraph


llm = ChatOllama(model=config.model, temperature=config.temperature)


# ── Nœuds ────────────────────────────────────────────────────────────────────

def load_and_analyze(state: AgentState) -> dict:
    """Lit le fichier source et produit l'analyse statique."""
    with open(state["file_path"], "r") as f:
        source = f.read()

    analysis = analyze_code(source)
    return {
        "source_code": source,
        "analysis": analysis.to_prompt_context(),
    }


def synthesize(state: AgentState) -> dict:
    """Produit le rapport final lisible."""
    status = "✓ Succès" if state["execution_success"] else "✗ Échec"
    task_label = "Amélioration" if state["task"] == "improve" else "Tests"

    report = f"""=== Rapport agent ===
Tâche        : {task_label}
Fichier      : {state["file_path"]}
Résultat     : {status}
Tentatives   : {state["retry_count"]}

--- Code produit ---
{state["generated_code"]}
"""
    return {"final_report": report}


# ── Routeur ───────────────────────────────────────────────────────────────────

def route_task(state: AgentState) -> str:
    """Dirige vers le subgraph approprié selon state["task"]."""
    if state["task"] == "improve":
        return "improve"
    return "test"


# ── Construction ──────────────────────────────────────────────────────────────

def build_graph(checkpointer=None):
    graph = StateGraph(AgentState)

    # Nœuds simples
    graph.add_node("load_and_analyze", load_and_analyze)
    graph.add_node("synthesize", synthesize)

    # Subgraphs enregistrés comme nœuds
    graph.add_node("improvement_subgraph", improvement_subgraph)
    graph.add_node("test_subgraph", test_subgraph)

    # Arêtes
    graph.set_entry_point("load_and_analyze")

    graph.add_conditional_edges(
        "load_and_analyze",
        route_task,
        {
            "improve": "improvement_subgraph",
            "test":    "test_subgraph",
        }
    )

    # Les deux subgraphs convergent vers synthesize
    graph.add_edge("improvement_subgraph", "synthesize")
    graph.add_edge("test_subgraph", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile(checkpointer=checkpointer)

