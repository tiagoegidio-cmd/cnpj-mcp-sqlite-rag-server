#!/usr/bin/env python3
"""
Apify Actor: Gerador de Tokens OAuth 2.0
Execute este Actor para gerar os tokens reais do Google Drive
"""

import os
import json
from urllib.parse import urlparse, parse_qs
from apify import Actor
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

async def main():
    async with Actor:
        Actor.log.info("🔐 Gerador de Tokens OAuth 2.0 - CNPJ Google Drive")
        
        # Obter input
        actor_input = await Actor.get_input() or {}
        
        # Configuração OAuth
        CLIENT_ID = "388098591605-eunqel7pdgid80j7v1c49vleetpasn7c.apps.googleusercontent.com"
        CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if not CLIENT_SECRET or CLIENT_SECRET == "temp_client_secret":
            await Actor.push_data({
                "status": "ERRO",
                "erro": "GOOGLE_CLIENT_SECRET não configurado corretamente",
                "instrucao": "Configure o Client Secret real nas variáveis de ambiente"
            })
            return
        
        operation = actor_input.get('operation', 'generate_auth_url')
        
        if operation == 'generate_auth_url':
            await generate_authorization_url(CLIENT_ID, CLIENT_SECRET)
        elif operation == 'process_auth_code':
            auth_code = actor_input.get('auth_code')
            if not auth_code:
                await Actor.push_data({
                    "status": "ERRO",
                    "erro": "Código de autorização não fornecido",
                    "instrucao": "Execute primeiro com operation='generate_auth_url'"
                })
                return
            await process_authorization_code(CLIENT_ID, CLIENT_SECRET, auth_code)
        elif operation == 'test_connection':
            await test_google_drive_connection()
        else:
            await Actor.push_data({
                "status": "ERRO",
                "erro": "Operação inválida",
                "operacoes_validas": ["generate_auth_url", "process_auth_code", "test_connection"]
            })

async def generate_authorization_url(client_id, client_secret):
    """Gera URL de autorização OAuth"""
    try:
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8080"]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=['https://www.googleapis.com/auth/drive.readonly'],
            redirect_uri='http://localhost:8080'
        )
        
        auth_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent',
            include_granted_scopes='true'
        )
        
        await Actor.push_data({
            "status": "SUCCESS",
            "passo": "1 - AUTORIZAÇÃO",
            "auth_url": auth_url,
            "instrucoes": {
                "1": f"Abra esta URL no navegador: {auth_url}",
                "2": "Faça login com tiagosimon@gmail.com",
                "3": "Autorize o acesso ao Google Drive",
                "4": "Você será redirecionado para http://localhost:8080/?code=XXXXXX",
                "5": "Copie APENAS o código (parte depois de 'code=')",
                "6": "Execute este Actor novamente com operation='process_auth_code' e auth_code='CODIGO_COPIADO'"
            }
        })
        
    except Exception as e:
        await Actor.push_data({
            "status": "ERRO",
            "erro": f"Falha ao gerar URL: {str(e)}"
        })

async def process_authorization_code(client_id, client_secret, auth_code):
    """Processa código de autorização e gera tokens"""
    try:
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8080"]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=['https://www.googleapis.com/auth/drive.readonly'],
            redirect_uri='http://localhost:8080'
        )
        
        # Trocar código por tokens
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials
        
        if not credentials.refresh_token:
            await Actor.push_data({
                "status": "ERRO",
                "erro": "Refresh token não recebido",
                "solucao": "Execute novamente com prompt=consent"
            })
            return
        
        # Testar tokens
        service = build('drive', 'v3', credentials=credentials)
        about = service.about().get(fields="user").execute()
        user_email = about.get('user', {}).get('emailAddress', 'Unknown')
        
        await Actor.push_data({
            "status": "SUCCESS",
            "passo": "2 - TOKENS GERADOS",
            "user_conectado": user_email,
            "tokens": {
                "GOOGLE_ACCESS_TOKEN": credentials.token,
                "GOOGLE_REFRESH_TOKEN": credentials.refresh_token,
                "GOOGLE_CLIENT_SECRET": client_secret
            },
            "proximos_passos": {
                "1": "Copie os tokens acima",
                "2": "Substitua as variáveis de ambiente no Apify:",
                "3": "GOOGLE_ACCESS_TOKEN = [valor do access_token]",
                "4": "GOOGLE_REFRESH_TOKEN = [valor do refresh_token]",
                "5": "Faça Build do Actor",
                "6": "Execute com operation='test_connection' para validar"
            }
        })
        
    except Exception as e:
        await Actor.push_data({
            "status": "ERRO",
            "erro": f"Falha ao processar código: {str(e)}"
        })

async def test_google_drive_connection():
    """Testa conexão com Google Drive usando tokens das variáveis"""
    try:
        CLIENT_ID = "388098591605-eunqel7pdgid80j7v1c49vleetpasn7c.apps.googleusercontent.com"
        CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
        ACCESS_TOKEN = os.getenv('GOOGLE_ACCESS_TOKEN')
        REFRESH_TOKEN = os.getenv('GOOGLE_REFRESH_TOKEN')
        
        if ACCESS_TOKEN == "temp_access_token" or REFRESH_TOKEN == "temp_refresh_token":
            await Actor.push_data({
                "status": "ERRO",
                "erro": "Tokens ainda são temporários",
                "instrucao": "Execute primeiro com operation='generate_auth_url'"
            })
            return
        
        # Criar credenciais
        credentials = Credentials(
            token=ACCESS_TOKEN,
            refresh_token=REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        
        # Testar conexão
        service = build('drive', 'v3', credentials=credentials)
        about = service.about().get(fields="user").execute()
        user_email = about.get('user', {}).get('emailAddress', 'Unknown')
        
        # Buscar arquivo cnpj.db
        Actor.log.info("🔍 Buscando arquivo cnpj.db...")
        
        # Buscar em múltiplas localizações
        queries = [
            "name='cnpj.db' and sharedWithMe=true",
            "name='BASE DE DADOS' and sharedWithMe=true and mimeType='application/vnd.google-apps.folder'",
            "name='BASE B2B' and sharedWithMe=true and mimeType='application/vnd.google-apps.folder'"
        ]
        
        files_found = []
        
        for query in queries:
            results = service.files().list(
                q=query,
                fields="files(id,name,size,mimeType,parents)"
            ).execute()
            files = results.get('files', [])
            files_found.extend(files)
        
        await Actor.push_data({
            "status": "SUCCESS",
            "passo": "3 - TESTE DE CONEXÃO",
            "user_conectado": user_email,
            "arquivos_encontrados": len(files_found),
            "arquivos": [
                {
                    "nome": f['name'],
                    "id": f['id'],
                    "tipo": f['mimeType'],
                    "tamanho": f.get('size', 'N/A')
                }
                for f in files_found
            ],
            "resultado": "✅ Conexão estabelecida com sucesso!" if files_found else "⚠️ Conexão OK, mas cnpj.db não encontrado",
            "proximos_passos": {
                "1": "Se cnpj.db foi encontrado, o sistema está pronto!",
                "2": "Execute o Actor principal com operation='query_cnpj'",
                "3": "Se não encontrou, verifique compartilhamento do arquivo"
            }
        })
        
    except Exception as e:
        await Actor.push_data({
            "status": "ERRO",
            "erro": f"Falha no teste: {str(e)}"
        })

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())