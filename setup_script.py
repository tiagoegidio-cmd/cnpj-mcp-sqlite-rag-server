#!/usr/bin/env python3
"""
Setup script para CNPJ MCP SQLite RAG Server
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def check_python_version():
    """Verifica versão do Python"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ é necessário")
        print(f"Versão atual: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} OK")

def install_dependencies():
    """Instala dependências"""
    print("📦 Instalando dependências...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependências instaladas")
    except subprocess.CalledProcessError:
        print("❌ Erro ao instalar dependências")
        sys.exit(1)

def check_credentials():
    """Verifica se credentials.json existe"""
    creds_path = Path("credentials.json")
    if not creds_path.exists():
        print("⚠️  credentials.json não encontrado")
        print("\n📋 Para criar o arquivo:")
        print("1. Acesse: https://console.cloud.google.com/")
        print("2. 🔑 IMPORTANTE: Use a conta tiagosimon@gmail.com")
        print("3. Configure Tela de Consentimento (Externo)")
        print("4. Ative a Google Drive API")
        print("5. Crie credenciais OAuth 2.0 (Aplicativo para computador)")
        print("6. Baixe como 'credentials.json'")
        print("7. 🚨 NUNCA commite este arquivo no GitHub!")
        print("8. Coloque na pasta do projeto")
        return False
    print("✅ credentials.json encontrado")
    print("🔒 Lembre-se: NUNCA commite credentials.json!")
    return True

def create_mcp_config():
    """Cria configuração exemplo para Claude Desktop"""
    current_dir = Path(__file__).parent.absolute()
    script_path = current_dir / "mcp_sqlite_rag_server.py"
    
    config = {
        "mcpServers": {
            "cnpj-sqlite-rag-server": {
                "command": "python",
                "args": [str(script_path)],
                "env": {
                    "PYTHONPATH": str(current_dir)
                }
            }
        }
    }
    
    config_path = Path("claude_desktop_config_example.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Configuração exemplo criada: {config_path}")
    return config

def show_instructions(config):
    """Mostra instruções finais"""
    print("\n" + "="*60)
    print("🎉 SETUP CONCLUÍDO!")
    print("="*60)
    
    print("\n📋 PRÓXIMOS PASSOS:")
    print("\n1. 🔑 Configure Google Drive API:")
    if not Path("credentials.json").exists():
        print("   - Coloque credentials.json na pasta do projeto")
    else:
        print("   ✅ credentials.json já configurado")
    
    print("\n2. 🔧 Configure Claude Desktop:")
    
    # Detectar OS
    if sys.platform == "darwin":  # macOS
        config_path = "~/Library/Application Support/Claude/claude_desktop_config.json"
    elif sys.platform == "win32":  # Windows
        config_path = "%APPDATA%\\Claude\\claude_desktop_config.json"
    else:  # Linux
        config_path = "~/.config/claude/claude_desktop_config.json"
    
    print(f"   - Edite: {config_path}")
    print("   - Adicione a configuração do arquivo: claude_desktop_config_example.json")
    
    print("\n3. 🚀 Como usar no Claude:")
    print("   - Reinicie Claude Desktop")
    print("   - Use as ferramentas:")
    print("     • natural_query: 'Quantos clientes temos?'")
    print("     • sql_query: 'SELECT * FROM tabela LIMIT 10'")
    print("     • get_schema: 'Mostra estrutura do banco'")
    print("     • semantic_search: 'Procure por vendas'")
    
    print("\n4. 🔐 Primeira execução:")
    print("   - Autorização Google será solicitada automaticamente")
    print("   - Login com: tiagosimon@gmail.com")
    
    print("\n📚 Documentação completa no README.md")
    print("🐛 Issues: https://github.com/tiagoegidio-cmd/cnpj-mcp-sqlite-rag-server/issues")

def main():
    """Função principal do setup"""
    print("🔧 CNPJ MCP SQLite RAG Server - Setup")
    print("=" * 40)
    
    # Verificações
    check_python_version()
    install_dependencies()
    has_creds = check_credentials()
    
    # Configuração
    config = create_mcp_config()
    
    # Instruções finais
    show_instructions(config)
    
    if not has_creds:
        print("\n⚠️  Lembre-se de adicionar credentials.json antes de usar!")

if __name__ == "__main__":
    main()
