# Revisão de qualidade

## Checklist

| Item | Verificação | Resultado |
|---|---|---|
| RF/RN e enums | PRD, SPEC, rotas e domínio comparados | Implementados; valores fixos e status corretos |
| Carga inicial | `test_modelo.py`, `GET /api/salas` | Seis salas, duas por local |
| Critérios de aceite | `tests/test_reservas.py` | Dez testes com status e campo relevante |
| Bordas | Testes RN-02 a RN-07 | Duração, início, participantes, cancelamento, ocupação e capacidade |
| Relógio | `tests/conftest.py`, `app/relogio.py` | Injetado; regras recebem `agora` |
| Erros e extremos | `tests/test_seguranca.py` | Id gigante, anos fora da faixa, texto vazio/longo, número negativo, dígitos Unicode e recurso inexistente retornam 4xx |
| Estrutura | Inspeção de `app/dominio`, `app/repositorio`, `app/rotas` | Domínio sem FastAPI/SQLite; SQL no repositório; escritas dependentes de leitura em transação |
| Tela | `node --check .tmp/tela.js`; inspeção de IDs; testes HTTP | Script válido; campos e seletores presentes; erros da API exibidos |

## Achados

| Gravidade | Descrição | Arquivo | Status |
|---|---|---|---|
| Alto | Teste de ocupação usava a primeira sala da lista, que é ordenada por local. Alterado para localizar `sala_id=1`. | `tests/test_reservas.py` | CORRIGIDO |
| Médio | Roteiro HTTP não registrava o valor obtido de ocupação e a lista do filtro. Resumo enriquecido. | `verificacao/verificar_ca.py` | CORRIGIDO |
| Baixo | Aviso de depreciação do TestClient na versão fixada do modelo. | dependências | ACEITO: testes passam; versão do pacote da skill mantida |

Testes antes das correções: `2 failed, 26 passed` (teste de relatório). Depois: `32 passed, 1 warning`.
