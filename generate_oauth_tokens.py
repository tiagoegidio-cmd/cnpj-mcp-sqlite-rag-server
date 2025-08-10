#!/usr/bin/env python3
"""
Script para gerar tokens OAuth 2.0 para Google Drive
Execute uma vez para obter access_token e refresh_token para o Apify Actor
"""

from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import json
import webbrowser
from urllib.parse import urlparse, parse_qs

# Configuração OAuth 2.0 para BD-CNPJ
CLIENT_ID = "388098591605-eunqel7pdgid80j7v1c49vleetpasn7c.apps.googleusercontent.com"
CLIENT_SECRET = ""  # COLE SEU CLIENT SECRET AQUI

def get_oauth_tokens():
    """Gera tokens OAuth 2.0 para acesso ao Google Drive"""
    
    if not CLIENT_SECRET:
        print("❌ ERRO: CLIENT_SECRET não configurado!")
        print()
        print("📝 Como obter o Client Secret:")
        print("1. Acesse: https://console.cloud.google.com/")
        print("2. Selecione projeto: BD-CNPJ")
        print("3. Vá em: APIs e Serviços > Credenciais")
        print("4. Encontre: CNPJ MCP SQLite RAG Server")
        print("5. Clique em ✏️ Editar")
        print("6. Copie o Client Secret")
        print("7. Cole na variável CLIENT_SECRET neste script")
        return None
    
    # Configuração do cliente OAuth
    client_config = {
        "web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost:8080"]
        }
    }
    
    print("🚀 Iniciando processo de autorização OAuth 2.0...")
    print(f"📧 Cliente: {CLIENT_ID}")
    print()
    
    try:
        # Criar fluxo OAuth
        flow = Flow.from_client_config(
            client_config,
            scopes=['https://www.googleapis.com/auth/drive.readonly'],
            redirect_uri='http://localhost:8080'
        )
        
        # Obter URL de autorização
        auth_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent',
            include_granted_scopes='true'
        )
        
        print("🔗 PASSO 1: Autorização no navegador")
        print("=" * 50)
        print("Abra esta URL no navegador:")
        print(auth_url)
        print()
        
        # Tentar abrir automaticamente
        try:
            webbrowser.open(auth_url)
            print("✅ URL aberta automaticamente no navegador")
        except:
            print("⚠️ Copie e cole a URL manualmente no navegador")
        
        print()
        print("📋 PASSO 2: Autorizar acesso")
        print("=" * 50)
        print("1. Faça login com a conta tiagosimon@gmail.com")
        print("2. Autorize o acesso aos arquivos do Google Drive")
        print("3. Você será redirecionado para http://localhost:8080/?code=...")
        print("4. Copie TODA a URL de redirecionamento")
        print()
        
        # Obter URL de callback
        callback_url = input("📥 Cole a URL completa de redirecionamento aqui: ").strip()
        
        # Extrair código da URL
        parsed_url = urlparse(callback_url)
        
        if parsed_url.netloc != "localhost:8080":
            print("❌ URL inválida! Deve ser localhost:8080")
            return None
            
        query_params = parse_qs(parsed_url.query)
        
        if 'code' not in query_params:
            print("❌ Código de autorização não encontrado na URL!")
            if 'error' in query_params:
                print(f"Erro: {query_params['error'][0]}")
            return None
        
        auth_code = query_params['code'][0]
        print(f"✅ Código extraído: {auth_code[:20]}...")
        
        print()
        print("🔄 PASSO 3: Trocando código por tokens...")
        print("=" * 50)
        
        # Trocar código por tokens
        flow.fetch_token(code=auth_code)
        
        # Extrair credenciais
        credentials = flow.credentials
        
        if not credentials.refresh_token:
            print("❌ ERRO: Refresh token não recebido!")
            print("💡 Tente novamente usando 'prompt=consent'")
            return None
        
        tokens = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scopes": credentials.scopes
        }
        
        print("✅ Tokens gerados com sucesso!")
        print()
        
        # Salvar em arquivo
        with open('oauth_tokens.json', 'w') as f:
            json.dump(tokens, f, indent=2)
        
        print("💾 Tokens salvos em: oauth_tokens.json")
        print()
        
        print("🔑 CONFIGURAÇÃO PARA APIFY ACTOR:")
        print("=" * 70)
        print("Adicione estas variáveis de ambiente no Apify:")
        print()
        print(f"GOOGLE_ACCESS_TOKEN={tokens['access_token']}")
        print()
        print(f"GOOGLE_REFRESH_TOKEN={tokens['refresh_token']}")
        print()
        print(f"GOOGLE_CLIENT_SECRET={tokens['client_secret']}")
        print("=" * 70)
        print()
        
        print("📋 Input de teste para o Actor:")
        print("""
{
  "operation": "query_cnpj",
  "cnpj": "43227497000198"
}
        """)
        
        print("🎉 Configuração concluída!")
        print("📖 Consulte o OAUTH_SETUP_GUIDE.md para mais detalhes")
        
        return tokens
        
    except Exception as e:
        print(f"❌ Erro durante autorização: {e}")
        return None

def test_tokens(tokens_file="oauth_tokens.json"):
    """Testa se os tokens estão funcionando"""
    
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        # Carregar tokens
        with open(tokens_file, 'r') as f:
            tokens = json.load(f)
        
        print("🧪 Testando tokens...")
        
        # Criar credenciais
        credentials = Credentials(
            token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            token_uri=tokens['token_uri'],
            client_id=tokens['client_id'],
            client_secret=tokens['client_secret'],
            scopes=tokens['scopes']
        )
        
        # Criar serviço Google Drive
        service = build('drive', 'v3', credentials=credentials)
        
        # Testar acesso
        about = service.about().get(fields="user").execute()
        user_email = about.get('user', {}).get('emailAddress', 'Unknown')
        
        print(f"✅ Conectado como: {user_email}")
        
        # Buscar arquivo cnpj.db
        print("🔍 Buscando cnpj.db...")
        
        query = "name='cnpj.db' and sharedWithMe=true"
        results = service.files().list(q=query, fields="files(id,name,size)").execute()
        files = results.get('files', [])
        
        if files:
            file_info = files[0]
            print(f"✅ Arquivo encontrado: {file_info['name']} (ID: {file_info['id']})")
            print(f"📏 Tamanho: {file_info.get('size', 'Unknown')} bytes")
        else:
            print("❌ Arquivo cnpj.db não encontrado")
            print("💡 Verifique se o arquivo está compartilhado com sua conta")
        
        print("✅ Teste concluído!")
        
    except FileNotFoundError:
        print(f"❌ Arquivo {tokens_file} não encontrado")
        print("💡 Execute primeiro a função get_oauth_tokens()")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")

def main():
    """Função principal"""
    
    print("🔐 Gerador de Tokens OAuth 2.0 - CNPJ Google Drive")
    print("=" * 60)
    print()
    
    choice = input("Escolha uma opção:\n1. Gerar novos tokens\n2. Testar tokens existentes\n\nOpção (1 ou 2): ").strip()
    
    if choice == "1":
        tokens = get_oauth_tokens()
        
        if tokens:
            print()
            test_choice = input("Deseja testar os tokens agora? (s/n): ").strip().lower()
            if test_choice in ['s', 'sim', 'y', 'yes']:
                print()
                test_tokens()
                
    elif choice == "2":
        test_tokens()
        
    else:
        print("❌ Opção inválida")

if __name__ == "__main__":
    main()
