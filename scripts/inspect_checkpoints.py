import sys
sys.path.insert(0, ".")

from langgraph.checkpoint.sqlite import SqliteSaver
from graph import build_graph

with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    graph = build_graph(checkpointer=checkpointer)

    # thread_id utilisé lors des exécutions précédentes
    config = {"configurable": {"thread_id": "default"}}

    # Liste tous les checkpoints du thread
    history = list(graph.get_state_history(config))

    print(f"Nombre de checkpoints : {len(history)}\n")

    for i, snapshot in enumerate(history):
        print(f"--- Checkpoint {i} ---")
        print(f"  nœud suivant   : {snapshot.next}")
        print(f"  retry_count    : {snapshot.values.get('retry_count')}")
        print(f"  exec_success   : {snapshot.values.get('execution_success')}")
        generated = snapshot.values.get('generated_code', '')
        if generated:
            preview = generated[:60].replace('\n', ' ')
            print(f"  generated_code : {preview}...")
        print()
