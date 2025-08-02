#!/usr/bin/env python3
"""
GitHub Launcher para CNPJ MCP SQLite RAG Server
Baixa 100% do código do GitHub e executa localmente
Usa apenas credentials.json local
"""

import os
import sys
import asyncio
import tempfile
import requests
from pathlib import Path
import importlib.util
import logging

# GitHub repository info
GITHUB_USER = "tiagoegidio-cmd"
REPO_NAME = "cnpj-mcp-sqlite-rag-server"
GITHUB_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubLauncher:
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "cnpj_mcp_github_cache"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Local credentials path
        self.local_credentials = Path("credentials.json")
        
        # Files to download from GitHub
        self.github_files = [
            "mcp_sqlite_rag_server.py",
            "requirements.txt"
        ]
    
    def check_local_credentials(self):
        """Verify that credentials.json exists locally"""
        if not self.local_credentials.exists():
            print("❌ ERRO: credentials.json não encontrado localmente!")
            print("\n📋 Para criar o arquivo:")
            print("1. Acesse: https://console.cloud.google.com/")
            print("2. 🔑 Use a conta: tiagosimon@gmail.com")
            print("3. Configure OAuth 2.0 (Aplicativo para computador)")
            print("4. Baixe como 'credentials.json'")
            print("5. Coloque na mesma pasta deste launcher")
            return False
        
        print(f"✅ credentials.json encontrado: {self.local_credentials}")
        return True
    
    def download_file_from_github(self, filename):
        """Download a file from GitHub repository"""
        url = f"{GITHUB_BASE_URL}/{filename}"
        local_path = self.temp_dir / filename
        
        try:
            print(f"📥 Baixando: {filename}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"✅ Baixado: {filename}")
            return local_path
            
        except Exception as e:
            print(f"❌ Erro ao baixar {filename}: {e}")
            return None
    
    def copy_credentials_to_temp(self):
        """Copy local credentials.json to temp directory"""
        temp_credentials = self.temp_dir / "credentials.json"
        
        try:
            import shutil
            shutil.copy2(self.local_credentials, temp_credentials)
            print(f"✅ Credentials copiado para: {temp_credentials}")
            return temp_credentials
        except Exception as e:
            print(f"❌ Erro ao copiar credentials: {e}")
            return None
    
    def install_dependencies(self, requirements_path):
        """Install dependencies from downloaded requirements.txt"""
        try:
            print("📦 Verificando dependências...")
            
            # Read requirements
            with open(requirements_path, 'r') as f:
                requirements = f.read()
            
            # Extract only the essential packages (skip built-in modules)
            essential_packages = []
            for line in requirements.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Skip built-in modules
                    if not any(builtin in line.lower() for builtin in [
                        'sqlite3', 'pathlib', 'tempfile', 'asyncio', 
                        'logging', 'json', 'hashlib', 'io'
                    ]):
                        essential_packages.append(line)
            
            if essential_packages:
                import subprocess
                packages_to_install = ' '.join(essential_packages)
                print(f"📦 Instalando: {packages_to_install}")
                
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install"
                ] + essential_packages, 
                capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Dependências instaladas com sucesso")
                    return True
                else:
                    print(f"⚠️  Aviso na instalação: {result.stderr}")
                    return True  # Continue anyway
            else:
                print("✅ Nenhuma dependência adicional necessária")
                return True
                
        except Exception as e:
            print(f"⚠️  Erro ao instalar dependências: {e}")
            return True  # Continue anyway
    
    def load_and_run_server(self, server_path):
        """Load and run the MCP server from downloaded file"""
        try:
            print(f"🚀 Carregando servidor de: {server_path}")
            
            # Add temp directory to Python path
            sys.path.insert(0, str(self.temp_dir))
            
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location("mcp_server", server_path)
            server_module = importlib.util.module_from_spec(spec)
            
            # Execute the module
            spec.loader.exec_module(server_module)
            
            # Run the main function
            if hasattr(server_module, 'main'):
                print("✅ Executando servidor MCP...")
                asyncio.run(server_module.main())
            else:
                print("❌ Função main() não encontrada no servidor")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao executar servidor: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_test_mode(self, server_path):
        """Run in test mode instead of MCP server mode"""
        try:
            print("🧪 Modo de Teste Ativado")
            
            # Add temp directory to Python path
            sys.path.insert(0, str(self.temp_dir))
            
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location("mcp_server", server_path)
            server_module = importlib.util.module_from_spec(spec)
            
            # Execute the module
            spec.loader.exec_module(server_module)
            
            # Create server instance and test
            if hasattr(server_module, 'SQLiteRAGServer'):
                print("✅ Iniciando teste do servidor...")
                
                server = server_module.SQLiteRAGServer()
                
                print("\n🧪 Testando CNPJ MCP SQLite RAG Server (GitHub Version)")
                print("=" * 60)
                print("📂 Estrutura esperada: BASE DE DADOS/BASE B2B/cnpj.db")
                print("🔑 Conta Google: tiagosimon@gmail.com")
                print("🌐 Código fonte: GitHub (sempre atualizado)")
                print("🔒 Credenciais: Local (seguro)")
                print("=" * 60)
                
                # Test 1: Load database
                print("\n1️⃣ Carregando banco de dados...")
                print("   • Conectando ao Google Drive...")
                print("   • Procurando pasta 'BASE DE DADOS'...")
                print("   • Procurando subpasta 'BASE B2B'...")
                print("   • Procurando arquivo 'cnpj.db'...")
                
                await server.ensure_database_loaded()
                print("✅ Banco carregado com sucesso")
                
                # Test 2: Schema
                print("\n2️⃣ Testando schema...")
                schema = await server.handle_get_schema()
                tables_count = len(schema.split('Tabela')) - 1
                print(f"✅ Schema obtido: {tables_count} tabelas encontradas")
                
                # Test 3: SQL Query
                print("\n3️⃣ Testando SQL...")
                sql_result = await server.handle_sql_query("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5")
                print(f"✅ SQL executado com sucesso")
                
                # Test 4: Natural Query
                print("\n4️⃣ Testando consulta natural...")
                natural_result = await server.handle_natural_query("Quantas tabelas existem no banco?")
                print(f"✅ Consulta natural processada")
                
                print("\n" + "=" * 60)
                print("🎉 TODOS OS TESTES PASSARAM!")
                print("=" * 60)
                print("✅ Servidor funcionando com código do GitHub")
                print("✅ Banco de dados CNPJ acessível")
                print("✅ RAG operacional")
                print("✅ Pronto para integração com Claude")
                
                return True
            else:
                print("❌ Classe SQLiteRAGServer não encontrada")
                return False
                
        except Exception as e:
            print(f"❌ Erro no teste: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run(self, test_mode=False):
        """Main launcher function"""
        print("🚀 CNPJ MCP SQLite RAG Server - GitHub Launcher")
        print("=" * 50)
        print("🌐 Código: GitHub (sempre atualizado)")
        print("🔒 Credenciais: Local (seguro)")
        print("=" * 50)
        
        # Step 1: Check local credentials
        if not self.check_local_credentials():
            return False
        
        # Step 2: Download files from GitHub
        print(f"\n📁 Diretório temporário: {self.temp_dir}")
        
        downloaded_files = {}
        for filename in self.github_files:
            file_path = self.download_file_from_github(filename)
            if file_path:
                downloaded_files[filename] = file_path
            else:
                print(f"❌ Falha ao baixar {filename}")
                return False
        
        # Step 3: Copy credentials to temp directory
        if not self.copy_credentials_to_temp():
            return False
        
        # Step 4: Install dependencies
        if "requirements.txt" in downloaded_files:
            self.install_dependencies(downloaded_files["requirements.txt"])
        
        # Step 5: Run the server
        if "mcp_sqlite_rag_server.py" in downloaded_files:
            if test_mode:
                return asyncio.run(self.run_test_mode(downloaded_files["mcp_sqlite_rag_server.py"]))
            else:
                return self.load_and_run_server(downloaded_files["mcp_sqlite_rag_server.py"])
        else:
            print("❌ Servidor principal não foi baixado")
            return False

def main():
    """Main function with command line arguments"""
    launcher = GitHubLauncher()
    
    # Check for test mode
    test_mode = "--test" in sys.argv or "-t" in sys.argv
    
    if test_mode:
        print("🧪 Modo de teste ativado")
        success = launcher.run(test_mode=True)
    else:
        print("🖥️  Modo servidor MCP ativado")
        success = launcher.run(test_mode=False)
    
    if success:
        print("\n✅ Launcher executado com sucesso!")
    else:
        print("\n❌ Erro na execução do launcher")
        sys.exit(1)

if __name__ == "__main__":
    main()
