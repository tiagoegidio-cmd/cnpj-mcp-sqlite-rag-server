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
            # Buscar credenciais do environment
            credentials_json = os.getenv('GOOGLE_CREDENTIALS')
            if not credentials_json:
                raise ValueError("GOOGLE_CREDENTIALS não encontrado no environment")
            
            await Actor.log.info("🔐 Carregando credenciais Google...")
            
            # Carregar credenciais
            credentials_info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            
            # Criar serviço Google Drive
            self.service = build('drive', 'v3', credentials=credentials)
            
            await Actor.log.info("✅ Conexão com Google Drive estabelecida")
            return True
            
        except Exception as e:
            await Actor.log.error(f"❌ Erro ao conectar Google Drive: {e}")
            return False
    
    async def find_cnpj_database(self):
        """Encontra e baixa o arquivo cnpj.db do Google Drive"""
        try:
            await Actor.log.info("🔍 Procurando pasta BASE DE DADOS...")
            
            # Buscar pasta "BASE DE DADOS"
            query = "name='BASE DE DADOS' and mimeType='application/vnd.google-apps.folder'"
            results = self.service.files().list(q=query).execute()
            folders = results.get('files', [])
            
            if not folders:
                raise FileNotFoundError("Pasta 'BASE DE DADOS' não encontrada")
            
            base_folder_id = folders[0]['id']
            await Actor.log.info(f"✅ Pasta BASE DE DADOS encontrada: {base_folder_id}")
            
            # Buscar pasta "BASE B2B" dentro de "BASE DE DADOS"
            query = f"name='BASE B2B' and parents in '{base_folder_id}' and mimeType='application/vnd.google-apps.folder'"
            results = self.service.files().list(q=query).execute()
            folders = results.get('files', [])
            
            if not folders:
                raise FileNotFoundError("Pasta 'BASE B2B' não encontrada dentro de 'BASE DE DADOS'")
            
            b2b_folder_id = folders[0]['id']
            await Actor.log.info(f"✅ Pasta BASE B2B encontrada: {b2b_folder_id}")
            
            # Buscar arquivo cnpj.db
            query = f"name='cnpj.db' and parents in '{b2b_folder_id}'"
            results = self.service.files().list(q=query).execute()
            files = results.get('files', [])
            
            if not files:
                raise FileNotFoundError("Arquivo 'cnpj.db' não encontrado")
            
            file_id = files[0]['id']
            file_size = files[0].get('size', 'Unknown')
            await Actor.log.info(f"✅ Arquivo cnpj.db encontrado: {file_id} ({file_size} bytes)")
            
            # Baixar arquivo para arquivo temporário
            await Actor.log.info("📥 Baixando cnpj.db...")
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
                    await Actor.log.info(f"📥 Download progress: {int(status.progress() * 100)}%")
            
            # Salvar arquivo
            with open(self.temp_db_path, 'wb') as f:
                f.write(downloader.getvalue())
            
            await Actor.log.info(f"✅ cnpj.db baixado para: {self.temp_db_path}")
            return True
            
        except Exception as e:
            await Actor.log.error(f"❌ Erro ao baixar cnpj.db: {e}")
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
            
            await Actor.log.info(f"🔍 Consultando CNPJ: {cnpj_clean}")
            
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
            
            await Actor.log.info(f"✅ CNPJ encontrado: {empresa_data.get('razao_social')}")
            return response
            
        except Exception as e:
            await Actor.log.error(f"❌ Erro na consulta CNPJ: {e}")
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
        await Actor.log.info("🚀 Iniciando CNPJ Google Drive Connector")
        
        # Obter input
        actor_input = await Actor.get_input() or {}
        await Actor.log.info(f"📥 Input recebido: {actor_input}")
        
        # Verificar se tem input
        if not actor_input:
            await Actor.log.warning("⚠️ Nenhum input fornecido - usando CNPJ de teste")
            actor_input = {
                "operation": "query_cnpj",
                "cnpj": "43227497000198"
            }
        
        # Inicializar conector
        connector = CNPJGoogleDriveConnector()
        
        try:
            # Conectar ao Google Drive
            if not await connector.initialize_drive_connection():
                await Actor.fail("Falha na conexão com Google Drive")
                return
            
            # Baixar base de dados
            if not await connector.find_cnpj_database():
                await Actor.fail("Falha ao baixar base de dados CNPJ")
                return
            
            # Processar solicitação
            operation = actor_input.get('operation', 'query_cnpj')
            
            if operation == 'query_cnpj':
                cnpj = actor_input.get('cnpj')
                if not cnpj:
                    await Actor.fail("CNPJ não fornecido no input")
                    return
                
                result = await connector.query_cnpj(cnpj)
                await Actor.push_data(result)
                
                if result.get("success"):
                    await Actor.log.info(f"✅ Consulta realizada: {result['dados_cadastrais']['razao_social']}")
                else:
                    await Actor.log.warning(f"⚠️ CNPJ não encontrado: {cnpj}")
                
            else:
                await Actor.fail(f"Operação não suportada: {operation}")
                return
            
            await Actor.log.info("✅ Execução concluída com sucesso")
            
        except Exception as e:
            await Actor.log.error(f"❌ Erro fatal: {e}")
            await Actor.fail(str(e))
            
        finally:
            # Cleanup
            connector.cleanup()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
