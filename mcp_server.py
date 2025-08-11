#!/usr/bin/env python3
"""
MCP Server para CNPJ Google Drive Connector
Arquivo: mcp_server.py
"""

import asyncio
import json
import sys
from typing import Dict, Any, List
from main import CNPJGoogleDriveStreamConnector

class CNPJMCPServer:
    """Servidor MCP para consulta de CNPJs via Google Drive"""
    
    def __init__(self):
        self.connector = CNPJGoogleDriveStreamConnector()
        self.initialized = False
    
    async def initialize(self):
        """Inicializa conexão com Google Drive"""
        if not self.initialized:
            try:
                await self.connector.initialize_drive_connection()
                await self.connector.find_cnpj_database()
                self.initialized = True
                return True
            except Exception as e:
                print(f"Erro na inicialização: {e}", file=sys.stderr)
                return False
        return True
    
    def get_tools_manifest(self) -> Dict[str, Any]:
        """Retorna manifesto de ferramentas MCP"""
        return {
            "version": "1.0.0",
            "mcpVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "tools": [
                {
                    "name": "query_cnpj",
                    "description": "Consulta dados completos de CNPJ na base real via Google Drive",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "cnpj": {
                                "type": "string",
                                "description": "CNPJ para consulta (14 dígitos, com ou sem formatação)",
                                "pattern": "^[0-9]{14}$|^[0-9]{2}\\.[0-9]{3}\\.[0-9]{3}/[0-9]{4}-[0-9]{2}$"
                            }
                        },
                        "required": ["cnpj"],
                        "additionalProperties": false
                    }
                },
                {
                    "name": "search_by_name",
                    "description": "Busca empresas por nome ou razão social na base real",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "nome": {
                                "type": "string",
                                "description": "Nome completo ou parte do nome da empresa",
                                "minLength": 3
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Número máximo de resultados (1-50)",
                                "minimum": 1,
                                "maximum": 50,
                                "default": 10
                            }
                        },
                        "required": ["nome"],
                        "additionalProperties": false
                    }
                },
                {
                    "name": "get_statistics",
                    "description": "Retorna estatísticas gerais da base de dados de CNPJs",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": false
                    }
                }
            ]
        }
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executa ferramenta MCP"""
        try:
            # Inicializar se necessário
            if not await self.initialize():
                return {
                    "success": False,
                    "error": "Falha na inicialização",
                    "message": "Não foi possível conectar ao Google Drive"
                }
            
            # Executar ferramenta
            if name == "query_cnpj":
                cnpj = arguments.get("cnpj")
                if not cnpj:
                    return {
                        "success": False,
                        "error": "CNPJ obrigatório",
                        "message": "Parâmetro 'cnpj' é obrigatório"
                    }
                return await self.connector.query_cnpj(cnpj)
            
            elif name == "search_by_name":
                nome = arguments.get("nome")
                limit = arguments.get("limit", 10)
                
                if not nome:
                    return {
                        "success": False,
                        "error": "Nome obrigatório",
                        "message": "Parâmetro 'nome' é obrigatório"
                    }
                
                return await self.connector.search_by_name(nome, limit)
            
            elif name == "get_statistics":
                return await self.connector.get_statistics()
            
            else:
                return {
                    "success": False,
                    "error": "Ferramenta não encontrada",
                    "message": f"A ferramenta '{name}' não está disponível"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": "Erro interno",
                "message": str(e)
            }

async def main():
    """Função principal para modo MCP"""
    server = CNPJMCPServer()
    
    # Verificar modo de execução
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--list-tools":
            # Retornar lista de ferramentas
            manifest = server.get_tools_manifest()
            print(json.dumps(manifest, indent=2, ensure_ascii=False))
            
        elif command == "--call-tool" and len(sys.argv) >= 4:
            # Executar ferramenta
            tool_name = sys.argv[2]
            try:
                arguments = json.loads(sys.argv[3])
                result = await server.call_tool(tool_name, arguments)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print(json.dumps({
                    "success": False,
                    "error": "JSON inválido",
                    "message": "Argumentos devem estar em formato JSON válido"
                }, indent=2))
        
        elif command == "--test":
            # Modo de teste
            print("🧪 Testando servidor MCP...")
            
            # Testar inicialização
            if await server.initialize():
                print("✅ Inicialização: OK")
                
                # Testar consulta
                test_result = await server.call_tool("query_cnpj", {"cnpj": "01784792000103"})
                print("📋 Resultado do teste:")
                print(json.dumps(test_result, indent=2, ensure_ascii=False))
            else:
                print("❌ Falha na inicialização")
        
        else:
            print("Uso: python mcp_server.py [--list-tools|--call-tool <nome> <args>|--test]")
    
    else:
        # Modo servidor MCP ativo
        manifest = server.get_tools_manifest()
        print(json.dumps(manifest, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())