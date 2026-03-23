import argparse
from langgraph.checkpoint.sqlite import SqliteSaver

from graph import build_graph

def format_node_name(namespace: tuple, node_name: str) -> str:
    """
    Construit un label lisible selon la profondeur du nœud.
    Graphe principal  → "  [synthesize]"
    Subgraph          → "    ↳ [execute_code]"
    """
    depth = len(namespace)
    if depth == 0:
        return f"[{node_name}]"
    return f"    ↳ [{node_name}]"


def print_node_output(node_name: str, node_output: dict, depth: int):
    """Affiche les informations pertinentes selon le nœud."""

    # Nœuds à ignorer dans l'affichage
    if node_name == "__interrupt__":
        return

    indent = "      " if depth > 0 else "  "

    if "generated_code" in node_output and node_output["generated_code"]:
        preview = node_output["generated_code"][:100].replace("\n", " ")
        print(f"{indent}code généré    : {preview}...")

    if "execution_success" in node_output:
        status = "✓" if node_output["execution_success"] else "✗"
        print(f"{indent}exécution      : {status}")

    if "retry_count" in node_output and node_output["retry_count"]:
        print(f"{indent}tentative n°   : {node_output['retry_count']}")

    if "current_error" in node_output and node_output["current_error"]:
        error_preview = node_output["current_error"][:120].replace("\n", " ")
        print(f"{indent}erreur         : {error_preview}")

    if "analysis" in node_output and node_output["analysis"]:
        print(f"{indent}analyse ast    : ok")

    if "final_report" in node_output:
        print(f"\n{node_output['final_report']}")


def parse_args():
    from config import config
    parser = argparse.ArgumentParser(description="Agent d'automatisation de code")
    parser.add_argument("file", help="Fichier Python à traiter")
    parser.add_argument(
        "--task",
        choices=["improve", "test"],
        default="improve",
        help="Tâche : améliorer le code (improve) ou générer des tests (test)",
    )
    parser.add_argument(
        "--max-retries", type=int, default=config.max_retries,
        help=f"Nombre maximum de tentatives de correction (défaut : {config.max_retries})",
    )
    parser.add_argument(
        "--thread-id", default="default",
        help="ID de session pour le checkpointing (défaut : default)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Checkpointer SQLite — persiste dans le répertoire courant
    with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
        graph = build_graph(checkpointer=checkpointer)

        initial_state = {
            "file_path":         args.file,
            "task":              args.task,
            "max_retries":       args.max_retries,
            "source_code":       "",
            "generated_code":    "",
            "execution_success": False,
            "retry_count":       0,
            "final_report":      "",
            "analysis":          "",
        }

        config = {"configurable": {"thread_id": args.thread_id}}

        print(f"\n=== Agent démarré | tâche : {args.task} | fichier : {args.file} ===\n")

        # Streaming — affiche chaque nœud dès qu'il termine
        for chunk in graph.stream(
            initial_state,
            config,
            stream_mode="updates",
            subgraphs=True,          # ← nœuds internes visibles
        ):
            namespace, data = chunk
            depth = len(namespace)

            for node_name, node_output in data.items():
                label = format_node_name(namespace, node_name)
                print(label)
                print_node_output(node_name, node_output, depth)
                print()


if __name__ == "__main__":
    main()
