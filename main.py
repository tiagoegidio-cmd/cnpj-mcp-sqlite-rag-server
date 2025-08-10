#!/usr/bin/env python3
"""
Apify Actor: CNPJ Google Drive Connector
Conecta ao Google Drive via OAuth 2.0, baixa base CNPJ e executa consultas
Para uso com Claude Projetos
"""

import os
import json
import sqlite3
import tempfile
from typing import Dict, Any, Optional
from apify import Actor
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import io

class CNPJGoogleDriveConnector:
    """Conector principal para CNPJ via Google Drive usando OAuth 2.0"""
    
    def __init__(self):
        self.service = None
        self.temp_db_path = None
        self.credentials = None
        
    async def initialize_drive_connection(self):
        """Inicializa conexão com Google Drive usando OAuth 2.0"""
        try:
            Actor.log.info("🔐 Inicializando conexão OAuth 2.0...")
            
            # Configuração OAuth 2.0
            client_config = {
                "web": {
                    "client_id": "388098591605-eunqel7pdgid80j7v1c49vleetpasn7c.apps.googleusercontent.com",
                    "project_id": "bd-cnpj",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": os.getenv('GOOGLE_CLIENT_SECRET', ''),
                    "redirect_uris": ["http://localhost:8080/callback"]
                }
            }
            
            # Verificar se temos token de refresh no environment
            refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')
            access_token = os.getenv('GOOGLE_ACCESS_TOKEN')
            
            if refresh_token and access_token:
                Actor.log.info("🔑 Usando tokens existentes...")
                
                # Criar credenciais a partir dos tokens
                self.credentials = Credentials(
                    token=access_token,
                    refresh_token=refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=client_config["web"]["client_id"],
                    client_secret=client_config["web"]["client_secret"],
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
                
                # Verificar se o token precisa ser renovado
                if self.credentials.expired:
                    Actor.log.info("🔄 Renovando access token...")
                    self.credentials.refresh(Request())
                    
            else:
                Actor.log.error("❌ Tokens OAuth não encontrados no environment")
                Actor.log.info("💡 Configure GOOGLE_ACCESS_TOKEN e GOOGLE_REFRESH_TOKEN")
                return False
            
            # Criar serviço Google Drive
            self.service = build('drive', 'v3', credentials=self.credentials)
            
            # Testar conexão
            about = self.service.about().get(fields="user").execute()
            user_email = about.get('user', {}).get('emailAddress', 'Unknown')
            
            Actor.log.info(f"✅ Conectado como: {user_email}")
            return True
            
        except Exception as e:
            Actor.log.error(f"❌ Erro ao conectar Google Drive: {e}")
            return False
    
    async def find_cnpj_database(self):
        """Encontra e baixa o arquivo cnpj.db do Google Drive compartilhado"""
        try:
            Actor.log.info("🔍 Procurando arquivo cnpj.db em 'Compartilhados comigo'...")
            
            # Buscar em arquivos compartilhados
            # Primeiro, vamos buscar a pasta "BASE DE DADOS" compartilhada
            query = "name='BASE DE DADOS' and sharedWithMe=true and mimeType='application/vnd.google-apps.folder'"
            results = self.service.files().list(
                q=query,
                fields="files(id,name,owners,permissions,parents)"
            ).execute()
            
            folders = results.get('files', [])
            Actor.log.info(f"📁 Pastas 'BASE DE DADOS' encontradas: {len(folders)}")
            
            if not folders:
                # Tentar buscar diretamente a pasta BASE B2B
                Actor.log.info("🔍 Buscando pasta 'BASE B2B' diretamente...")
                query = "name='BASE B2B' and sharedWithMe=true and mimeType='application/vnd.google-apps.folder'"
                results = self.service.files().list(
                    q=query,
                    fields="files(id,name,owners,permissions,parents)"
                ).execute()
                folders = results.get('files', [])
                
                if folders:
                    b2b_folder_id = folders[0]['id']
                    Actor.log.info(f"✅ Pasta BASE B2B encontrada diretamente: {b2b_folder_id}")
                else:
                    raise FileNotFoundError("Nenhuma pasta 'BASE DE DADOS' ou 'BASE B2B' encontrada em compartilhados")
            else:
                base_folder_id = folders[0]['id']
                Actor.log.info(f"✅ Pasta BASE DE DADOS encontrada: {base_folder_id}")
                
                # Buscar pasta "BASE B2B" dentro de "BASE DE DADOS"
                query = f"name='BASE B2B' and parents in '{base_folder_id}' and mimeType='application/vnd.google-apps.folder'"
                results = self.service.files().list(
                    q=query,
                    fields="files(id,name,size)"
                ).execute()
                folders = results.get('files', [])
                
                if not folders:
                    raise FileNotFoundError("Pasta 'BASE B2B' não encontrada dentro de 'BASE DE DADOS'")
                
                b2b_folder_id = folders[0]['id']
                Actor.log.info(f"✅ Pasta BASE B2B encontrada: {b2b_folder_id}")
            
            # Buscar arquivo cnpj.db na pasta BASE B2B
            query = f"name='cnpj.db' and parents in '{b2b_folder_id}'"
            results = self.service.files().list(
                q=query,
                fields="files(id,name,size,modifiedTime)"
            ).execute()
            files = results.get('files', [])
            
            if not files:
                # Tentar buscar arquivo diretamente por nome em compartilhados
                Actor.log.info("🔍 Buscando cnpj.db diretamente em compartilhados...")
                query = "name='cnpj.db' and sharedWithMe=true"
                results = self.service.files().list(
                    q=query,
                    fields="files(id,name,size,modifiedTime)"
                ).execute()
                files = results.get('files', [])
                
                if not files:
                    raise FileNotFoundError("Arquivo 'cnpj.db' não encontrado")
            
            file_info = files[0]
            file_id = file_info['id']
            file_size = file_info.get('size', 'Unknown')
            modified_time = file_info.get('modifiedTime', 'Unknown')
            
            Actor.log.info(f"✅ Arquivo cnpj.db encontrado:")
            Actor.log.info(f"   ID: {file_id}")
            Actor.log.info(f"   Tamanho: {file_size} bytes")
            Actor.log.info(f"   Modificado: {modified_time}")
            
            # Baixar arquivo para arquivo temporário
            Actor.log.info("📥 Baixando cnpj.db...")
            request = self.service.files().get_media(fileId=file_id)
            
            # Criar arquivo temporário
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            self.temp_db_path = temp_file.name
            
            # Download direto (para arquivos menores)
            file_content = request.execute()
            
            # Salvar arquivo
            with open(self.temp_db_path, 'wb') as f:
                f.write(file_content)
            
            # Verificar se o arquivo foi baixado corretamente
            if os.path.exists(self.temp_db_path):
                downloaded_size = os.path.getsize(self.temp_db_path)
                Actor.log.info(f"✅ cnpj.db baixado: {downloaded_size} bytes → {self.temp_db_path}")
                
                # Teste rápido da conexão SQLite
                try:
                    conn = sqlite3.connect(self.temp_db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM empresas LIMIT 1")
                    count = cursor.fetchone()[0]
                    conn.close()
                    Actor.log.info(f"✅ Base SQLite válida: {count} empresas")
                    return True
                except Exception as e:
                    Actor.log.error(f"❌ Erro ao validar SQLite: {e}")
                    return False
            else:
                Actor.log.error("❌ Arquivo não foi salvo corretamente")
                return False
            
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
            
            Actor.log.info(f"🔍 Consultando CNPJ: {self.format_cnpj(cnpj_clean)}")
            
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
                    "cnpj_formatted": self.format_cnpj(cnpj_clean),
                    "message": "Este CNPJ não está presente na base de dados"
                }
            
            # Obter nomes das colunas
            columns = [desc[0] for desc in cursor.description]
            empresa_data = dict(zip(columns, result))
            
            conn.close()
            
            # Formatar endereço completo
            endereco_parts = []
            if empresa_data.get('tipo_logradouro') and empresa_data.get('logradouro'):
                endereco_parts.append(f"{empresa_data['tipo_logradouro']} {empresa_data['logradouro']}")
            elif empresa_data.get('logradouro'):
                endereco_parts.append(empresa_data['logradouro'])
                
            if empresa_data.get('numero'):
                endereco_parts.append(f", {empresa_data['numero']}")
            if empresa_data.get('complemento'):
                endereco_parts.append(f", {empresa_data['complemento']}")
            if empresa_data.get('bairro'):
                endereco_parts.append(f" - {empresa_data['bairro']}")
            if empresa_data.get('municipio') and empresa_data.get('uf'):
                endereco_parts.append(f" - {empresa_data['municipio']}/{empresa_data['uf']}")
            if empresa_data.get('cep'):
                cep = empresa_data['cep']
                if len(cep) == 8:
                    cep = f"{cep[:5]}-{cep[5:]}"
                endereco_parts.append(f" - CEP: {cep}")
            
            endereco_completo = ''.join(endereco_parts)
            
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
                    "endereco_completo": endereco_completo,
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
                    "consulta_via": "Apify Actor OAuth 2.0",
                    "timestamp": Actor.get_env().get('APIFY_STARTED_AT'),
                    "arquivo_modificado": empresa_data.get('created_at')
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
    
    async def search_by_name(self, nome: str, limit: int = 10) -> Dict[str, Any]:
        """Busca empresas por nome/razão social"""
        try:
            if not self.temp_db_path or not os.path.exists(self.temp_db_path):
                return {
                    "success": False,
                    "error": "Base de dados não disponível"
                }
            
            Actor.log.info(f"🔍 Buscando empresas com nome: {nome}")
            
            conn = sqlite3.connect(self.temp_db_path)
            cursor = conn.cursor()
            
            # Buscar por nome
            cursor.execute("""
                SELECT cnpj, razao_social, nome_fantasia, situacao_cadastral, municipio, uf
                FROM empresas 
                WHERE razao_social LIKE ? OR nome_fantasia LIKE ?
                LIMIT ?
            """, (f'%{nome}%', f'%{nome}%', limit))
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                return {
                    "success": True,
                    "total_found": 0,
                    "empresas": [],
                    "message": f"Nenhuma empresa encontrada com o nome '{nome}'"
                }
            
            empresas = []
            for row in results:
                empresa = {
                    "cnpj": row[0],
                    "cnpj_formatted": self.format_cnpj(row[0]),
                    "razao_social": row[1],
                    "nome_fantasia": row[2] or '',
                    "situacao_cadastral": row[3],
                    "municipio": row[4],
                    "uf": row[5]
                }
                empresas.append(empresa)
            
            return {
                "success": True,
                "total_found": len(empresas),
                "empresas": empresas,
                "busca_termo": nome
            }
            
        except Exception as e:
            Actor.log.error(f"❌ Erro na busca por nome: {e}")
            return {
                "success": False,
                "error": "Erro na busca",
                "message": str(e)
            }
    
    def cleanup(self):
        """Limpa arquivos temporários"""
        if self.temp_db_path and os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)
            Actor.log.info("🧹 Arquivo temporário removido")

async def main():
    """Função principal do Actor"""
    async with Actor:
        Actor.log.info("🚀 Iniciando CNPJ Google Drive Connector OAuth 2.0")
        
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
                await Actor.push_data({
                    "success": False,
                    "error": "Falha na conexão OAuth",
                    "message": "Verifique as variáveis GOOGLE_ACCESS_TOKEN e GOOGLE_REFRESH_TOKEN"
                })
                return
            
            # Baixar base de dados
            if not await connector.find_cnpj_database():
                await Actor.push_data({
                    "success": False,
                    "error": "Base de dados não encontrada",
                    "message": "Arquivo cnpj.db não foi encontrado no Google Drive compartilhado"
                })
                return
            
            # Processar solicitação
            operation = actor_input.get('operation', 'query_cnpj')
            
            if operation == 'query_cnpj':
                cnpj = actor_input.get('cnpj')
                if not cnpj:
                    await Actor.push_data({
                        "success": False,
                        "error": "CNPJ não fornecido",
                        "message": "Parâmetro 'cnpj' é obrigatório"
                    })
                    return
                
                result = await connector.query_cnpj(cnpj)
                await Actor.push_data(result)
                
                if result.get("success"):
                    Actor.log.info(f"✅ Consulta realizada: {result['dados_cadastrais']['razao_social']}")
                else:
                    Actor.log.warning(f"⚠️ CNPJ não encontrado: {cnpj}")
                    
            elif operation == 'search_by_name':
                nome = actor_input.get('nome', actor_input.get('name'))
                limit = actor_input.get('limit', 10)
                
                if not nome:
                    await Actor.push_data({
                        "success": False,
                        "error": "Nome não fornecido",
                        "message": "Parâmetro 'nome' é obrigatório para busca"
                    })
                    return
                
                result = await connector.search_by_name(nome, limit)
                await Actor.push_data(result)
                
                if result.get("success"):
                    Actor.log.info(f"✅ Busca realizada: {result['total_found']} empresas encontradas")
                else:
                    Actor.log.warning(f"⚠️ Erro na busca: {nome}")
                
            else:
                await Actor.push_data({
                    "success": False,
                    "error": "Operação não suportada",
                    "message": f"Operação '{operation}' não é válida. Use 'query_cnpj' ou 'search_by_name'"
                })
                return
            
            Actor.log.info("✅ Execução concluída com sucesso")
            
        except Exception as e:
            Actor.log.error(f"❌ Erro fatal: {e}")
            await Actor.push_data({
                "success": False,
                "error": "Erro fatal",
                "message": str(e)
            })
            
        finally:
            # Cleanup
            connector.cleanup()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())