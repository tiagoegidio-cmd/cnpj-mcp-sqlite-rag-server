#!/usr/bin/env python3
"""
Instalador Ultra-Simples do CNPJ MCP SQLite RAG Server
Baixa apenas o launcher do GitHub + usa credentials.json local
"""

import os
import sys
import requests
from pathlib import Path

def download_launcher():
    """Download the GitHub launcher"""
    launcher_url = "https://raw.githubusercontent.com/tiagoegidio-cmd/cnpj-mcp-sqlite-rag-server/main/run_from_github.py"
    
    try:
        print("📥 Baixando launcher do GitHub...")
        response = requests.get(launcher_url, timeout=30)
        response.raise_for_status()
        
        with open("run_from_github.py", 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print("✅ Launcher baixado: run_from_github.py")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao baixar launcher: {e}")
        return False

def check_python():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ é necessário")
        return False
    print(f"✅ Python {sys.version.split()[0]} OK")
    return True

def install_requests():
    """Install requests if not available"""
    try:
        import requests
        print("✅ requests já instalado")
        return True
    except ImportError:
        print("📦 Instalando requests...")
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pip", "install", "requests"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ requests instalado")
            return True
        else:
            print(f"❌ Erro ao instalar requests: {result.stderr}")
            return False

def check_credentials():
    """Check for credentials.json"""
    if Path("credentials.json").exists():
        print("✅ credentials.json encontrado")
        return True
    else:
        print("⚠️  credentials.json não encontrado")
        print("\n📋 Para criar:")
        print("1. Acesse: https://console.cloud.google.com/")
        print("2. Use conta: tiagosimon@gmail.com")
        print("3. OAuth 2.0 → Aplicativo para computador") 
        print("4. Baixe como 'credentials.json'")
        print("5. Coloque na mesma pasta deste instalador")
        return False

def create_claude_config():
    """Create Claude Desktop configuration"""
    current_path = Path.cwd().absolute()
    launcher_path = current_path / "run_from_github.py"
    
    config = {
        "mcpServers": {
            "cnpj-sqlite-rag-server": {
                "command": "python",
                "args": [str(launcher_path)],
                "env": {
                    "PYTHONPATH": str(current_path)
                }
            }
        }
    }
    
    import json
    with open("claude_desktop_config.json", 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Configuração criada: claude_desktop_config.json")
    
    # Show instructions for different OS
    if sys.platform == "win32":
        config_path = "%APPDATA%\\Claude\\claude_desktop_config.json"
    elif sys.platform == "darwin":
        config_path = "~/Library/Application Support/Claude/claude_desktop_config.json"
    else:
        config_path = "~/.config/claude/claude_desktop_config.json"
    
    print(f"\n📋 Copie o conteúdo para: {config_path}")
    return True

def main():
    """Main installer"""
    print("🚀 CNPJ MCP SQLite RAG Server - Instalador Ultra-Simples")
    print("=" * 60)
    print("🌐 Código: Sempre do GitHub (auto-atualizado)")
    print("🔒 Dados: Local (credentials.json apenas)")
    print("=" * 60)
    
    # Check Python
    if not check_python():
        return False
    
    # Install requests
    if not install_requests():
        return False
    
    # Download launcher
    if not download_launcher():
        return False
    
    # Check credentials
    has_credentials = check_credentials()
    
    # Create Claude config
    create_claude_config()
    
    print("\n" + "=" * 60)
    print("🎉 INSTALAÇÃO CONCLUÍDA!")
    print("=" * 60)
    
    print("\n📁 Arquivos criados:")
    print("   ✅ run_from_github.py (launcher)")
    print("   ✅ claude_desktop_config.json (configuração)")
    
    if has_credentials:
        print("   ✅ credentials.json (já existia)")
    else:
        print("   ❌ credentials.json (VOCÊ DEVE CRIAR)")
    
    print("\n🧪 Teste o sistema:")
    print("   python run_from_github.py --test")
    
    print("\n🔧 Configure Claude Desktop:")
    print("   Copie o conteúdo de claude_desktop_config.json")
    print("   Para o arquivo de configuração do Claude")
    
    if not has_credentials:
        print("\n⚠️  IMPORTANTE: Crie credentials.json antes de testar!")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
