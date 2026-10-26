"""Sobe o servidor real com relógio fixo e registra cada verificação feita via HTTP."""

import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import httpx

# Console do Windows usa cp1252; a saída fica legível com acentos.
sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent  # gerado/
EVIDENCIAS = RAIZ.parent / "evidencias"


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextmanager
def servidor(agora_iso: str | None, banco: Path):
    """Sobe uvicorn numa porta livre com APP_DB e, se informado, APP_AGORA.

    Para o tempo "passar", feche o servidor e abra outro com agora_iso posterior e o mesmo banco.
    """
    porta = _porta_livre()
    env = {**os.environ, "APP_DB": str(banco), "PYTHONIOENCODING": "utf-8"}
    env.pop("APP_AGORA", None)
    if agora_iso:
        env["APP_AGORA"] = agora_iso
    processo = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(porta)],
        cwd=RAIZ,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{porta}"
    try:
        for _ in range(100):
            try:
                if httpx.get(f"{url}/api/saude", timeout=1).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.2)
        else:
            raise RuntimeError("O servidor não respondeu em /api/saude")
        with httpx.Client(base_url=url, timeout=5) as cliente:
            yield cliente
    finally:
        processo.terminate()
        try:
            processo.wait(timeout=10)
        except subprocess.TimeoutExpired:
            processo.kill()


def resumo(resposta: httpx.Response, *campos: str) -> str:
    """Texto curto para a coluna "Obtido": status HTTP e só os campos que a verificação confere."""
    partes = [f"HTTP {resposta.status_code}"]
    try:
        corpo = resposta.json()
    except ValueError:
        return partes[0]
    if isinstance(corpo, dict):
        for campo in campos:
            partes.append(f"{campo}={corpo.get(campo)}")
    elif campos:
        partes.append(f"{len(corpo)} itens")
    return ", ".join(partes)


class Verificacao:
    def __init__(self):
        self.linhas: list[tuple[str, str, str, str, bool]] = []

    def registrar(self, codigo: str, cenario: str, esperado: str, obtido: str, passou: bool) -> None:
        self.linhas.append((codigo, cenario, esperado, obtido, passou))
        print(f"{'PASSOU' if passou else 'FALHOU'} {codigo}: {obtido}")

    def salvar(self, nome: str = "criterios-aceite.md") -> bool:
        """Grava em evidencias/, com as linhas ordenadas por código (TELA por último)."""
        linhas = sorted(self.linhas, key=lambda linha: (linha[0] == "TELA", linha[0]))
        aprovados = sum(1 for linha in linhas if linha[4])
        texto = [
            "# Critérios de aceite verificados via HTTP",
            "",
            f"Executado em {datetime.now().isoformat(timespec='seconds')} contra o servidor real (uvicorn).",
            "",
            f"**Resultado: {aprovados}/{len(linhas)} aprovados.**",
            "",
            "| Código | Cenário | Esperado | Obtido | Resultado |",
            "|---|---|---|---|---|",
        ]
        for codigo, cenario, esperado, obtido, passou in linhas:
            obtido = obtido.replace("|", "\\|").replace("\n", " ")
            texto.append(f"| {codigo} | {cenario} | {esperado} | {obtido} | {'PASSOU' if passou else 'FALHOU'} |")
        EVIDENCIAS.mkdir(parents=True, exist_ok=True)
        (EVIDENCIAS / nome).write_text("\n".join(texto) + "\n", encoding="utf-8")
        return aprovados == len(linhas)
