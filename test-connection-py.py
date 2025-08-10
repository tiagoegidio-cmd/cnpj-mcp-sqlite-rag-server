#!/usr/bin/env python3
"""
Test Connection - Sistema CNPJ Google Drive
Testa conexão e funcionalidades do sistema
Para uso com Claude Projetos
"""

import sys
import json
import traceback
from datetime import datetime
from pathlib import Path

def test_imports():
    """Testa se todos os módulos podem ser importados"""
    print("🔍 TESTANDO IMPORTS...")
    
    try:
        from google_drive_connector import GoogleDriveCNPJConnector
        print("   ✅ google_drive_connector importado")
    except ImportError as e:
        print(f"   ❌ Erro ao importar google_drive_connector: {e}")
        return False
    
    try:
        from cnpj_query_engine import CNPJQueryEngine, consultar_cnpj_para_claude
        print("   ✅ cnpj_query_engine importado")
    except ImportError as e:
        print(f"   ❌ Erro ao importar cnpj_query_engine: {e}")
        return False
    
    print("   🎉 Todos os imports OK!")
    return True

def test_credentials():
    """Verifica se credenciais estão configuradas"""
    print("\n🔑 TESTANDO CREDENCIAIS...")
    
    credentials_files = [
        "credentials.json",
        "service-account-key.json", 
        "google-credentials.json"
    ]
    
    found_credentials = False
    
    for cred_file in credentials_files:
        if Path(cred_file).exists():
            print(f"   ✅ Arquivo encontrado: {cred_file}")
            
            try:
                with open(cred_file, 'r') as f:
                    creds = json.load(f)
                
                # Verificar estrutura básica
                required_fields = ["type", "project_id", "client_email"]
                missing_fields = [field for field in required_fields if field not in creds]
                
                if missing_fields:
                    print(f"   ⚠️  Campos faltando: {missing_fields}")
                else:
                    print(f"   ✅ Estrutura válida")
                    print(f"   📧 Service Account: {creds.get('client_email', 'N/A')}")
                    print(f"   🎯 Projeto: {creds.get('project_id', 'N/A')}")
                    found_credentials = True
                    
            except json.JSONDecodeError:
                print(f"   ❌ Arquivo {cred_file} não é um JSON válido")
            except Exception as e:
                print(f"   ❌ Erro ao ler {cred_file}: {e}")
        else:
            print(f"   ⚪ {cred_file} não encontrado")
    
    if not found_credentials:
        print("   ⚠️  ATENÇÃO: Nenhuma credencial válida encontrada!")
        print("   📝 Copie suas credenciais para 'credentials.json'")
        return False
    
    return True

def test_google_drive_connection():
    """Testa conexão com Google Drive"""
    print("\n🌐 TESTANDO CONEXÃO GOOGLE DRIVE...")
    
    try:
        from google_drive_connector import GoogleDriveCNPJConnector
        
        connector = GoogleDriveCNPJConnector()
        print("   🔄 Inicializando conector...")
        
        # Testar conexão
        status = connector.test_connection()
        
        if status["connected"]:
            print("   ✅ Conexão estabelecida com sucesso!")
            print(f"   📁 Arquivos encontrados: {status['files_found']}")
            print(f"   📊 Fonte primária: {status.get('primary_source_available', 'N/A')}")
            print(f"   🎯 Fonte recomendada: {status.get('recommended_source', 'N/A')}")
            print(f"   🕒 Última atualização: {status.get('last_updated', 'N/A')}")
            return True
        else:
            print("   ❌ Falha na conexão!")
            print(f"   💬 Erro: {status.get('error', 'Erro desconhecido')}")
            print(f"   📝 Mensagem: {status.get('message', '')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro inesperado: {e}")
        print("   🔍 Detalhes do erro:")
        traceback.print_exc()
        return False

def test_data_sources():
    """Testa fontes de dados disponíveis"""
    print("\n📂 TESTANDO FONTES DE DADOS...")
    
    try:
        from google_drive_connector import GoogleDriveCNPJConnector
        
        connector = GoogleDriveCNPJConnector()
        sources = connector.get_available_data_sources()
        
        print(f"   📊 Total de arquivos: {sources['total_files']}")
        
        if sources["primary_source"]:
            primary = sources["primary_source"]
            print(f"   🎯 Fonte primária: {primary['name']}")
            print(f"   📏 Tamanho: {primary['size_mb']} MB")
            print(f"   📅 Modificado: {primary['modified']}")
        else:
            print("   ⚠️  Nenhuma fonte primária encontrada")
        
        if sources["backup_sources"]:
            print(f"   🔄 Fontes backup: {len(sources['backup_sources'])}")
            for i, backup in enumerate(sources["backup_sources"][:3]):  # Mostrar até 3
                print(f"     {i+1}. {backup['name']} ({backup['size_mb']} MB)")
        
        print(f"   💡 Fonte recomendada: {sources['recommended_source']}")
        
        return len(sources["backup_sources"]) > 0 or sources["primary_source"] is not None
        
    except Exception as e:
        print(f"   ❌ Erro ao verificar fontes: {e}")
        return False

def test_cnpj_query():
    """Testa consulta CNPJ"""
    print("\n🔍 TESTANDO CONSULTA CNPJ...")
    
    try:
        from cnpj_query_engine import CNPJQueryEngine
        
        engine = CNPJQueryEngine()
        print("   🔄 Inicializando motor de consulta...")
        
        # Testar CNPJs de exemplo
        test_cnpjs = ["43227497000198", "11222333000144"]
        
        for cnpj in test_cnpjs:
            print(f"\n   🔍 Testando CNPJ: {cnpj}")
            
            resultado = engine.query_cnpj(cnpj)
            
            if "error" in resultado:
                print(f"   ⚠️  {resultado['error']}: {resultado.get('message', '')}")
                if "não encontrado" in resultado["error"]:
                    print("   💡 Este é esperado se o CNPJ não estiver na base")
            else:
                print("   ✅ Consulta bem-sucedida!")
                dados = resultado["dados_cadastrais"]
                print(f"   🏢 Empresa: {dados['razao_social']}")
                print(f"   📊 Situação: {dados['situacao_cadastral']}")
                print(f"   📍 UF: {resultado['endereco']['uf']}")
                return True
        
        return False
        
    except Exception as e:
        print(f"   ❌ Erro na consulta: {e}")
        traceback.print_exc()
        return False

def test_search_functionality():
    """Testa funcionalidade de busca"""
    print("\n🔎 TESTANDO BUSCA POR NOME...")
    
    try:
        from cnpj_query_engine import CNPJQueryEngine
        
        engine = CNPJQueryEngine()
        
        # Testar busca
        termos_busca = ["N9", "EXEMPLO", "TECNOLOGIA"]
        
        for termo in termos_busca:
            print(f"\n   🔍 Buscando: '{termo}'")
            
            resultados = engine.search_by_name(termo, limit=3)
            
            if resultados:
                print(f"   ✅ {len(resultados)} resultado(s) encontrado(s)")
                for i, empresa in enumerate(resultados[:2]):  # Mostrar até 2
                    print(f"     {i+1}. {empresa['razao_social']} ({empresa['cnpj_formatted']})")
                return True
            else:
                print(f"   ⚪ Nenhum resultado para '{termo}'")
        
        return False
        
    except Exception as e:
        print(f"   ❌ Erro na busca: {e}")
        return False

def test_statistics():
    """Testa geração de estatísticas"""
    print("\n📊 TESTANDO ESTATÍSTICAS...")
    
    try:
        from cnpj_query_engine import CNPJQueryEngine
        
        engine = CNPJQueryEngine()
        stats = engine.get_statistics()
        
        if "error" in stats:
            print(f"   ❌ Erro: {stats['error']}")
            return False
        
        print("   ✅ Estatísticas geradas com sucesso!")
        print(f"   📈 Total de empresas: {stats.get('total_empresas', 'N/A')}")
        
        if "por_situacao_cadastral" in stats:
            print(f"   📊 Por situação: {stats['por_situacao_cadastral']}")
        
        if "por_uf" in stats:
            top_ufs = list(stats['por_uf'].items())[:3]
            print(f"   🗺️  Top 3 UFs: {dict(top_ufs)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro nas estatísticas: {e}")
        return False

def test_claude_integration():
    """Testa função de integração com Claude"""
    print("\n🤖 TESTANDO INTEGRAÇÃO CLAUDE...")
    
    try:
        from cnpj_query_engine import consultar_cnpj_para_claude
        
        cnpj_teste = "43227497000198"
        print(f"   🔍 Testando consulta Claude para: {cnpj_teste}")
        
        resultado = consultar_cnpj_para_claude(cnpj_teste)
        
        # Verificar se retornou uma string formatada
        if isinstance(resultado, str) and len(resultado) > 50:
            print("   ✅ Função Claude funcionando!")
            print("   📝 Exemplo de resposta:")
            # Mostrar primeiras 3 linhas da resposta
            linhas = resultado.split('\n')[:3]
            for linha in linhas:
                if linha.strip():
                    print(f"     {linha}")
            print("     ...")
            return True
        else:
            print(f"   ⚠️  Resposta inesperada: {resultado[:100]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro na integração Claude: {e}")
        return False

def run_complete_test():
    """Executa bateria completa de testes"""
    print("🧪 TESTE COMPLETO DO SISTEMA CNPJ")
    print("=" * 50)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Lista de testes
    tests = [
        ("Imports", test_imports),
        ("Credenciais", test_credentials),
        ("Conexão Google Drive", test_google_drive_connection),
        ("Fontes de Dados", test_data_sources),
        ("Consulta CNPJ", test_cnpj_query),
        ("Busca por Nome", test_search_functionality),
        ("Estatísticas", test_statistics),
        ("Integração Claude", test_claude_integration)
    ]
    
    # Executar testes
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ FALHA CRÍTICA em {test_name}: {e}")
            results[test_name] = False
    
    # Relatório final
    print("\n" + "=" * 50)
    print("📋 RELATÓRIO FINAL")
    print("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"📊 RESULTADO: {passed}/{total} testes passaram")
    print(f"📈 Taxa de sucesso: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("🚀 Sistema pronto para uso com Claude Projetos!")
        print("\n💡 Próximos passos:")
        print("   1. Adicionar repositório ao Claude Projetos")
        print("   2. Testar consultas reais via Claude")
        print("   3. Monitorar performance em produção")
    elif passed >= total * 0.7:  # 70% ou mais
        print("\n⚠️  SISTEMA PARCIALMENTE FUNCIONAL")
        print("🔧 Alguns componentes precisam de ajustes")
        print("💡 Revise os testes que falharam acima")
    else:
        print("\n❌ SISTEMA NÃO ESTÁ PRONTO")
        print("🛠️  Configure os componentes que falharam")
        print("📚 Consulte README_CLAUDE_PROJECTS.md para ajuda")
    
    print(f"\n⏰ Concluído em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total

def quick_test():
    """Teste rápido apenas dos componentes essenciais"""
    print("⚡ TESTE RÁPIDO")
    print("-" * 30)
    
    essential_tests = [
        test_imports,
        test_credentials,
        test_google_drive_connection
    ]
    
    for i, test in enumerate(essential_tests):
        try:
            if not test():
                print(f"\n❌ Teste {i+1} falhou - sistema não está pronto")
                return False
        except Exception as e:
            print(f"\n❌ Erro no teste {i+1}: {e}")
            return False
    
    print("\n✅ Testes essenciais passaram!")
    print("🚀 Sistema básico funcionando")
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Teste do Sistema CNPJ")
    parser.add_argument("--quick", action="store_true", help="Executar apenas testes essenciais")
    parser.add_argument("--component", choices=["imports", "credentials", "drive", "query", "search", "stats", "claude"], help="Testar componente específico")
    
    args = parser.parse_args()
    
    if args.quick:
        success = quick_test()
    elif args.component:
        # Testes individuais
        tests_map = {
            "imports": test_imports,
            "credentials": test_credentials,
            "drive": test_google_drive_connection,
            "query": test_cnpj_query,
            "search": test_search_functionality,
            "stats": test_statistics,
            "claude": test_claude_integration
        }
        
        if args.component in tests_map:
            success = tests_map[args.component]()
        else:
            print(f"❌ Componente '{args.component}' não encontrado")
            success = False
    else:
        success = run_complete_test()
    
    # Exit code para automação
    sys.exit(0 if success else 1)
