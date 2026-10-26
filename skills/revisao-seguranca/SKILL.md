---
name: revisao-seguranca
description: Etapa 5 da fábrica. Revisão de segurança do sistema gerado em gerado/ (injeção de SQL, XSS na tela, validação de entrada, vazamento de erro, segredos, dependências), com testes de ataque, correção dos achados e evidencias/seguranca.md. Use depois do gate da revisão de qualidade.
---

# Revisão de segurança

Objetivo: garantir que o sistema não tem as falhas mais comuns de uma aplicação web local, com evidência verificável.

## Passo a passo

1. Percorra o checklist. Para cada item, registre como verificou (comando, arquivo, teste) e o resultado.
2. Escreva os testes de ataque em `tests/test_seguranca.py` (lista abaixo). Eles ficam na suíte.
3. Corrija todo achado alto ou médio. Rode a suíte inteira de novo.
4. Grave `evidencias/seguranca.md` com o checklist preenchido, os achados e a saída dos comandos de varredura.

## Checklist

**Injeção de SQL**
- [ ] Procure SQL montado com f-string, `%`, `.format` ou `+` em `app/`: `grep -rnE "execute\(f|execute\(.*%|execute\(.*\.format|execute\(.*\+" app/`. Cada ocorrência precisa ser só composição de constantes de módulo, sem nenhum dado de entrada; registre cada uma com a justificativa. Dado de entrada só entra por parâmetro `?`.
- [ ] Teste: enviar `'; DROP TABLE x; --` em todo campo de texto de criação e em parâmetros de consulta. Esperado: dado gravado literalmente ou 4xx; tabelas intactas (listagem continua funcionando).

**XSS na tela**
- [ ] Procure `innerHTML` em `app/estatico/`. Só é aceitável com texto fixo, nunca com dado da API.
- [ ] Teste: gravar `<script>alert(1)</script>` num campo de texto. A API devolve o texto literal (o escape é responsabilidade da tela, que usa `textContent`).

**Validação de entrada**
- [ ] Todo campo de entrada tem tipo e limite no modelo Pydantic. Textos com `max_length` (ex.: 200). Números com faixa.
- [ ] Teste: texto acima do limite e número negativo retornam 422.

**Vazamento de informação**
- [ ] Teste: requisição malformada (JSON inválido) retorna 4xx sem stack trace nem SQL no corpo.
- [ ] A aplicação não roda com `debug=True`.

**Segredos e dados**
- [ ] Procure segredos em `gerado/` e `evidencias/`: `grep -rniE "(password|senha|secret|token|api[_-]?key)\s*[:=]" gerado/ evidencias/ --exclude-dir=.venv`. Resultado esperado: nada.
- [ ] Dados iniciais e de teste são fictícios.
- [ ] `gerado/.gitignore` (vem do modelo) contém `.venv/`, `dados/` e `.tmp/`.

**Dependências**
- [ ] Todas as versões, inclusive transitivas, estão fixadas em `requirements.txt` (vem do modelo).
- [ ] Rode `PY -m pip install pip-audit` e, com `PYTHONIOENCODING=utf-8`, `PY -m pip_audit -r requirements.txt -f json -o .tmp/pip-audit.json`. Copie o resumo para a evidência. O esperado com a stack do modelo é nenhuma vulnerabilidade. Se aparecer alguma: atualize a versão afetada para a menor versão corrigida que mantenha `pip check` e a suíte passando; se não houver versão corrigida, mitigue no código e registre. Sem rede, registre "não executado: sem rede" e siga. Não coloque `pip-audit` no `requirements.txt`.

**Exposição**
- [ ] O servidor sobe em `127.0.0.1` (padrão do uvicorn). Sem CORS liberado para `*`.

## Gate da revisão de segurança

- [ ] `tests/test_seguranca.py` existe e passa.
- [ ] `evidencias/seguranca.md` existe com todos os itens do checklist preenchidos.
- [ ] Nenhum achado alto ou médio aberto.
- [ ] `PY -m pytest -q` passa; resultado registrado no log.
