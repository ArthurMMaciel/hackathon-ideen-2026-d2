# Revisão de segurança

| Item | Verificação | Resultado |
|---|---|---|
| Injeção SQL | Busca `execute(f`, `%`, `.format`, `+` em `app/`; `test_injecao_textos_e_consulta` | Nenhuma montagem com entrada; `?` em todas as consultas; tabelas intactas |
| XSS | Busca `innerHTML` em `app/estatico/`; `test_xss_literal` | Sem ocorrência; API devolve texto literal e tela usa `textContent` |
| Validação | Inspeção dos modelos Pydantic e `test_limites_e_json_malformado`, `test_extremos_rotas` | Texto longo, vazio, números negativos, datas e ids inválidos retornam 422 |
| Vazamento | JSON inválido no teste de segurança; inspeção de `app/main.py` | 422 sem stack trace ou SQL; `debug=True` ausente |
| Segredos e dados | Busca de `password/senha/secret/token/api_key` em `gerado/` e `evidencias/`, exceto `.venv`; inspeção da carga | Nenhuma ocorrência; dados fictícios |
| `.gitignore` | Inspeção de `gerado/.gitignore` | Exclui `.venv/`, `dados/`, `.tmp/` |
| Dependências | `pip_audit -r requirements.txt -f json -o .tmp/pip-audit.json` | `No known vulnerabilities found` |
| Exposição | `subida_manual.py`; inspeção de CORS | Servidor em `127.0.0.1`; CORS amplo ausente |

## Achados

| Gravidade | Descrição | Status |
|---|---|---|
| Baixo | Comentário da tela continha a string `innerHTML`, confundindo a busca automática. Removido. | CORRIGIDO |

Testes de ataque: `tests/test_seguranca.py`. Suíte após correções: `32 passed, 1 warning`.
