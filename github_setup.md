# 🚀 Setup GitHub - CNPJ MCP SQLite RAG Server

Instruções completas para publicar o projeto no GitHub.

## 📋 Pré-requisitos

- ✅ Conta GitHub ativa
- ✅ Git instalado localmente
- ✅ Projeto funcionando localmente

## 🛠️ Passo a Passo

### 1. Preparar o Projeto Localmente

```bash
# Navegue até a pasta do projeto
cd cnpj-mcp-sqlite-rag-server

# Inicialize o repositório Git (se ainda não foi feito)
git init

# Adicione todos os arquivos
git add .

# Faça o primeiro commit
git commit -m "🎉 Initial commit: CNPJ MCP SQLite RAG Server"
```

### 2. Criar Repositório no GitHub

1. **Acesse** [github.com](https://github.com)
2. **Clique** em "New repository"
3. **Configure**:
   - **Repository name**: `cnpj-mcp-sqlite-rag-server`
   - **Description**: `MCP Server com RAG para bancos SQLite no Google Drive - CNPJ`
   - **Visibility**: Private ou Public (sua escolha)
   - ❌ **NÃO** marque "Add a README file"
   - ❌ **NÃO** adicione .gitignore
   - ❌ **NÃO** escolha uma license (já temos)

4. **Clique** "Create repository"

### 3. Conectar Repositório Local ao GitHub

```bash
# Adicione o repositório remoto
git remote add origin https://github.com/tiagoegidio-cmd/cnpj-mcp-sqlite-rag-server.git

# Verifique se foi adicionado corretamente
git remote -v

# Envie para o GitHub
git branch -M main
git push -u origin main
```

### 4. Configurar Secrets (Opcional)

Se quiser usar GitHub Actions no futuro:

1. **Vá** para Settings → Secrets and variables → Actions
2. **Adicione** secrets necessários:
   - `GOOGLE_CREDENTIALS`: conteúdo do credentials.json (se público)

### 5. Atualizar README com Link Correto

Edite o README.md e substitua `SEU_USUARIO` pelo seu username GitHub:

```markdown
git clone https://github.com/tiagoegidio-cmd/cnpj-mcp-sqlite-rag-server.git
```

Commit a mudança:

```bash
git add README.md
git commit -m "📝 Update GitHub username in README"
git push
```

## 🔐 Segurança - Arquivos Sensíveis

⚠️ **CRÍTICO - NUNCA** commite estes arquivos:

- ❌ `credentials.json` - **Credenciais Google (SENSÍVEL!)**
- ❌ `token.json` - Token de acesso OAuth
- ❌ `*.sqlite` - Bancos de dados
- ❌ `*.db` - Bancos de dados
- ❌ `chroma/` - Vector database cache

O `.gitignore` já está configurado para ignorá-los automaticamente.

### 🚨 Se você commitou credentials.json por engano:

```bash
# Remove do repositório (mas mantém local)
git rm --cached credentials.json
git commit -m "🔒 Remove sensitive credentials file"
git push

# Regenere as credenciais no Google Cloud Console!
```

## 📝 Colaboração

### Branch Strategy

```bash
# Criar nova feature
git checkout -b feature/nova-funcionalidade

# Fazer mudanças...
git add .
git commit -m "✨ Add nova funcionalidade"

# Push da branch
git push origin feature/nova-funcionalidade

# No GitHub: criar Pull Request
# Após aprovação: merge e delete branch
```

### Convenção de Commits

Use emojis para facilitar identificação:

- 🎉 `:tada:` - Initial commit
- ✨ `:sparkles:` - Nova funcionalidade
- 🐛 `:bug:` - Bug fix
- 📝 `:memo:` - Documentação
- 🔧 `:wrench:` - Configuração
- 🚀 `:rocket:` - Deploy/Performance
- 🔒 `:lock:` - Segurança
- 🧪 `:test_tube:` - Testes

Exemplos:
```bash
git commit -m "✨ Add semantic search functionality"
git commit -m "🐛 Fix authentication error"
git commit -m "📝 Update installation instructions"
```

## 🏷️ Releases

### Criar Release

1. **Vá** para GitHub → Releases
2. **Clique** "Create a new release"
3. **Tag**: `v1.0.0`
4. **Title**: `v1.0.0 - Initial Release`
5. **Descrição**:

```markdown
## 🎉 Initial Release

### Features
- ✅ MCP Server implementation
- ✅ Google Drive integration  
- ✅ RAG with sentence-transformers
- ✅ Natural language queries
- ✅ Semantic search
- ✅ SQL query support

### Installation
See README.md for complete instructions.

### Requirements
- Python 3.8+
- Google Drive API credentials
- Claude Desktop
```

### Versioning

Use [Semantic Versioning](https://semver.org/):

- **Major** (1.0.0): Breaking changes
- **Minor** (1.1.0): New features
- **Patch** (1.1.1): Bug fixes

## 🤝 Issues e Pull Requests

### Templates

Crie `.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Environment:**
- OS: [e.g. macOS, Windows, Linux]
- Python version: [e.g. 3.9]
- MCP Server version: [e.g. 1.0.0]

**Additional context**
Add any other context about the problem here.
```

## 📊 GitHub Actions (Opcional)

Crie `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    - name: Run tests
      run: |
        python -m pytest tests/ -v
```

## 🌟 README Badges

Adicione badges ao README.md:

```markdown
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![GitHub Stars](https://img.shields.io/github/stars/tiagoegidio-cmd/cnpj-mcp-sqlite-rag-server.svg)
![GitHub Issues](https://img.shields.io/github/issues/tiagoegidio-cmd/cnpj-mcp-sqlite-rag-server.svg)
```

## ✅ Checklist Final

- [ ] Repositório criado no GitHub
- [ ] Código enviado com sucesso
- [ ] README atualizado com links corretos
- [ ] .gitignore configurado
- [ ] Primeira release criada
- [ ] Issues templates (opcional)
- [ ] GitHub Actions (opcional)
- [ ] Badges no README (opcional)

---

🎉 **Parabéns!** Seu projeto está no GitHub e pronto para colaboração!
