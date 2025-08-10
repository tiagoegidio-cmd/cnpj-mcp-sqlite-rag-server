#!/usr/bin/env python3
"""
Apify Actor: CNPJ Google Drive Connector
Conecta ao Google Drive via OAuth 2.0, baixa base CNPJ e executa consultas
Sistema completo para consulta de CNPJs em tempo real
"""

import os
import json
import sqlite3
import tempfile
from typing import Dict, Any, Optional, List
from apify import Actor
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import io
import re
from datetime import datetime

class CNPJGoogleDriveConnector:
    """Conector principal para CNPJ via Google Drive usando OAuth 2.0"""
    
    def __init__(self):
        self.service = None
        self.temp_db_path = None
        self.credentials = None
        
    async def initialize_drive_connection(self):
        """Inicializa conexão com Google Drive usando OAuth 2.0"""
        try:
            CLIENT_ID = "388098591605-eunqel7pdgid80j7v1c49vleetpasn7c.apps.googleusercontent.com"
            CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
            ACCESS_TOKEN = os.getenv('GOOGLE_ACCESS_TOKEN')
            REFRESH_TOKEN = os.getenv('GOOGLE_REFRESH_TOKEN')
            
            if not all([CLIENT_SECRET, ACCESS_TOKEN, REFRESH_TOKEN]):
                Actor.log.error("❌ Variáveis OAuth não configuradas")
                return False
            
            Actor.log.info("🔐 Inicializando conexão OAuth 2.0...")
            
            # Criar credenciais OAuth
            self.credentials = Credentials(
                token=ACCESS_TOKEN,
                refresh_token=REFRESH_TOKEN,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            
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
            Actor.log.info("🔍 Procurando arquivo cnpj.db...")
            
            # Múltiplas estratégias de busca
            search_queries = [
                "name='cnpj.db' and sharedWithMe=true",
                "name='cnpj.db'",
                "name contains 'cnpj' and mimeType='application/x-sqlite3'",
                "name contains 'cnpj' and sharedWithMe=true"
            ]
            
            file_info = None
            
            for query in search_queries:
                Actor.log.info(f"🔍 Tentando: {query}")
                results = self.service.files().list(
                    q=query,
                    fields="files(id,name,size,modifiedTime,parents,owners)"
                ).execute()
                files = results.get('files', [])
                
                if files:
                    file_info = files[0]
                    Actor.log.info(f"✅ Arquivo encontrado: {file_info['name']}")
                    break
            
            if not file_info:
                # Tentar buscar pastas primeiro
                Actor.log.info("🔍 Buscando em pastas...")
                
                folder_queries = [
                    "name='BASE DE DADOS' and sharedWithMe=true and mimeType='application/vnd.google-apps.folder'",
                    "name='BASE B2B' and sharedWithMe=true and mimeType='application/vnd.google-apps.folder'"
                ]
                
                for query in folder_queries:
                    results = self.service.files().list(q=query).execute()
                    folders = results.get('files', [])
                    
                    for folder in folders:
                        # Buscar cnpj.db dentro da pasta
                        file_query = f"name='cnpj.db' and parents in '{folder['id']}'"
                        file_results = self.service.files().list(q=file_query).execute()
                        folder_files = file_results.get('files', [])
                        
                        if folder_files:
                            file_info = folder_files[0]
                            Actor.log.info(f"✅ Arquivo encontrado na pasta {folder['name']}")
                            break
                    
                    if file_info:
                        break
            
            if not file_info:
                raise FileNotFoundError("Arquivo cnpj.db não encontrado em nenhuma localização")
            
            file_id = file_info['id']
            file_size = file_info.get('size', 'Unknown')
            modified_time = file_info.get('modifiedTime', 'Unknown')
            
            Actor.log.info(f"📄 Arquivo: {file_info['name']}")
            Actor.log.info(f"📏 Tamanho: {file_size} bytes")
            Actor.log.info(f"📅 Modificado: {modified_time}")
            
            # Baixar arquivo
            Actor.log.info("📥 Baixando cnpj.db...")
            request = self.service.files().get_media(fileId=file_id)
            
            # Criar arquivo temporário
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            self.temp_db_path = temp_file.name
            
            # Download do arquivo
            file_content = request.execute()
            
            # Salvar arquivo
            with open(self.temp_db_path, 'wb') as f:
                f.write(file_content)
            
            # Verificar se o arquivo foi baixado corretamente
            if os.path.exists(self.temp_db_path):
                downloaded_size = os.path.getsize(self.temp_db_path)
                Actor.log.info(f"✅ cnpj.db baixado: {downloaded_size} bytes → {self.temp_db_path}")
                
                # Teste da base SQLite
                try:
                    conn = sqlite3.connect(self.temp_db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM empresas LIMIT 1")
                    count = cursor.fetchone()[0]
                    conn.close()
                    Actor.log.info(f"✅ Base SQLite válida: {count:,} empresas")
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
            
            # Verificar se a base está disponível
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
            
            # Formatar capital social
            capital_social = empresa_data.get('capital_social', 0)
            if capital_social:
                try:
                    capital_social = float(capital_social)
                except:
                    capital_social = 0
            
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
                    "capital_social": capital_social,
                    "capital_social_formatado": f"R$ {capital_social:,.2f}" if capital_social else "R$ 0,00",
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
                    "timestamp": datetime.now().isoformat(),
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
                ORDER BY razao_social
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
            
            Actor.log.info(f"✅ Encontradas {len(empresas)} empresas")
            
            return {
                "success": True,
                "total_found": len(empresas),
                "empresas": empresas,
                "busca_termo": nome,
                "limit_aplicado": limit
            }
            
        except Exception as e:
            Actor.log.error(f"❌ Erro na busca por nome: {e}")
            return {
                "success": False,
                "error": "Erro na busca",
                "message": str(e)
            }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas da base de dados"""
        try:
            if not self.temp_db_path or not os.path.exists(self.temp_db_path):
                return {
                    "success": False,
                    "error": "Base de dados não disponível"
                }
            
            Actor.log.info("📊 Gerando estatísticas...")
            
            conn = sqlite3.connect(self.temp_db_path)
            cursor = conn.cursor()
            
            # Total de empresas
            cursor.execute("SELECT COUNT(*) FROM empresas")
            total_empresas = cursor.fetchone()[0]
            
            # Por situação cadastral
            cursor.execute("SELECT situacao_cadastral, COUNT(*) FROM empresas GROUP BY situacao_cadastral ORDER BY COUNT(*) DESC")
            por_situacao = dict(cursor.fetchall())
            
            # Por UF
            cursor.execute("SELECT uf, COUNT(*) FROM empresas GROUP BY uf ORDER BY COUNT(*) DESC LIMIT 10")
            por_uf = dict(cursor.fetchall())
            
            # Por porte (se existe a coluna)
            try:
                cursor.execute("SELECT porte_empresa, COUNT(*) FROM empresas GROUP BY porte_empresa ORDER BY COUNT(*) DESC")
                por_porte = dict(cursor.fetchall())
            except:
                por_porte = {}
            
            conn.close()
            
            return {
                "success": True,
                "total_empresas": total_empresas,
                "total_empresas_formatado": f"{total_empresas:,}",
                "por_situacao_cadastral": por_situacao,
                "por_uf": por_uf,
                "por_porte": por_porte,
                "fonte": "Google Drive - cnpj.db",
                "gerado_em": datetime.now().isoformat()
            }
            
        except Exception as e:
            Actor.log.error(f"❌ Erro ao gerar estatísticas: {e}")
            return {
                "success": False,
                "error": "Erro ao calcular estatísticas",
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
        Actor.log.info("🚀 Iniciando CNPJ Google Drive Connector")
        
        # Obter input
        actor_input = await Actor.get_input() or {}
        Actor.log.info(f"📥 Input recebido: {actor_input}")
        
        # Verificar se tem input
        if not actor_input:
            await Actor.push_data({
                "success": False,
                "error": "Input não fornecido",
                "message": "Parâmetros necessários não foram fornecidos",
                "exemplo_uso": {
                    "consulta_cnpj": {
                        "operation": "query_cnpj",
                        "cnpj": "43227497000198"
                    },
                    "busca_nome": {
                        "operation": "search_by_name",
                        "nome": "N9 PARTICIPACOES",
                        "limit": 10
                    },
                    "estatisticas": {
                        "operation": "get_statistics"
                    }
                }
            })
            return
        
        # Inicializar conector
        connector = CNPJGoogleDriveConnector()
        
        try:
            # Conectar ao Google Drive
            if not await connector.initialize_drive_connection():
                await Actor.push_data({
                    "success": False,
                    "error": "Falha na conexão OAuth",
                    "message": "Não foi possível conectar ao Google Drive. Verifique as variáveis GOOGLE_ACCESS_TOKEN, GOOGLE_REFRESH_TOKEN e GOOGLE_CLIENT_SECRET"
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
                        "message": "Parâmetro 'cnpj' é obrigatório para consulta"
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
                    
            elif operation == 'get_statistics':
                result = await connector.get_statistics()
                await Actor.push_data(result)
                
                if result.get("success"):
                    Actor.log.info(f"✅ Estatísticas geradas: {result['total_empresas']} empresas")
                else:
                    Actor.log.warning("⚠️ Erro ao gerar estatísticas")
                
            else:
                await Actor.push_data({
                    "success": False,
                    "error": "Operação não suportada",
                    "message": f"Operação '{operation}' não é válida",
                    "operacoes_validas": ["query_cnpj", "search_by_name", "get_statistics"]
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
