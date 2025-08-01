#!/usr/bin/env python3
"""
MCP SQLite RAG Server
Servidor MCP que acessa banco SQLite no Google Drive e oferece capacidades RAG
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

# Google Drive API
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import io
from googleapiclient.http import MediaIoBaseDownload

# RAG components
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteRAGServer:
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
                    description="Execute consulta em linguagem natural no banco SQLite",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Pergunta em linguagem natural sobre os dados"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="sql_query",
                    description="Execute consulta SQL direta no banco",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "Comando SQL a ser executado"
                            }
                        },
                        "required": ["sql"]
                    }
                ),
                Tool(
                    name="get_schema",
                    description="Obtém a estrutura do banco de dados",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="semantic_search",
                    description="Busca semântica nos dados do banco",
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
        """Find SQLite database file in Google Drive"""
        try:
            # Search for folder "BASE DE DADOS"
            folder_query = "name='BASE DE DADOS' and mimeType='application/vnd.google-apps.folder'"
            folder_results = self.drive_service.files().list(
                q=folder_query,
                fields="files(id, name)"
            ).execute()
            
            folders = folder_results.get('files', [])
            if not folders:
                raise Exception("Pasta 'BASE DE DADOS' não encontrada")
            
            folder_id = folders[0]['id']
            logger.info(f"Pasta 'BASE DE DADOS' encontrada: {folder_id}")
            
            # Search for SQLite files in the folder
            db_query = f"'{folder_id}' in parents and (name contains '.sqlite' or name contains '.db')"
            db_results = self.drive_service.files().list(
                q=db_query,
                fields="files(id, name, size)"
            ).execute()
            
            db_files = db_results.get('files', [])
            if not db_files:
                raise Exception("Nenhum arquivo SQLite encontrado na pasta")
            
            # Return the first database file found
            return db_files[0]
            
        except Exception as e:
            logger.error(f"Erro ao procurar arquivo de banco: {e}")
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
                ids.append(f"schema_{table_name}")
                
                # Add sample data as documents
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
                rows = cursor.fetchall()
                
                for i, row in enumerate(rows):
                    row_text = f"Dados da tabela {table_name}: " + ", ".join([
                        f"{key}={value}" for key, value in dict(row).items()
                    ])
                    
                    documents.append(row_text)
                    metadatas.append({"type": "data", "table": table_name, "row": i})
                    ids.append(f"data_{table_name}_{i}")
            
            # Generate embeddings and store
            if documents:
                embeddings = self.embedding_model.encode(documents)
                
                self.collection.add(
                    embeddings=embeddings.tolist(),
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logger.info(f"Vector DB populado com {len(documents)} documentos")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao popular vector DB: {e}")
            raise

    async def ensure_database_loaded(self):
        """Ensure database is loaded and ready"""
        if not self.db_path:
            await self.authenticate_google_drive()
            file_info = await self.find_database_file()
            await self.download_database(file_info)
            await self.load_database_schema()
            await self.initialize_rag()

    async def handle_natural_query(self, query: str) -> str:
        """Handle natural language query"""
        try:
            # Use RAG to find relevant context
            results = self.collection.query(
                query_texts=[query],
                n_results=5
            )
            
            context = ""
            if results['documents']:
                context = "\n".join(results['documents'][0])
            
            # Convert natural language to SQL (simplified approach)
            # In a real implementation, you might use an LLM here
            sql_query = await self.natural_to_sql(query, context)
            
            # Execute the generated SQL
            result = await self.execute_sql(sql_query)
            
            return f"Consulta: {query}\nSQL gerado: {sql_query}\nResultado:\n{result}"
            
        except Exception as e:
            return f"Erro na consulta natural: {str(e)}"

    async def natural_to_sql(self, query: str, context: str) -> str:
        """Convert natural language to SQL (simplified)"""
        # This is a simplified version. In production, use an LLM
        query_lower = query.lower()
        
        # Simple pattern matching
        if "todos" in query_lower or "listar" in query_lower:
            # Find table name from context
            for table_name in self.db_schema.keys():
                if table_name.lower() in query_lower:
                    return f"SELECT * FROM {table_name} LIMIT 10"
            
            # Default to first table
            first_table = list(self.db_schema.keys())[0]
            return f"SELECT * FROM {first_table} LIMIT 10"
        
        # More patterns can be added here
        return "SELECT name FROM sqlite_master WHERE type='table'"

    async def handle_sql_query(self, sql: str) -> str:
        """Handle direct SQL query"""
        return await self.execute_sql(sql)

    async def execute_sql(self, sql: str) -> str:
        """Execute SQL query safely"""
        try:
            # Basic security check
            sql_lower = sql.lower().strip()
            forbidden = ['drop', 'delete', 'update', 'insert', 'alter', 'create']
            
            if any(cmd in sql_lower for cmd in forbidden):
                return "Erro: Apenas consultas SELECT são permitidas"
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(sql)
            results = cursor.fetchall()
            
            if not results:
                return "Nenhum resultado encontrado"
            
            # Format results
            output = []
            for row in results:
                row_dict = dict(row)
                output.append(str(row_dict))
            
            conn.close()
            
            return "\n".join(output[:50])  # Limit to 50 rows
            
        except Exception as e:
            return f"Erro SQL: {str(e)}"

    async def handle_get_schema(self) -> str:
        """Handle schema request"""
        try:
            schema_info = []
            
            for table_name, info in self.db_schema.items():
                columns = [f"{col[1]} ({col[2]})" for col in info['columns']]
                schema_info.append(f"Tabela {table_name}:\n  - " + "\n  - ".join(columns))
            
            return "\n\n".join(schema_info)
            
        except Exception as e:
            return f"Erro ao obter schema: {str(e)}"

    async def handle_semantic_search(self, query: str, limit: int = 10) -> str:
        """Handle semantic search"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            if not results['documents']:
                return "Nenhum resultado encontrado"
            
            output = []
            for i, doc in enumerate(results['documents'][0]):
                score = results['distances'][0][i] if results['distances'] else 0
                output.append(f"Resultado {i+1} (score: {score:.3f}):\n{doc}")
            
            return "\n\n".join(output)
            
        except Exception as e:
            return f"Erro na busca semântica: {str(e)}"

async def main():
    """Main function to run the MCP server"""
    server_instance = SQLiteRAGServer()
    
    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="cnpj-sqlite-rag-server",
                server_version="1.0.0",
                capabilities=server_instance.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
