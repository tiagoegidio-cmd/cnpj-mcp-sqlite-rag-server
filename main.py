#!/usr/bin/env python3
"""
Apify Actor: CNPJ Google Drive Connector
Conecta ao Google Drive, baixa base CNPJ e executa consultas
Para uso com Claude Projetos
"""

import os
import json
import sqlite3
import tempfile
from typing import Dict, Any, Optional
from apify import Actor
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import io

class CNPJGoogleDriveConnector:
    """Conector principal para CNPJ via Google Drive"""
    
    def __init__(self):
        self.service = None
        self.temp_db_path = None
        
    async def initialize_drive_connection(self):
        """Inicializa conexão com Google Drive"""
        try:
            # Buscar credenciais do environment ou integration body
            credentials_json = os.getenv('GOOGLE_CREDENTIALS')
            
            # Se não encontrar, tentar ler do input (fallback)
            if not credentials_json:
                # Tentar ler das configurações do Actor
                try:
                    import requests
                    # Como fallback, usar credenciais hardcoded temporariamente
                    credentials_json = '''{
  "type": "service_account",
  "project_id": "bd-cnpj",
  "private_key_id": "8de40c846175bd3840658718bd3a620aa745fa70",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCVAmQqL7jECAJu\\nhUeasBLqIZMSVuUcxRNQFCRlVgB3jhAqU/xOIHGoI7wgPFs4bSRVoXI3JPJjT20A\\nKz6d9Qbk3A+N35/BL1BtUpJXDQM3W7SUaiVYqC9QRe4fcWuVInq7jHBZpzzDSibr\\nCR5u7WVZfRsrCnquDlprh9bnUtof26Y5cs6LKyzmKmSHxlIdcYQfnh0zt4mlRmo0\\nguhhDX+9hHXAGkQJQRAtT+dSplIBQN/mCvQfxDa/sN7LFL7JJ5XTZq89tQqWD5Ay\\nGFgh5qJH3ECzcf+Ybt03/NjgH2nkYskp1+gPrP2fXQWHQWGFyREC7ttYMELsrEmu\\ndyvikdHpAgMBAAECggEALkTl0WusFcLe7m6YQ2I1HVp7jpBI6FwRmSYH/ydrUbRd\\nNKeLir7sS+d8vQ3AzY6mX6iYDKN+WHQLRqgm82loUJw8gDNWKeiFMs0W/8zcmM3z\\nDrq/Cf5/Yo+0VzMi0tY4AhCjulMBvSpDV2wndQ5mEBmW3BCO84klboppor7JWGak\\ntPksqmFEGiJP9o20EzFoBIlzdvFjPiOdvnlwx7guU6JWRaRLHYWwubrBsN7lKNDO\\n3K1p1YiVYb5IDhQolDsRRSNrUohfUAyLbrVJmO5mN/PmCIkqSLMCpBZHBjtDPaVA\\nYLxNNB8dCC5/MqM5SOaewKk/dEgM0RUP7q/TvEOLeQKBgQDEc3yjpZUdA6XeEHO3\\nGfdfgHYCbgMFO0rK/i5pbaeEeHQYQhqKsXMeRjtkJgAOLUGSiXc4X04iHUhzNWMY\\nR4ZbEHnHFz8eVRiucb63b31MEzry2SIW2kXeabvlsG93TUJIXBddz7dxYP6NYK9B\\ntGwVsTbD+so12AInOG9EsEgLQwKBgQDCLXHoVHDR0smjQ1jP41Rc9Hra1iYcaOPl\\n1ZnrwHz6FvAWI7gCYkky/4RHczCeJ7Q6zNyDlVuAHNBoaPuC0zO3MuCfg8glj/FH\\nGqOky5I7YYN3AjNK0SoixS9GGzQksnG351S7QXCKA2aNrFCCPbO8muifdaipAZ7G\\nWsLCSTe9YwKBgQC8oKMJwsDVlh4ahjOFmWIkCgXFuXoe+NqM5NkNlCNoF/xpGne/\\nujjt1cPLGo2tDxlKKcIWl7Q/H1zkeluHAY5pO/2iA5kwd8b2IPNd0Kg/dquAaKrJ\\nxJWXxHCNUAcHR2CgeARbqEncjKR+fVpqPWIWxgzuyoyEfL88h3yXOKhEXwKBgQC8\\nP7Keur5lrSUu0qvXX1z6gUpZviNUh5vpxhtjI0oGaxZ3YEmUhhTRDEcBvfr0WSmx\\nl8pxBuueWFDz6FNtkbQhd4GtI+V2BQa1GG5t5a3vQ6pgRhHUBtQCwYgDP3xd12HI\\nGM1cfSTNqF5UGyoyGf+Wadf8P+UzdA6p3nPSR4lyYQKBgDM6iF7gP4J8gwIwsx5d\\nqMN/H4RzcmIheFMCC0SQ+hpCPxpNPKjnOa4quuLNpjStnAnSu7TJfk/dxSqXRMFn\\nWTBk/FbGTb/b6lubasttjtbwG5BNCXe2F+Gdo0SNT7YlBtoISJas4F9PXIKvv7BP\\njhdpxHgg5wwFwgSFJSyT7YX8\\n-----END PRIVATE KEY-----\\n",
  "client_email": "cnpj-drive-access@bd-cnpj.iam.gserviceaccount.com",
  "client_id": "102786034357488294792",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/cnpj-drive-access%40bd-cnpj.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}'''
                except:
                    pass
            
            if not credentials_json:
                raise ValueError("GOOGLE_CREDENTIALS não encontrado no environment")
            
            Actor.log.info("🔐 Carregando credenciais Google...")
            
            # Carregar credenciais
            credentials_info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            
            # Criar serviço Google Drive
            self.service = build('drive', 'v3', credentials=credentials)
            
            Actor.log.info("✅ Conexão com Google Drive estabelecida")
            return True
            
        except Exception as e:
            Actor.log.error(f"❌ Erro ao conectar Google Drive: {e}")
            return False
    
    async def find_cnpj_database(self):
        """Encontra e baixa o arquivo cnpj.db do Google Drive"""
        try:
            Actor.log.info("🔍 Procurando pasta BASE DE DADOS...")
            
            # Buscar pasta "BASE DE DADOS"
            query = "name='BASE DE DADOS' and mimeType='application/vnd.google-apps.folder'"
            results = self.service.files().list(q=query).execute()
            folders = results.get('files', [])
            
            if not folders:
                raise FileNotFoundError("Pasta 'BASE DE DADOS' não encontrada")
            
            base_folder_id = folders[0]['id']
            Actor.log.info(f"✅ Pasta BASE DE DADOS encontrada: {base_folder_id}")
            
            # Buscar pasta "BASE B2B" dentro de "BASE DE DADOS"
            query = f"name='BASE B2B' and parents in '{base_folder_id}' and mimeType='application/vnd.google-apps.folder'"
            results = self.service.files().list(q=query).execute()
            folders = results.get('files', [])
            
            if not folders:
                raise FileNotFoundError("Pasta 'BASE B2B' não encontrada dentro de 'BASE DE DADOS'")
            
            b2b_folder_id = folders[0]['id']
            Actor.log.info(f"✅ Pasta BASE B2B encontrada: {b2b_folder_id}")
            
            # Buscar arquivo cnpj.db
            query = f"name='cnpj.db' and parents in '{b2b_folder_id}'"
            results = self.service.files().list(q=query).execute()
            files = results.get('files', [])
            
            if not files:
                raise FileNotFoundError("Arquivo 'cnpj.db' não encontrado")
            
            file_id = files[0]['id']
            file_size = files[0].get('size', 'Unknown')
            Actor.log.info(f"✅ Arquivo cnpj.db encontrado: {file_id} ({file_size} bytes)")
            
            # Baixar arquivo para arquivo temporário
            Actor.log.info("📥 Baixando cnpj.db...")
            request = self.service.files().get_media(fileId=file_id)
            
            # Criar arquivo temporário
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            self.temp_db_path = temp_file.name
            
            # Download em chunks
            downloader = io.BytesIO()
            done = False
            while not done:
                status, done = request.next_chunk(out=downloader)
                if status:
                    Actor.log.info(f"📥 Download progress: {int(status.progress() * 100)}%")
            
            # Salvar arquivo
            with open(self.temp_db_path, 'wb') as f:
                f.write(downloader.getvalue())
            
            Actor.log.info(f"✅ cnpj.db baixado para: {self.temp_db_path}")
            return True
            
        except Exception as e:
            Actor.log.error(f"❌ Erro ao baixar cnpj.db: {e}")
            return False
    
    def normalize_cnpj(self, cnpj: str) -> str:
        """Normaliza CNPJ removendo formatação"""
        if not cnpj:
            return ""
        return ''.join(filter(str.isdigit, str(cnpj)))
    
    def validate_cnpj(self, cnpj: str) -> bool:
        """Valida formato do CNPJ"""
        cnpj_clean = self.normalize_cnpj(cnpj)
        return len(cnpj_clean) == 14 and not all(d == cnpj_clean[0] for d in cnpj_clean)
    
    def format_cnpj(self, cnpj: str) -> str:
        """Formata CNPJ para exibição"""
        cnpj_clean = self.normalize_cnpj(cnpj)
        if len(cnpj_clean) != 14:
            return cnpj
        return f"{cnpj_clean[:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:]}"
    
    async def query_cnpj(self, cnpj: str) -> Dict[str, Any]:
        """Consulta CNPJ específico na base"""
        try:
            # Validar CNPJ
            if not self.validate_cnpj(cnpj):
                return {
                    "success": False,
                    "error": "CNPJ inválido",
                    "message": "CNPJ deve ter 14 dígitos válidos",
                    "cnpj_input": cnpj
                }
            
            cnpj_clean = self.normalize_cnpj(cnpj)
            
            # Conectar ao banco SQLite
            if not self.temp_db_path or not os.path.exists(self.temp_db_path):
                return {
                    "success": False,
                    "error": "Base de dados não disponível",
                    "message": "Arquivo cnpj.db não foi baixado corretamente"
                }
            
            Actor.log.info(f"🔍 Consultando CNPJ: {cnpj_clean}")
            
            conn = sqlite3.connect(self.temp_db_path)
            cursor = conn.cursor()
            
            # Consultar empresa
            cursor.execute("SELECT * FROM empresas WHERE cnpj = ?", (cnpj_clean,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return {
                    "success": False,
                    "error": "CNPJ não encontrado",
                    "cnpj": cnpj_clean,
                    "cnpj_formatted": self.format_cnpj(cnpj_clean)
                }
            
            # Obter nomes das colunas
            columns = [desc[0] for desc in cursor.description]
            empresa_data = dict(zip(columns, result))
            
            conn.close()
            
            # Formatar resposta
            response = {
                "success": True,
                "cnpj": cnpj_clean,
                "cnpj_formatted": self.format_cnpj(cnpj_clean),
                "dados_cadastrais": {
                    "razao_social": empresa_data.get('razao_social'),
                    "nome_fantasia": empresa_data.get('nome_fantasia', ''),
                    "situacao_cadastral": empresa_data.get('situacao_cadastral'),
                    "data_situacao_cadastral": empresa_data.get('data_situacao_cadastral'),
                    "natureza_juridica": empresa_data.get('natureza_juridica'),
                    "porte_empresa": empresa_data.get('porte_empresa'),
                    "capital_social": empresa_data.get('capital_social'),
                    "data_inicio_atividade": empresa_data.get('data_inicio_atividade'),
                    "opcao_simples": empresa_data.get('opcao_simples')
                },
                "endereco": {
                    "tipo_logradouro": empresa_data.get('tipo_logradouro'),
                    "logradouro": empresa_data.get('logradouro'),
                    "numero": empresa_data.get('numero'),
                    "complemento": empresa_data.get('complemento'),
                    "bairro": empresa_data.get('bairro'),
                    "cep": empresa_data.get('cep'),
                    "municipio": empresa_data.get('municipio'),
                    "uf": empresa_data.get('uf')
                },
                "atividade_economica": {
                    "cnae_principal": empresa_data.get('cnae_principal'),
                    "cnae_descricao": empresa_data.get('cnae_descricao')
                },
                "contato": {
                    "telefone": empresa_data.get('telefone', ''),
                    "email": empresa_data.get('email', '')
                },
                "metadata": {
                    "fonte": "Google Drive - cnpj.db",
                    "consulta_via": "Apify Actor",
                    "timestamp": Actor.get_env().get('APIFY_STARTED_AT')
                }
            }
            
            Actor.log.info(f"✅ CNPJ encontrado: {empresa_data.get('razao_social')}")
            return response
            
        except Exception as e:
            Actor.log.error(f"❌ Erro na consulta CNPJ: {e}")
            return {
                "success": False,
                "error": "Erro interno",
                "message": str(e),
                "cnpj": cnpj
            }
    
    def cleanup(self):
        """Limpa arquivos temporários"""
        if self.temp_db_path and os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)
            Actor.log.info("🧹 Arquivo temporário removido")

async def main():
    """Função principal do Actor"""
    async with Actor:
        Actor.log.info("🚀 Iniciando CNPJ Google Drive Connector")
        
        # Obter input
        actor_input = await Actor.get_input() or {}
        Actor.log.info(f"📥 Input recebido: {actor_input}")
        
        # Verificar se tem input
        if not actor_input:
            Actor.log.warning("⚠️ Nenhum input fornecido - usando CNPJ de teste")
            actor_input = {
                "operation": "query_cnpj",
                "cnpj": "43227497000198"
            }
        
        # Inicializar conector
        connector = CNPJGoogleDriveConnector()
        
        try:
            # Conectar ao Google Drive
            if not await connector.initialize_drive_connection():
                Actor.log.error("Falha na conexão com Google Drive")
                return
                return
            
            # Baixar base de dados
            if not await connector.find_cnpj_database():
                Actor.log.error("Falha ao baixar base de dados CNPJ")
                return
                return
            
            # Processar solicitação
            operation = actor_input.get('operation', 'query_cnpj')
            
            if operation == 'query_cnpj':
                cnpj = actor_input.get('cnpj')
                if not cnpj:
                    Actor.log.error("CNPJ não fornecido no input")
                    return
                    return
                
                result = await connector.query_cnpj(cnpj)
                await Actor.push_data(result)
                
                if result.get("success"):
                    Actor.log.info(f"✅ Consulta realizada: {result['dados_cadastrais']['razao_social']}")
                else:
                    Actor.log.warning(f"⚠️ CNPJ não encontrado: {cnpj}")
                
            else:
                Actor.log.error(f"Operação não suportada: {operation}")
                return
                return
            
            Actor.log.info("✅ Execução concluída com sucesso")
            
        except Exception as e:
            Actor.log.error(f"❌ Erro fatal: {e}")
            return
            
        finally:
            # Cleanup
            connector.cleanup()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
