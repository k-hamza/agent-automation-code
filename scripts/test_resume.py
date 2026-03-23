import sys
sys.path.insert(0, ".")

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, END
from graph import build_graph

THREAD_ID = "resume-test"

# ── Étape 1 : lancer le graphe et l'interrompre avant synthesize ──────────────

print("=== Étape 1 : exécution avec interruption avant synthesize ===\n")

with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:

    # On compile le graphe avec interrupt_before
    from state import AgentState
    from tools.code_analyzer import analyze_code
    from subgraphs.improvement import improvement_subgraph
    from subgraphs.test_generator import test_subgraph
    from langchain_ollama import ChatOllama
    from langgraph.graph import StateGraph, END

    llm = ChatOllama(model="qwen2.5:7b", temperature=0)

    def load_and_analyze(state):
        with open(state["file_path"], "r") as f:
            source = f.read()
        analysis = analyze_code(source)
        return {"source_code": source, "analysis": analysis.to_prompt_context()}

    def synthesize(state):
        status = "✓ Succès" if state["execution_success"] else "✗ Échec"
        report = f"Tâche : {state['task']} | Résultat : {status} | Tentatives : {state['retry_count']}"
        return {"final_report": report}

    def route_task(state):
        return "improve" if state["task"] == "improve" else "test"

    graph = StateGraph(AgentState)
    graph.add_node("load_and_analyze", load_and_analyze)
    graph.add_node("synthesize", synthesize)
    graph.add_node("improvement_subgraph", improvement_subgraph)
    graph.add_node("test_subgraph", test_subgraph)
    graph.set_entry_point("load_and_analyze")
    graph.add_conditional_edges(
        "load_and_analyze", route_task,
        {"improve": "improvement_subgraph", "test": "test_subgraph"}
    )
    graph.add_edge("improvement_subgraph", "synthesize")
    graph.add_edge("test_subgraph", "synthesize")
    graph.add_edge("synthesize", END)

    # interrupt_before="synthesize" : le graphe s'arrête AVANT ce nœud
    interrupted_graph = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["synthesize"],
    )

    initial_state = {
        "file_path": "sample.py",
        "task": "improve",
        "max_retries": 3,
        "source_code": "",
        "generated_code": "",
        "execution_success": False,
        "retry_count": 0,
        "final_report": "",
        "analysis": "",
    }

    config = {"configurable": {"thread_id": THREAD_ID}}

    # Exécution — va s'arrêter avant synthesize
    for chunk in interrupted_graph.stream(initial_state, config, stream_mode="updates"):
        for node_name, _ in chunk.items():
            print(f"  nœud exécuté : {node_name}")

    # Inspecte l'état au moment de l'interruption
    state_at_interrupt = interrupted_graph.get_state(config)
    print(f"\nInterrompu. Prochain nœud prévu : {state_at_interrupt.next}")
    print(f"generated_code présent : {bool(state_at_interrupt.values.get('generated_code'))}")
    print(f"execution_success : {state_at_interrupt.values.get('execution_success')}")


# ── Étape 2 : reprendre depuis le checkpoint ──────────────────────────────────

print("\n=== Étape 2 : reprise du workflow ===\n")

with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    # On recompile SANS interrupt_before pour laisser synthesize s'exécuter
    from graph import build_graph
    resumed_graph = build_graph(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": THREAD_ID}}

    # None comme input = reprendre depuis le dernier checkpoint
    for chunk in resumed_graph.stream(None, config, stream_mode="updates"):
        for node_name, node_output in chunk.items():
            print(f"  nœud repris : {node_name}")
            if "final_report" in node_output:
                print(f"\n{node_output['final_report']}")
