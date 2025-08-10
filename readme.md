# 🏢 Sistema de Consulta CNPJ - Versão Simplificada

Sistema standalone para consulta de dados CNPJ com interface web e API REST.

## ✨ Características

- ✅ **Funciona sem Claude Desktop** - Sistema independente
- ✅ **Interface web moderna** - Bootstrap + JavaScript
- ✅ **API REST** - Endpoints para integração
- ✅ **Banco SQLite local** - Dados armazenados localmente
- ✅ **Setup simples** - 2 comandos apenas
- ✅ **Sem dependências complexas** - Apenas Flask e requests

## 🚀 Instalação Rápida

```bash
# 1. Clonar repositório
git clone https://github.com/tiagoegidio-cmd/cnpj-mcp-sqlite-rag-server.git
cd cnpj-mcp-sqlite-rag-server

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar
python main.py --web
```

Acesse: http://localhost:5000

## 💻 Uso da Linha de Comando

```bash
# Consultar CNPJ específico
python main.py --cnpj 43227497000198

# Buscar por nome
python main.py --nome "N9 PARTICIPACOES"

# Listar empresas cadastradas
python main.py --listar

# Ver estatísticas
python main.py --stats

# Interface web
python main.py --web
```

## 🌐 Interface Web

O sistema inclui uma interface web completa com:

- 🔍 **Consulta CNPJ** - Digite o CNPJ e veja todos os dados
- 📋 **Listagem** - Veja todas as empresas cadastradas
- 📊 **Estatísticas** - Análise dos dados
- 🎨 **Design responsivo** - Funciona em mobile e desktop

### Screenshots

Interface principal com busca:
- Campo para digite do CNPJ
- Validação automática
- Exemplos clicáveis
- Resultados detalhados

## 🔌 API REST

### Endpoints Disponíveis

```
GET /api/consultar/<cnpj>     # Consultar CNPJ específico
GET /api/listar               # Listar empresas (até 20)
GET /api/stats                # Estatísticas do banco
GET /api/buscar/<termo>       # Buscar por nome
```

### Exemplos de Uso

```bash
# Consultar CNPJ
curl http://localhost:5000/api/consultar/43227497000198

# Listar empresas
curl http://localhost:5000/api/listar

# Estatísticas
curl http://localhost:5000/api/stats
```

### Resposta da API

```json
{
  "cnpj": "43227497000198",
  "razao_social": "N9 PARTICIPACOES SOCIEDADE SIMPLES",
  "nome_fantasia": "",
  "situacao_cadastral": "ATIVA",
  "municipio": "SAO PAULO",
  "uf": "SP",
  "cnae_principal": "7020400",
  "cnae_descricao": "ATIVIDADES DE CONSULTORIA EM GESTAO EMPRESARIAL",
  "capital_social": 1000000.0
}
```

## 📂 Estrutura do Projeto

```
├── main.py              # Script principal e lógica de negócio
├── web_interface.py     # Interface web Flask
├── requirements.txt     # Dependências mínimas
├── README.md           # Documentação
├── data/               # Dados locais (criado automaticamente)
│   └── cnpj.db         # Banco SQLite
└── tests/              # Testes (futuro)
    └── test_api.py
```

## 🗄️ Banco de Dados

O sistema cria automaticamente um banco SQLite local com:

- **Tabela empresas** - Dados principais das empresas
- **Dados de exemplo** - CNPJs de teste pré-carregados
- **Índices** - Para consultas rápidas

### CNPJs de Exemplo

- `43227497000198` - N9 PARTICIPACOES SOCIEDADE SIMPLES
- `11222333000144` - EMPRESA EXEMPLO TECNOLOGIA LTDA

## ⚙️ Configuração

### Variáveis de Ambiente (Opcional)

```bash
export CNPJ_DB_PATH="data/cnpj.db"          # Caminho do banco
export FLASK_PORT="5000"                    # Porta da web interface
export FLASK_DEBUG="True"                   # Debug mode
```

### Personalização

Para adicionar mais dados ao banco:

```python
from main import CNPJDatabase

db = CNPJDatabase()
# Conectar ao banco e inserir dados
```

## 🧪 Testes

```bash
# Executar testes básicos
python -m pytest tests/

# Testar API
python main.py --cnpj 43227497000198
python main.py --stats
```

## 🔧 Desenvolvimento

### Adicionar Novos CNPJs

1. Edite `main.py` na função `insert_sample_data()`
2. Adicione novos registros na tupla `sample_data`
3. Delete `data/cnpj.db` e execute novamente

### Integrar API Externa

Para conectar com API real da Receita Federal:

```python
def consultar_receita_federal(self, cnpj: str) -> Dict:
    # Implementar chamada para API real
    url = f"https://api-receita-federal.com/cnpj/{cnpj}"
    response = requests.get(url)
    return response.json()
```

## 📊 Comparação com Versão Anterior

| Aspecto | Versão Anterior | Versão Atual |
|---------|----------------|--------------|
| **Setup** | Complexo (MCP + Google + Claude) | 2 comandos |
| **Dependências** | 15+ bibliotecas pesadas | 3 bibliotecas leves |
| **Interface** | Apenas Claude Desktop | Web + CLI + API |
| **Dados** | Google Drive | SQLite local |
| **Manutenção** | Alta | Baixa |
| **Portabilidade** | Baixa | Alta |

## 🐛 Solução de Problemas

### Erro: "Module not found"
```bash
pip install -r requirements.txt
```

### Erro: "Permission denied" no banco
```bash
chmod 755 data/
chmod 644 data/cnpj.db
```

### Interface web não carrega
```bash
# Verificar porta
netstat -an | grep 5000

# Usar porta alternativa
python main.py --web --port 8080
```

## 🤝 Contribuição

1. Fork o repositório
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit: `git commit -m 'Add nova funcionalidade'`
4. Push: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

## 📄 Licença

MIT License - veja LICENSE.md para detalhes.

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/tiagoegidio-cmd/cnpj-mcp-sqlite-rag-server/issues)
- **Email**: tiago.egidio@n9par.com.br
- **Documentação**: Sempre atualizada neste README

---

**🎯 Sistema funcional, simples e sem complicações!**
