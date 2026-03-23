import ast
from dataclasses import dataclass, field


@dataclass
class CodeAnalysis:
    """Résultat de l'analyse statique d'un fichier Python."""
    functions: list[str] = field(default_factory=list)   # noms des fonctions
    classes: list[str]   = field(default_factory=list)   # noms des classes
    imports: list[str]   = field(default_factory=list)   # modules importés
    has_main: bool       = False                          # if __name__ == "__main__"
    line_count: int      = 0
    parse_error: str     = ""                             # vide si OK

    def to_prompt_context(self) -> str:
        """
        Résumé structuré pour l'inclure dans un prompt LLM.
        Plus compact qu'un dump JSON brut.
        """
        if self.parse_error:
            return f"Erreur d'analyse : {self.parse_error}"
        lines = [
            f"Lignes : {self.line_count}",
            f"Fonctions : {', '.join(self.functions) or 'aucune'}",
            f"Classes : {', '.join(self.classes) or 'aucune'}",
            f"Imports : {', '.join(self.imports) or 'aucun'}",
            f"Point d'entrée __main__ : {'oui' if self.has_main else 'non'}",
        ]
        return "\n".join(lines)


def analyze_code(source: str) -> CodeAnalysis:
    """
    Analyse statique d'un code source Python via ast.

    Args:
        source: Code source Python (string).

    Returns:
        CodeAnalysis avec les métadonnées extraites.
    """
    analysis = CodeAnalysis(line_count=len(source.splitlines()))

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        analysis.parse_error = str(e)
        return analysis

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            analysis.functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            analysis.classes.append(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                analysis.imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            analysis.imports.append(node.module or "")
        elif isinstance(node, ast.If):
            # Détecte : if __name__ == "__main__"
            if (isinstance(node.test, ast.Compare)
                    and isinstance(node.test.left, ast.Name)
                    and node.test.left.id == "__name__"):
                analysis.has_main = True

    return analysis
