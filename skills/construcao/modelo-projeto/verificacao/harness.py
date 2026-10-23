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

RAIZ = Path(__file__).resolve().parent.parent  # gerado/


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# Porta livre escolhida pelo sistema, para execuções em paralelo não colidirem.
PORTA = int(os.environ.get("VERIFICACAO_PORTA") or _porta_livre())


@contextmanager
def servidor(agora_iso: str, banco: Path):
    """Sobe uvicorn com APP_AGORA e APP_DB. Reinicie com outro agora_iso e o mesmo banco para o tempo 'passar'."""
    env = {**os.environ, "APP_AGORA": agora_iso, "APP_DB": str(banco)}
    processo = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(PORTA)],
        cwd=RAIZ,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{PORTA}"
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
        processo.wait(timeout=10)


class Verificacao:
    def __init__(self):
        self.linhas: list[tuple[str, str, str, str, bool]] = []

    def registrar(self, codigo: str, cenario: str, esperado: str, obtido: str, passou: bool) -> None:
        self.linhas.append((codigo, cenario, esperado, obtido, passou))
        print(f"{'PASSOU' if passou else 'FALHOU'} {codigo}: {obtido}")

    def salvar(self, caminho: Path) -> bool:
        aprovados = sum(1 for linha in self.linhas if linha[4])
        texto = [
            "# Critérios de aceite verificados via HTTP",
            "",
            f"Executado em {datetime.now().isoformat(timespec='seconds')} contra o servidor real (uvicorn, porta {PORTA}).",
            "",
            f"**Resultado: {aprovados}/{len(self.linhas)} aprovados.**",
            "",
            "| Código | Cenário | Esperado | Obtido | Resultado |",
            "|---|---|---|---|---|",
        ]
        for codigo, cenario, esperado, obtido, passou in self.linhas:
            obtido = obtido.replace("|", "\\|").replace("\n", " ")
            texto.append(f"| {codigo} | {cenario} | {esperado} | {obtido} | {'PASSOU' if passou else 'FALHOU'} |")
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text("\n".join(texto) + "\n", encoding="utf-8")
        return aprovados == len(self.linhas)
