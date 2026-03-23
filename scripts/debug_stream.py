import sys
sys.path.insert(0, ".")

from langgraph.checkpoint.sqlite import SqliteSaver
from graph import build_graph

with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    graph = build_graph(checkpointer=checkpointer)

    initial_state = {
        "file_path": "sample.py",
        "task": "improve",
        "max_retries": 1,        # 1 seul retry pour que ce soit rapide
        "source_code": "",
        "generated_code": "",
        "execution_success": False,
        "retry_count": 0,
        "final_report": "",
        "analysis": "",
    }

    config = {"configurable": {"thread_id": "debug-stream"}}

    print("=" * 60)
    print("MODE : updates")
    print("=" * 60)
    for i, chunk in enumerate(graph.stream(
        initial_state, config, stream_mode="updates"
    )):
        print(f"\n── chunk {i} ──")
        for node_name, node_output in chunk.items():
            print(f"  nœud    : {node_name}")
            print(f"  clés    : {list(node_output.keys())}")
            # Affiche chaque valeur tronquée
            for k, v in node_output.items():
                val_str = str(v)[:80].replace("\n", " ")
                print(f"  {k:25s} : {val_str}")
                