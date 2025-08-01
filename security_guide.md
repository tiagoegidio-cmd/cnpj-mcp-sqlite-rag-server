# 🔒 Guia de Segurança - CNPJ MCP SQLite RAG Server

## 🚨 ARQUIVOS SENSÍVEIS - NUNCA COMMITAR

### ❌ Arquivos que NUNCA devem ir para o GitHub:

| Arquivo | Motivo | Risco |
|---------|--------|-------|
| `credentials.json` | **Credenciais OAuth Google** | 🔴 **CRÍTICO** - Acesso total ao Google Drive |
| `token.json` | Token de acesso gerado | 🟡 Acesso temporário aos dados |
| `*.sqlite`, `*.db` | Bancos de dados com dados reais | 🟡 Exposição de dados empresariais |
| `chroma/` | Cache do vector database | 🟡 Dados processados em cache |

### ✅ Proteções Implementadas:

- **`.gitignore`** configurado para ignorar todos os arquivos sensíveis
- **Verificações no setup.py** alertam sobre arquivos em falta
- **Documentação clara** sobre segurança

## 🛡️ Boas Práticas de Segurança

### 1. Configuração das Credenciais Google

```bash
# ✅ Correto: arquivo local, não versionado
./credentials.json

# ❌ Errado: no repositório público
git add credentials.json  # NUNCA FAÇA ISSO!
```

### 2. Variáveis de Ambiente (Alternativa)

Para ambientes de produção, considere usar variáveis de ambiente:

```bash
export GOOGLE_CREDENTIALS_PATH="/caminho/seguro/credentials.json"
export GOOGLE_APPLICATION_CREDENTIALS="/caminho/seguro/credentials.json"
```

### 3. Verificação antes de Commit

Sempre execute antes de fazer commit:

```bash
# Verifica se não há arquivos sensíveis
git status

# Verifica o que será commitado
git diff --cached

# Lista arquivos ignorados (não devem aparecer no status)
git ls-files --others --ignored --exclude-standard
```

## 🚨 O que fazer se commitou por engano

### Se commitou `credentials.json`:

```bash
# 1. Remove do repositório (mas mantém local)
git rm --cached credentials.json
git commit -m "🔒 Remove sensitive credentials file"
git push

# 2. IMPORTANTE: Regenere as credenciais no Google Cloud Console
# 3. Adicione as novas credenciais localmente
```

### Se o repositório for público e commitou dados sensíveis:

1. **URGENTE**: Acesse Google Cloud Console
2. **Revogue** as credenciais comprometidas
3. **Crie novas** credenciais OAuth
4. **Limpe o histórico** do Git (ou torne o repo privado temporariamente)

```bash
# Opção drástica: reescrever histórico
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch credentials.json' \
  --prune-empty --tag-name-filter cat -- --all

git push origin --force --all
```

## 🔐 Configuração de Produção

### Para uso em servidor:

1. **Use Service Account** em vez de OAuth para servidores
2. **Stored Secrets** em plataformas cloud (AWS Secrets Manager, etc.)
3. **Rotate credentials** periodicamente
4. **Monitor access logs** no Google Cloud Console

### Para desenvolvimento em equipe:

1. **Cada desenvolvedor** tem suas próprias credenciais
2. **Compartilhe apenas** o `credentials.json.example`:

```json
{
  "installed": {
    "client_id": "SEU_CLIENT_ID_AQUI",
    "project_id": "SEU_PROJETO_AQUI",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "SEU_CLIENT_SECRET_AQUI",
    "redirect_uris": ["http://localhost"]
  }
}
```

## 📞 Contato para Questões de Segurança

- **Issues de segurança**: [Reporte de forma responsável](https://github.com/tiagoegidio-cmd/cnpj-mcp-sqlite-rag-server/security)
- **Email**: tiago.egidio@n9par.com.br
- **Não poste** credenciais ou tokens em issues públicas

## ✅ Checklist de Segurança

Antes de cada commit:

- [ ] `credentials.json` não está sendo versionado
- [ ] `token.json` não está sendo versionado  
- [ ] Nenhum arquivo `.sqlite` ou `.db` está sendo versionado
- [ ] Nenhuma senha ou token aparece no código
- [ ] `.gitignore` está atualizado
- [ ] Testei em ambiente local isolado

---

**🛡️ Segurança é responsabilidade de todos. Quando em dúvida, não commite!**
