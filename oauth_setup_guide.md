# 🔐 Guia de Configuração OAuth 2.0 - CNPJ Google Drive Connector

## 📋 Visão Geral

Este guia explica como configurar a autenticação OAuth 2.0 para o Apify Actor acessar o arquivo `cnpj.db` compartilhado no Google Drive.

## 🎯 Informações do Projeto

- **Cliente OAuth 2.0:** CNPJ MCP SQLite RAG Server
- **Client ID:** 388098591605-eunqel7pdgid80j7v1c49vleetpasn7c.apps.googleusercontent.com
- **Projeto Google Cloud:** BD-CNPJ
- **Arquivo Alvo:** `cnpj.db` em `Compartilhados comigo/BASE DE DADOS/BASE B2B/`
- **Conta Proprietária:** tiagosimon@gmail.com

## 🚀 Passos de Configuração

### 1. Obter Client Secret

No Google Cloud Console:

1. Acesse: https://console.cloud.google.com/
2. Selecione projeto: **BD-CNPJ**
3. Vá em: **APIs e Serviços > Credenciais**
4. Encontre: **CNPJ MCP SQLite RAG Server**
5. Clique em ✏️ **Editar**
6. Copie o **Client Secret**

### 2. Gerar Tokens OAuth 2.0

Execute este script Python para obter os tokens:

```python
#!/usr/bin/env python3
"""
Script para gerar tokens OAuth 2.0 para Google Drive
Execute uma vez para obter access_token e refresh_token
"""

from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import json

# Configuração OAuth 2.0
CLIENT_ID = "388098591605-eunqel7pdgid80j7v1c49vleetpasn7c.apps.googleusercontent.com"
CLIENT_SECRET = "SEU_CLIENT_SECRET_AQUI"  # Substituir pelo valor real

# Configuração do cliente
client_config = {
    "web": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8080"]
    }
}

def get_oauth_tokens():
    """Gera tokens OAuth 2.0"""
    
    # Criar fluxo OAuth
    flow = Flow.from_client_config(
        client_config,
        scopes=['https://www.googleapis.com/auth/drive.readonly'],
        redirect_uri='http://localhost:8080'
    )
    
    # Obter URL de autorização
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )
    
    print("🔗 Abra esta URL no navegador:")
    print(auth_url)
    print()
    
    # Obter código de autorização
    auth_code = input("📥 Cole o código de autorização aqui: ").strip()
    
    # Trocar código por tokens
    flow.fetch_token(code=auth_code)
    
    # Extrair tokens
    credentials = flow.credentials
    
    tokens = {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    
    print("\n✅ Tokens gerados com sucesso!")
    print("\n🔑 CONFIGURAÇÃO PARA APIFY:")
    print("=" * 50)
    print(f"GOOGLE_ACCESS_TOKEN={tokens['access_token']}")
    print(f"GOOGLE_REFRESH_TOKEN={tokens['refresh_token']}")
    print(f"GOOGLE_CLIENT_SECRET={tokens['client_secret']}")
    print("=" * 50)
    
    # Salvar em arquivo
    with open('oauth_tokens.json', 'w') as f:
        json.dump(tokens, f, indent=2)
    
    print(f"\n💾 Tokens salvos em: oauth_tokens.json")
    
    return tokens

if __name__ == "__main__":
    get_oauth_tokens()
```

### 3. Configurar no Apify

Nas configurações do Actor no Apify, adicione estas variáveis de ambiente:

```bash
# Variáveis obrigatórias
GOOGLE_ACCESS_TOKEN=ya29.a0AX9GBdT...  # Token obtido no passo 2
GOOGLE_REFRESH_TOKEN=1//04...          # Refresh token obtido no passo 2  
GOOGLE_CLIENT_SECRET=GOCSPX-...        # Client Secret obtido no passo 1
```

### 4. Testar Conexão

Use este input de teste no Apify:

```json
{
  "operation": "query_cnpj",
  "cnpj": "43227497000198"
}
```

## 🔧 Estrutura de Pastas Esperada

O Actor buscará o arquivo nesta estrutura:

```
📁 Compartilhados comigo/
└── 📁 BASE DE DADOS/
    └── 📁 BASE B2B/
        └── 📄 cnpj.db
```

**Ou diretamente:**

```
📁 Compartilhados comigo/
├── 📁 BASE B2B/
│   └── 📄 cnpj.db
└── 📄 cnpj.db (busca direta)
```

## 🔍 Operações Disponíveis

### 1. Consultar CNPJ

```json
{
  "operation": "query_cnpj",
  "cnpj": "43227497000198"
}
```

**Resposta:**
```json
{
  "success": true,
  "cnpj": "43227497000198",
  "cnpj_formatted": "43.227.497/0001-98",
  "dados_cadastrais": {
    "razao_social": "N9 PARTICIPACOES SOCIEDADE SIMPLES",
    "situacao_cadastral": "ATIVA",
    "capital_social": 1000000.00
  },
  "endereco": {
    "endereco_completo": "RUA TABAPUA, 1123 - ITAIM BIBI - SAO PAULO/SP - CEP: 04533-004"
  }
}
```

### 2. Buscar por Nome

```json
{
  "operation": "search_by_name", 
  "nome": "N9 PARTICIPACOES",
  "limit": 5
}
```

**Resposta:**
```json
{
  "success": true,
  "total_found": 1,
  "empresas": [
    {
      "cnpj": "43227497000198",
      "cnpj_formatted": "43.227.497/0001-98", 
      "razao_social": "N9 PARTICIPACOES SOCIEDADE SIMPLES",
      "situacao_cadastral": "ATIVA"
    }
  ]
}
```

## 🛠️ Troubleshooting

### Erro 403 - Forbidden

**Problema:** Token expirado ou sem permissão
**Solução:** 
1. Regenerar tokens usando o script do passo 2
2. Verificar se a conta tem acesso ao arquivo compartilhado

### Erro 404 - Not Found

**Problema:** Arquivo ou pasta não encontrada
**Solução:**
1. Verificar se `cnpj.db` está em "Compartilhados comigo"
2. Confirmar estrutura de pastas: `BASE DE DADOS/BASE B2B/cnpj.db`
3. Verificar permissões de acesso

### Token Refresh Failed

**Problema:** Refresh token inválido
**Solução:**
1. Refazer autorização OAuth completa
2. Usar `prompt='consent'` para forçar novo refresh token

### Arquivo Muito Grande

**Problema:** Timeout no download
**Solução:**
1. Implementar download por chunks (já implementado)
2. Aumentar timeout do Apify Actor

## 🔐 Segurança

### Boas Práticas

- ✅ **Tokens são secretos** - nunca compartilhar em logs
- ✅ **Scope mínimo** - apenas `drive.readonly`
- ✅ **Rotação regular** - renovar tokens periodicamente  
- ✅ **Ambiente isolado** - usar apenas no Apify

### Monitoramento

- 📊 **Google Cloud Console** - monitorar uso da API
- 🔍 **Apify Logs** - verificar tentativas de acesso
- ⚠️ **Alertas** - configurar notificações de erro

## 📞 Suporte

### Logs Importantes

O Actor registra estas informações:

```
🔐 Inicializando conexão OAuth 2.0...
🔑 Usando tokens existentes...
✅ Conectado como: sua-conta@gmail.com
🔍 Procurando arquivo cnpj.db em 'Compartilhados comigo'...
✅ Arquivo cnpj.db encontrado: file_id
📥 Baixando cnpj.db...
✅ Base SQLite válida: 123456 empresas
```

### Em Caso de Problemas

1. **Verificar logs** do Actor para erro específico
2. **Testar tokens** localmente com o script Python
3. **Confirmar permissões** no Google Drive
4. **Regenerar credenciais** se necessário

---

## ⚡ Exemplo Completo

```bash
# 1. Configurar variáveis no Apify
GOOGLE_ACCESS_TOKEN=ya29.a0AX9GBdT_exemplo...
GOOGLE_REFRESH_TOKEN=1//04_exemplo...
GOOGLE_CLIENT_SECRET=GOCSPX-exemplo...

# 2. Input de teste
{
  "operation": "query_cnpj",
  "cnpj": "43227497000198"
}

# 3. Resposta esperada
{
  "success": true,
  "cnpj_formatted": "43.227.497/0001-98",
  "dados_cadastrais": {
    "razao_social": "N9 PARTICIPACOES SOCIEDADE SIMPLES"
  }
}
```

🎉 **Sistema pronto para uso!**