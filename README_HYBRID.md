# 🌐 CNPJ MCP SQLite RAG Server - Arquitetura Híbrida

**Código 100% do GitHub + Credenciais 100% Locais**

## 🚀 Características Principais

- ✅ **Sempre Atualizado**: Código baixado do GitHub a cada execução
- ✅ **Ultra Seguro**: Apenas `credentials.json` fica local
- ✅ **Zero Manutenção**: Sem necessidade de git pull ou atualizações manuais
- ✅ **Instalação Mínima**: Apenas 2 arquivos locais necessários
- ✅ **Estrutura Específica**: `BASE DE DADOS/BASE B2B/cnpj.db`

## 🏗️ Arquitetura

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│     GitHub          │    │   Máquina Local     │    │   Google Drive      │
│   (Código Público)  │────┤   (Mínimo Local)    ├────│   (Dados Privados)  │
│                     │    │                     │    │                     │
│ • Launcher          │    │ • run_from_github.py│    │ BASE DE DADOS/      │
│ • MCP Server        │    │ • credentials.json  │    │ └── BASE B2B/       │
│ • Dependências      │    │ • (cache temp)      │    │     └── cnpj.db     │
│ • Documentação      │    │                     │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

## ⚡ Instalação Ultra-Rápida

### 1. Baixe e execute o instalador:

```bash
# Crie uma pasta para o projeto
mkdir cnpj-mcp-server
cd cnpj-mcp-server

# Baixe o instalador
curl -o install_launcher.py https://raw.githubusercontent.com/tiagoegidio-cmd/cnpj-mcp-sqlite-rag-server/main/install_launcher.py

# Execute o instalador
python install_launcher.py
```

### 2. Crie o credentials.json:

1. **Acesse**: [console.cloud.google.com](https://console.cloud.google.com/)
2. **Login com**: `tiagosimon@gmail.com`
3. **Configure OAuth 2.0** (Aplicativo para computador)
4. **Baixe** como `credentials.json`
5. **Coloque** na pasta do projeto

### 3. Teste o sistema:

```bash
python run_from_github.py --test
```

## 🎯 Como Funciona

### **Execução Típica:**

1. **Launcher inicia** (`run_from_github.py`)
2. **Verifica** `credentials.json` local
3. **Baixa** código mais recente do GitHub
4. **Instala** dependências automaticamente
5. **Executa** servidor MCP com código atualizado
6. **Conecta** ao Google Drive para acessar `cnpj.db`

### **Vantagens:**

- 🔄 **Auto-atualização**: Sempre usa a versão mais recente
- 🔒 **Segurança**: Credenciais nunca saem da sua máquina
- 🚀 **Performance**: Cache inteligente de dependências
- 🧹 **Limpeza**: Sem poluição do sistema local

## 📁 Estrutura de Arquivos

### **Local (sua máquina):**
```
projeto/
├── run_from_github.py      # Launcher (baixa tudo do GitHub)
├── credentials.json        # Suas credenciais Google (PRIVADO)
└── claude_desktop_config.json  # Configuração gerada
```

### **GitHub (público):**
```
repositório/
├── mcp_sqlite_rag_server.py    # Servidor MCP principal
├── requirements.txt            # Dependências
├── install_launcher.py         # Instalador
├── run_from_github.py          # Launcher
└── README.md                   # Documentação
```

### **Google Drive (privado):**
```
BASE DE DADOS/
└── BASE B2B/
    └── cnpj.db
```

## 🛠️ Comandos Disponíveis

### **Teste do sistema:**
```bash
python run_from_github.py --test
```

### **Executar servidor MCP:**
```bash
python run_from_github.py
```

### **Reinstalar (se necessário):**
```bash
python install_launcher.py
```

## 🔧 Configuração no Claude Desktop

### **Windows:**
Arquivo: `%APPDATA%\Claude\claude_desktop_config.json`

### **Mac:**
Arquivo: `~/Library/Application Support/Claude/claude_desktop_config.json`

### **Conteúdo:**
```json
{
  "mcpServers": {
    "cnpj-sqlite-rag-server": {
      "command": "python",
      "args": ["C:\\CAMINHO\\COMPLETO\\run_from_github.py"],
      "env": {
        "PYTHONPATH": "C:\\CAMINHO\\COMPLETO"
      }
    }
  }
}
```

## 🎮 Uso no Claude

### **Consultas em linguagem natural:**
```
Quantas empresas estão cadastradas no CNPJ?
Mostre empresas de São Paulo
Qual a estrutura do banco de dados?
```

### **SQL direto:**
```
Execute: SELECT COUNT(*) FROM empresas
Execute: SELECT * FROM empresas WHERE uf = 'SP' LIMIT 10
```

### **Busca semântica:**
```
Procure por empresas de tecnologia
Encontre dados sobre MEI
```

## 🔍 Troubleshooting

### **Erro: credentials.json não encontrado**
```bash
# Solução: Crie o arquivo seguindo o tutorial no Google Cloud Console
```

### **Erro: Pasta BASE B2B não encontrada**
```bash
# Solução: Verifique estrutura no Google Drive:
# BASE DE DADOS/BASE B2B/cnpj.db
```

### **Erro: Dependências não instaladas**
```bash
# O launcher instala automaticamente, mas se falhar:
pip install requests mcp google-api-python-client google-auth-oauthlib sentence-transformers chromadb
```

### **Erro: Código desatualizado**
```bash
# Não acontece! O launcher sempre baixa a versão mais recente
# Mas se quiser forçar limpeza do cache:
python run_from_github.py --test
```

## 🌟 Benefícios da Arquitetura Híbrida

### **Para o Desenvolvedor:**
- ✅ **Deploys instantâneos**: Commit → Disponível para todos
- ✅ **Rollback fácil**: Revert no GitHub = todos voltam à versão anterior
- ✅ **Zero distribuição**: Usuários sempre têm a versão latest

### **Para o Usuário:**
- ✅ **Sempre atualizado**: Bugfixes e features automaticamente
- ✅ **Segurança máxima**: Credenciais nunca expostas
- ✅ **Instalação mínima**: Apenas 2 arquivos locais

### **Para a Empresa:**
- ✅ **Auditoria completa**: Código público, dados privados
- ✅ **Compliance**: Credenciais controladas localmente
- ✅ **Escalabilidade**: Funciona para 1 ou 1000 usuários

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/tiagoegidio-cmd/cnpj-mcp-sqlite-rag-server/issues)
- **Email**: tiago.egidio@n9par.com.br
- **Documentação**: Sempre no GitHub (auto-atualizada)

---

**🌐 A era do software híbrido: Código na nuvem, dados locais, segurança máxima!**
