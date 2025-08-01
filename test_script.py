#!/usr/bin/env python3
"""
Script de teste para o CNPJ MCP SQLite RAG Server
Execute para testar as funcionalidades localmente
"""

import asyncio
import json
import logging
from mcp_sqlite_rag_server import SQLiteRAGServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_server():
    """Testa as funcionalidades do servidor"""
    print("🧪 Testando CNPJ MCP SQLite RAG Server")
    print("=" * 40)
    
    # Inicializar servidor
    server = SQLiteRAGServer()
    
    try:
        # Test 1: Ensure database is loaded
        print("\n1️⃣ Carregando banco de dados...")
        await server.ensure_database_loaded()
        print("✅ Banco carregado com sucesso")
        
        # Test 2: Get schema
        print("\n2️⃣ Testando get_schema...")
        schema_result = await server.handle_get_schema()
        print(f"Schema: {schema_result[:200]}...")
        
        # Test 3: SQL query
        print("\n3️⃣ Testando consulta SQL...")
        sql_result = await server.handle_sql_query("SELECT name FROM sqlite_master WHERE type='table'")
        print(f"Tabelas: {sql_result}")
        
        # Test 4: Natural query
        print("\n4️⃣ Testando consulta natural...")
        natural_result = await server.handle_natural_query("Mostre todas as tabelas")
        print(f"Resultado natural: {natural_result[:200]}...")
        
        # Test 5: Semantic search
        print("\n5️⃣ Testando busca semântica...")
        semantic_result = await server.handle_semantic_search("tabela dados", 3)
        print(f"Busca semântica: {semantic_result[:200]}...")
        
        print("\n✅ Todos os testes passaram!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        logger.error(f"Erro detalhado: {e}", exc_info=True)

async def interactive_test():
    """Teste interativo"""
    print("\n🎮 Modo Interativo")
    print("Digite 'quit' para sair")
    print("Comandos disponíveis:")
    print("- sql: <query>     - Executa SQL")
    print("- natural: <query> - Consulta natural") 
    print("- schema           - Mostra estrutura")
    print("- search: <term>   - Busca semântica")
    
    server = SQLiteRAGServer()
    await server.ensure_database_loaded()
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'schema':
                result = await server.handle_get_schema()
                print(f"\n{result}")
            elif user_input.startswith('sql:'):
                query = user_input[4:].strip()
                result = await server.handle_sql_query(query)
                print(f"\n{result}")
            elif user_input.startswith('natural:'):
                query = user_input[8:].strip()
                result = await server.handle_natural_query(query)
                print(f"\n{result}")
            elif user_input.startswith('search:'):
                query = user_input[7:].strip()
                result = await server.handle_semantic_search(query, 5)
                print(f"\n{result}")
            else:
                print("Comando não reconhecido. Use: sql:, natural:, schema, search: ou quit")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Erro: {e}")
    
    print("👋 Teste interativo encerrado")

def main():
    """Função principal"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        asyncio.run(interactive_test())
    else:
        asyncio.run(test_server())

if __name__ == "__main__":
    main()
