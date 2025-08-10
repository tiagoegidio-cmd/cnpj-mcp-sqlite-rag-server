# 🤖 INSTRUÇÕES PARA CLAUDE - Sistema CNPJ Google Drive

## 📋 VISÃO GERAL

Este repositório contém um sistema de consulta CNPJ que acessa dados diretamente do Google Drive do usuário em tempo real. O Claude pode usar este sistema para responder consultas sobre empresas automaticamente.

## 🎯 COMO O CLAUDE DEVE USAR

### 1. CONSULTA SIMPLES DE CNPJ

Quando o usuário perguntar sobre um CNPJ específico:

```python
from cnpj_query_engine import consultar_cnpj_para_claude

# Exemplo de uso
resultado = consultar_cnpj_para_claude("43227497000198")
print(resultado)
```

### 2. BUSCA POR NOME DE EMPRESA

Para buscar empresas por nome:

```python
from cnpj_query_engine import CNPJQueryEngine

engine = CNPJQueryEngine()
empresas = engine.search_by_name("N9 PARTICIPACOES", limit=5)

for empresa in empresas:
    print(f"• {empresa['razao_social']} - CNPJ: {empresa['cnpj_formatted']}")
```

### 3. ESTATÍSTICAS DA BASE

Para mostrar estatísticas gerais:

```python
from cnpj_query_engine import CNPJQueryEngine

engine = CNPJQueryEngine()
stats = engine.get_statistics()

print(f"Total de empresas: {stats['total_empresas']}")
print(f"Por situação: {stats['por_situacao_cadastral']}")
```

## 🔧 CONFIGURAÇÃO AUTOMÁTICA

### Verificar Conexão com Google Drive

```python
from google_drive_connector import GoogleDriveCNPJConnector

connector = GoogleDriveCNPJConnector()
status = connector.test_connection()

if status["connected"]:
    print("✅ Conectado ao Google Drive")
    print(f"Arquivos encontrados: {status['files_found']}")
else:
    print("❌ Erro na conexão:", status["error"])
```

### Listar Fontes de Dados Disponíveis

```python
connector = GoogleDriveCNPJConnector()
sources = connector.get_available_data_sources()

print("📂 Fontes disponíveis:")
print(f"Fonte principal: {sources['primary_source']['name']}")
print(f"Última atualização: {sources['last_updated']}")
```

## 💬 TEMPLATES DE RESPOSTA PARA CLAUDE

### Template 1: Consulta CNPJ Bem-Sucedida

```
🏢 **DADOS DA EMPRESA**

**CNPJ:** [cnpj_formatado]
**Razão Social:** [razao_social]
**Nome Fantasia:** [nome_fantasia]
**Situação:** [situacao] desde [data_situacao]

📍 **Endereço:**
[endereco_completo]

💼 **Atividade Principal:**
[cnae] - [descricao_cnae]

💰 **Capital Social:** R$ [valor]
📊 **Porte:** [porte_empresa]

---
*Dados obtidos do Google Drive em tempo real*
```

### Template 2: CNPJ Não Encontrado

```
❌ **CNPJ NÃO ENCONTRADO**

O CNPJ [cnpj] não foi encontrado na base de dados.

**Possíveis motivos:**
• CNPJ pode estar incorreto
• Empresa não está na base atualizada
• Verificar se o CNPJ tem 14 dígitos

**Sugestões:**
• Verificar a formatação do CNPJ
• Tentar buscar pelo nome da empresa
• Conferir se todos os dígitos estão corretos
```

### Template 3: Erro de Conexão

```
⚠️ **ERRO DE CONEXÃO**

Não foi possível acessar a base de dados no Google Drive.

**Possíveis soluções:**
• Verificar se as credenciais estão corretas
• Confirmar se a pasta "BASE DE DADOS" existe
• Checar se os arquivos estão na estrutura correta

**Estrutura esperada:**
📁 BASE DE DADOS/
└── 📁 BASE B2B/
    └── 📄 cnpj.db (ou cnpj.csv)
```

## 🎨 RESPOSTAS PERSONALIZADAS

### Para Perguntas Específicas

**Pergunta:** "Qual a situação da empresa N9 Participações?"
**Resposta Claude:**
```python
# Buscar por nome primeiro
empresas = engine.search_by_name("N9 Participações")
if empresas:
    cnpj = empresas[0]['cnpj']
    dados = engine.query_cnpj(cnpj)
    resposta = f"A empresa {dados['dados_cadastrais']['razao_social']} está com situação {dados['dados_cadastrais']['situacao_cadastral']}"
```

**Pergunta:** "Quantas empresas ativas temos?"
**Resposta Claude:**
```python
stats = engine.get_statistics()
ativas = stats['por_situacao_cadastral'].get('ATIVA', 0)
resposta = f"Há {ativas} empresas com situação ATIVA na base de dados"
```

**Pergunta:** "Empresas em São Paulo?"
**Resposta Claude:**
```python
stats = engine.get_statistics()
sp = stats['por_uf'].get('SP', 0)
resposta = f"Existem {sp} empresas cadastradas no estado de São Paulo"
```

## 🚨 TRATAMENTO DE ERROS

### Erros Comuns e Como Resolver

```python
def consulta_segura(cnpj):
    try:
        resultado = consultar_cnpj_para_claude(cnpj)
        return resultado
    except Exception as e:
        if "conexão" in str(e).lower():
            return "❌ Erro de conexão com Google Drive. Verificar credenciais."
        elif "não encontrado" in str(e).lower():
            return f"❌ CNPJ {cnpj} não encontrado na base."
        else:
            return f"❌ Erro inesperado: {str(e)}"
```

## 📊 ANÁLISES AVANÇADAS

### Relatórios Personalizados

```python
def gerar_relatorio_empresas():
    engine = CNPJQueryEngine()
    stats = engine.get_statistics()
    
    relatorio = f"""
📊 **RELATÓRIO DA BASE CNPJ**

📈 **Números Gerais:**
• Total de empresas: {stats['total_empresas']:,}
• Última atualização: {stats['ultima_atualizacao']}

📍 **Por Estado (Top 5):**
"""
    
    for uf, count in list(stats['por_uf'].items())[:5]:
        relatorio += f"• {uf}: {count:,} empresas\n"
    
    return relatorio
```

## 🔍 BUSCA INTELIGENTE

### Sugestões de Busca

```python
def busca_inteligente(termo):
    engine = CNPJQueryEngine()
    
    # Se parece com CNPJ, tentar consulta direta
    if re.match(r'^\d{14}$', termo.replace('.', '').replace('/', '').replace('-', '')):
        return engine.query_cnpj(termo)
    
    # Caso contrário, buscar por nome
    else:
        return engine.search_by_name(termo, limit=10)
```

## ✅ CHECKLIST PARA CLAUDE

Antes de usar o sistema, sempre verificar:

- [ ] Conexão com Google Drive está funcionando
- [ ] Arquivos estão na estrutura correta
- [ ] Credenciais são válidas
- [ ] Base de dados está atualizada

```python
def verificar_sistema():
    connector = GoogleDriveCNPJConnector()
    status = connector.test_connection()
    
    if status["connected"]:
        print("✅ Sistema pronto para uso")
        return True
    else:
        print(f"❌ Sistema não está pronto: {status['message']}")
        return False
```

---

## 🎯 OBJETIVO FINAL

O Claude deve usar este sistema para:

1. **Responder consultas CNPJ instantaneamente**
2. **Buscar empresas por nome**
3. **Gerar relatórios e estatísticas**
4. **Fornecer análises dos dados**

Tudo em **tempo real**, acessando os dados diretamente do **Google Drive do usuário**.
