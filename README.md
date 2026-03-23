# Agent d'automatisation de code avec LangGraph

Agent IA local qui analyse du code Python, génère des améliorations
ou des tests unitaires, et valide en exécutant le code dans un
subprocess isolé. Boucle de correction automatique jusqu'à succès.

## Fonctionnalités

- **Amélioration de code** : le LLM propose une version améliorée,
  l'exécute, et corrige automatiquement en cas d'erreur
- **Génération de tests** : génère des tests pytest, les exécute,
  et corrige jusqu'à ce qu'ils passent
- **Streaming temps réel** : chaque étape s'affiche dans le terminal
  au fur et à mesure
- **Checkpointing** : reprend un workflow interrompu exactement
  là où il s'est arrêté

## Architecture
```
state.py          TypedDict partagés (AgentState, ImprovementState, TestState)
tools/            Outils Python purs sans LangGraph
  code_executor   subprocess isolé, timeout, capture stdout/stderr
  code_analyzer   analyse statique via ast
subgraphs/        Boucles de correction LangGraph
  improvement     génère → exécute → corrige → réexécute
  test_generator  génère tests → pytest → corrige → réexécute
graph.py          Graphe principal, routage, checkpointing SQLite
main.py           CLI, streaming subgraphs=True
```

## Prérequis

- Python 3.11+
- [Ollama](https://ollama.ai) avec le modèle qwen2.5:7b
```bash
ollama pull qwen2.5:7b
```

## Installation
```bash
pip install -r requirements.txt
```

## Utilisation
```bash
# Améliorer un fichier Python
python main.py sample.py --task improve

# Générer des tests unitaires
python main.py sample.py --task test

# Options disponibles
python main.py --help
```

## Exemple de sortie
```
=== Agent démarré | tâche : improve | fichier : sample.py ===

[load_and_analyze]
  analyse ast    : ok

    ↳ [generate_improvement]
      code généré    : def multiply(a, b):...

    ↳ [execute_code]
      exécution      : ✓

[synthesize]

=== Rapport agent ===
Tâche        : Amélioration
Résultat     : ✓ Succès
Tentatives   : 0
```

## Stack technique

- [LangGraph](https://github.com/langchain-ai/langgraph) — orchestration du graphe d'agent
- [LangChain Ollama](https://github.com/langchain-ai/langchain) — intégration LLM local
- [Ollama](https://ollama.ai) — inférence locale (qwen2.5:7b)
- subprocess — exécution isolée du code généré
- ast — analyse statique sans exécution
- pytest — validation des tests générés

