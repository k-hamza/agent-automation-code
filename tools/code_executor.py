# tools/code_executor.py
import subprocess
from dataclasses import dataclass
import tempfile
import os


@dataclass
class ExecutionResult:
    """Résultat structuré d'une exécution de code."""
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool

    @property
    def success(self) -> bool:
        return self.returncode == 0 and not self.timed_out

    def summary(self) -> str:
        """Résumé lisible pour le LLM lors d'une correction."""
        if self.timed_out:
            return "ERREUR : timeout — boucle infinie probable"
        if self.success:
            return f"Succès.\n{self.stdout.strip()}" if self.stdout.strip() else "Succès (pas de sortie)."
        # pytest écrit sur stdout — on prend les deux
        output = self.stderr.strip() or self.stdout.strip()
        return f"ERREUR (code {self.returncode}) :\n{output}"


def strip_markdown(code: str) -> str:
    """
    Supprime les balises markdown qu'un LLM peut insérer malgré les consignes.
    Gère : ```python ... ```, ``` ... ```, et les espaces superflus.
    """
    lines = code.strip().splitlines()

    # Supprime la première ligne si c'est une ouverture de bloc
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]

    # Supprime la dernière ligne si c'est une fermeture de bloc
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    return "\n".join(lines).strip()


def run_code(code: str, timeout: int = 10) -> ExecutionResult:
    """
    Exécute du code Python dans un subprocess isolé.

    Args:
        code: Code Python à exécuter (string).
        timeout: Secondes avant abandon. Défaut : 10s.

    Returns:
        ExecutionResult avec stdout, stderr, returncode, timed_out.
    """
    clean_code = strip_markdown(code)
    try:
        result = subprocess.run(
            ["python", "-c", clean_code],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return ExecutionResult(
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
            timed_out=False,
        )

    except subprocess.TimeoutExpired:
        return ExecutionResult(
            stdout="",
            stderr="",
            returncode=-1,
            timed_out=True,
        )


def run_pytest(test_code: str, timeout: int = 15) -> ExecutionResult:
    """
    Écrit les tests dans un fichier temporaire et les exécute avec pytest.
    Nécessite : pip install pytest
    """
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        prefix="test_",
        delete=False,
    ) as f:
        f.write(strip_markdown(test_code))
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["python", "-m", "pytest", tmp_path, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return ExecutionResult(
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
            timed_out=False,
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(
            stdout="", stderr="", returncode=-1, timed_out=True,
        )
    finally:
        os.unlink(tmp_path)   # nettoyage du fichier temporaire dans tous les cas
