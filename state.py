from typing import TypedDict


class ImprovementState(TypedDict):
    """État interne du subgraph d'amélioration."""
    # Clés partagées avec AgentState (mapping automatique)
    source_code: str
    generated_code: str
    execution_success: bool
    retry_count: int
    max_retries: int

    # Clés privées au subgraph
    execution_stdout: str
    execution_stderr: str
    current_error: str        # erreur formatée pour le LLM


class AgentState(TypedDict):
    """État du graphe principal."""
    # Entrée
    source_code: str
    task: str
    file_path: str

    # Résultats partagés avec les subgraphs
    generated_code: str
    execution_success: bool
    retry_count: int
    max_retries: int

    # Sortie
    final_report: str


class TestState(TypedDict):
    """État interne du subgraph de génération de tests."""
    # Clés partagées avec AgentState
    source_code: str
    generated_code: str
    execution_success: bool
    retry_count: int
    max_retries: int

    # Clés privées au subgraph
    execution_stdout: str
    execution_stderr: str
    current_error: str
    