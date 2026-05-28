# Contribuindo com a ZapUnlocked-API

Toda contribuição é bem-vinda, seja um bug report, sugestão de feature ou pull request.

---

## Reportar um problema

Antes de abrir uma issue, verifique se ela já existe em [issues abertas](https://github.com/kauafpssx/ZapUnlocked-API/issues).

- **Bug**: use o template [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md)
- **Feature**: use o template [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md)

Issues sem contexto suficiente podem ser fechadas.

---

## Contribuir com código

### 1. Fork e clone

```bash
git clone https://github.com/SEU_USER/ZapUnlocked-API.git
cd ZapUnlocked-API
```

### 2. Crie uma branch

```bash
git checkout -b feat/nome-da-feature
# ou
git checkout -b fix/nome-do-bug
```

### 3. Implemente

Mantenha o escopo focado. Um PR por feature ou fix.

### 4. Commit

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: adiciona endpoint de envio de localização
fix: corrige timeout na fila de mídia
docs: atualiza exemplos de webhook
refactor: extrai lógica de auth para módulo separado
chore: atualiza dependências
```

### 5. Abra o Pull Request

PR para a branch `main`, preenchendo o template completamente.

---

## Padrões

- Python: PEP 8, nomes descritivos em inglês
- Sem `print()` de debug em PRs
- Sem código comentado deixado para trás
- Imports: stdlib, terceiros, locais (nessa ordem)

---

## Segurança

Nunca abra issue pública para vulnerabilidades. Veja [SECURITY.md](SECURITY.md).
