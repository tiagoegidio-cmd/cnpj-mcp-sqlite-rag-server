#!/usr/bin/env python3
"""
CNPJ MCP SQLite RAG Server - Versão GitHub
Servidor MCP que acessa banco SQLite no Google Drive e oferece capacidades RAG
Estrutura: BASE DE DADOS/BASE B2B/cnpj.db
"""

import asyncio
import json
import sqlite3
import tempfile
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
    )
except ImportError as e:
    print(f"❌ Erro ao importar MCP: {e}")
    print("📦 Instale com: pip install mcp")
    raise

# Google Drive API
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    import io
    from googleapiclient.http import MediaIoBaseDownload
except ImportError as e:
    print(f"❌ Erro ao importar Google APIs: {e}")
    print("📦 Instale com: pip install google-api-python-client google-auth-oauthlib")
    raise

# RAG components
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.config import Settings
    import hashlib
except ImportError as e:
    print(f"❌ Erro ao importar componentes RAG: {e}")
    print("📦 Instale com: pip install sentence-transformers chromadb numpy")
    raise

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteRAGServer:
    """Servidor MCP com RAG para SQLite no Google Drive"""
    
    def __init__(self):
        self.server = Server("cnpj-sqlite-rag-server")
        self.drive_service = None
        self.db_path = None
        self.embedding_model = None
        self.vector_db = None
        self.db_schema = {}
        
        # Google Drive API scopes
        self.SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        
        # Initialize components
        self.setup_handlers()
        
    def setup_handlers(self):
        """Configure MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="natural_query",
                    description="Execute consulta em linguagem natural no banco SQLite CNPJ",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Pergunta em linguagem natural sobre os dados CNPJ"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="sql_query",
                    description="Execute consulta SQL direta no banco CNPJ",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "Comando SQL a ser executado (apenas SELECT)"
                            }
                        },
                        "required": ["sql"]
                    }
                ),
                Tool(
                    name="get_schema",
                    description="Obtém a estrutura do banco de dados CNPJ",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="semantic_search",
                    description="Busca semântica nos dados do banco CNPJ",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Termo ou frase para busca semântica"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Número máximo de resultados",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                # Ensure database is loaded
                await self.ensure_database_loaded()
                
                if name == "natural_query":
                    result = await self.handle_natural_query(arguments["query"])
                elif name == "sql_query":
                    result = await self.handle_sql_query(arguments["sql"])
                elif name == "get_schema":
                    result = await self.handle_get_schema()
                elif name == "semantic_search":
                    result = await self.handle_semantic_search(
                        arguments["query"], 
                        arguments.get("limit", 10)
                    )
                else:
                    result = f"Ferramenta desconhecida: {name}"
                
                return [TextContent(type="text", text=str(result))]
                
            except Exception as e:
                logger.error(f"Erro ao executar ferramenta {name}: {e}")
                return [TextContent(type="text", text=f"Erro: {str(e)}")]

    async def authenticate_google_drive(self):
        """Authenticate with Google Drive API"""
        creds = None
        token_path = Path("token.json")
        credentials_path = Path("credentials.json")
        
        # Check if token exists
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), self.SCOPES)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not credentials_path.exists():
                    raise FileNotFoundError(
                        "arquivo credentials.json não encontrado. "
                        "Baixe do Google Cloud Console e coloque na pasta do projeto."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.drive_service = build('drive', 'v3', credentials=creds)
        logger.info("Autenticação Google Drive concluída")

    async def find_database_file(self):
        """Find SQLite database file in Google Drive: BASE DE DADOS/BASE B2B/cnpj.db"""
        try:
            # Step 1: Search for folder "BASE DE DADOS"
            base_folder_query = "name='BASE DE DADOS' and mimeType='application/vnd.google-apps.folder'"
            base_results = self.drive_service.files().list(
                q=base_folder_query,
                fields="files(id, name)"
            ).execute()
            
            base_folders = base_results.get('files', [])
            if not base_folders:
                raise Exception("Pasta 'BASE DE DADOS' não encontrada")
            
            base_folder_id = base_folders[0]['id']
            logger.info(f"Pasta 'BASE DE DADOS' encontrada: {base_folder_id}")
            
            # Step 2: Search for subfolder "BASE B2B" inside "BASE DE DADOS"
            b2b_folder_query = f"'{base_folder_id}' in parents and name='BASE B2B' and mimeType='application/vnd.google-apps.folder'"
            b2b_results = self.drive_service.files().list(
                q=b2b_folder_query,
                fields="files(id, name)"
            ).execute()
            
            b2b_folders = b2b_results.get('files', [])
            if not b2b_folders:
                raise Exception("Pasta 'BASE B2B' não encontrada dentro de 'BASE DE DADOS'")
            
            b2b_folder_id = b2b_folders[0]['id']
            logger.info(f"Pasta 'BASE B2B' encontrada: {b2b_folder_id}")
            
            # Step 3: Search for "cnpj.db" file inside "BASE B2B"
            db_query = f"'{b2b_folder_id}' in parents and name='cnpj.db'"
            db_results = self.drive_service.files().list(
                q=db_query,
                fields="files(id, name, size, mimeType)"
            ).execute()
            
            db_files = db_results.get('files', [])
            if not db_files:
                # Fallback: search for any .db file in the folder
                fallback_query = f"'{b2b_folder_id}' in parents and (name contains '.db' or name contains '.sqlite')"
                fallback_results = self.drive_service.files().list(
                    q=fallback_query,
                    fields="files(id, name, size, mimeType)"
                ).execute()
                
                db_files = fallback_results.get('files', [])
                if not db_files:
                    raise Exception("Arquivo 'cnpj.db' não encontrado na pasta 'BASE B2B'")
                
                logger.info(f"Arquivo alternativo encontrado: {db_files[0]['name']}")
            
            db_file = db_files[0]
            logger.info(f"Arquivo de banco encontrado: {db_file['name']} (ID: {db_file['id']})")
            
            return db_file
            
        except Exception as e:
            logger.error(f"Erro ao procurar arquivo de banco: {e}")
            logger.error("Estrutura esperada: BASE DE DADOS/BASE B2B/cnpj.db")
            raise

    async def download_database(self, file_info):
        """Download SQLite database from Google Drive"""
        try:
            file_id = file_info['id']
            file_name = file_info['name']
            
            logger.info(f"Baixando arquivo: {file_name}")
            
            # Create temporary file
            temp_dir = Path(tempfile.gettempdir()) / "mcp_sqlite_rag"
            temp_dir.mkdir(exist_ok=True)
            
            db_path = temp_dir / file_name
            
            # Download file
            request = self.drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    logger.info(f"Download {int(status.progress() * 100)}%")
            
            # Save to file
            fh.seek(0)
            with open(db_path, 'wb') as f:
                f.write(fh.read())
            
            self.db_path = str(db_path)
            logger.info(f"Banco baixado para: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Erro ao baixar banco: {e}")
            raise

    async def load_database_schema(self):
        """Load database schema and prepare for RAG"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            self.db_schema = {}
            
            for table in tables:
                table_name = table[0]
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                # Get sample data
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                sample_data = cursor.fetchall()
                
                self.db_schema[table_name] = {
                    'columns': columns,
                    'sample_data': sample_data
                }
            
            conn.close()
            logger.info(f"Schema carregado: {len(self.db_schema)} tabelas")
            
        except Exception as e:
            logger.error(f"Erro ao carregar schema: {e}")
            raise

    async def initialize_rag(self):
        """Initialize RAG components"""
        try:
            # Initialize embedding model
            logger.info("Carregando modelo de embeddings...")
            self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            
            # Initialize vector database
            chroma_path = Path(tempfile.gettempdir()) / "mcp_sqlite_rag" / "chroma"
            chroma_path.mkdir(parents=True, exist_ok=True)
            
            self.vector_db = chromadb.PersistentClient(path=str(chroma_path))
            
            # Create or get collection
            collection_name = "sqlite_data"
            try:
                self.collection = self.vector_db.get_collection(collection_name)
                logger.info("Coleção existente carregada")
            except:
                self.collection = self.vector_db.create_collection(collection_name)
                await self.populate_vector_db()
                logger.info("Nova coleção criada e populada")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar RAG: {e}")
            raise

    async def populate_vector_db(self):
        """Populate vector database with SQLite data"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            documents = []
            metadatas = []
            ids = []
            
            for table_name, schema_info in self.db_schema.items():
                # Add table schema as document
                schema_text = f"Tabela {table_name}: " + ", ".join([
                    f"{col[1]} ({col[2]})" for col in schema_info['columns']
                ])
                
                documents.append(schema_text)
                metadatas.append({"type": "schema", "table": table_name})
