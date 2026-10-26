# Log de evolução

## Evolução 1 · Edição de despesa pendente e quantidades no resumo

- **Pedido:** > agora preciso poder editar uma despesa enquanto ela estiver pendente (valor, descrição e categoria), respeitando os mesmos limites. Também quero que o resumo do mês mostre quantas despesas há em cada categoria, além do total.
- **Início / fim:** 08:00:56 / 08:06:03
- **Códigos novos ou alterados:** novos RF-12, RN-11, PR-13, PR-14, PR-15, CA-11, CA-12, CA-13, CA-14; alterados RF-07, RN-01, RN-02, RN-10, PR-06, "Fora de escopo" (edição)
- **Arquivos alterados:** gerado/docs/PRD.md, gerado/docs/SPEC.md, gerado/app/dominio/despesas.py, gerado/app/repositorio/despesas.py, gerado/app/rotas/despesas.py, gerado/app/estatico/index.html, gerado/tests/test_evolucao_01.py (novo), gerado/tests/test_seguranca.py, gerado/verificacao/verificar_ca.py, evidencias/criterios-aceite.md (regerado pelo script)
- **Testes da mudança antes do código:** `pytest -q tests/test_evolucao_01.py` → 11 failed, 1 warning in 2.12s
- **Suíte completa depois:** `pytest -q` → 92 passed, 1 warning in 12.69s
- **Critérios via HTTP:** 15/15 (TELA + CA-01 a CA-14)
- **Testes antigos alterados:** nenhum
