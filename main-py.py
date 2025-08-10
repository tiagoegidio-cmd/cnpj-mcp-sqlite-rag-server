#!/usr/bin/env python3
"""
CNPJ Consulta System - Script Principal
Versão Simplificada sem Claude Desktop
"""

import sqlite3
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional
import argparse

class CNPJDatabase:
    """Gerenciador do banco de dados CNPJ local"""
    
    def __init__(self, db_path: str = "data/cnpj.db"):
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        """Inicializa banco de dados se não existir"""
        self.db_path.parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Criar tabela principal
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS empresas (
                cnpj TEXT PRIMARY KEY,
                razao_social TEXT,
                nome_fantasia TEXT,
                situacao_cadastral TEXT,
                data_situacao_cadastral TEXT,
                tipo_logradouro TEXT,
                logradouro TEXT,
                numero TEXT,
                complemento TEXT,
                bairro TEXT,
                cep TEXT,
                municipio TEXT,
                uf TEXT,
                cnae_principal TEXT,
                cnae_descricao TEXT,
                natureza_juridica TEXT,
                porte_empresa TEXT,
                capital_social REAL,
                data_inicio_atividade TEXT,
                opcao_simples TEXT,
                data_opcao_simples TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Inserir dados de exemplo se tabela vazia
        cursor.execute("SELECT COUNT(*) FROM empresas")
        if cursor.fetchone()[0] == 0:
            self.insert_sample_data(cursor)
        
        conn.commit()
        conn.close()
        print(f"✅ Banco de dados inicializado: {self.db_path}")
    
    def insert_sample_data(self, cursor):
        """Insere dados de exemplo"""
        sample_data = [
            (
                '43227497000198',
                'N9 PARTICIPACOES SOCIEDADE SIMPLES',
                '',
                'ATIVA',
                '2019-08-01',
                'RUA',
                'TABAPUA',
                '1123',
                '',
                'ITAIM BIBI',
                '04533004',
                'SAO PAULO',
                'SP',
                '7020400',
                'ATIVIDADES DE CONSULTORIA EM GESTAO EMPRESARIAL',
                '213-5 - SOCIEDADE SIMPLES',
                'DEMAIS',
                1000000.00,
                '2019-08-01',
                'NAO',
                ''
            ),
            (
                '11222333000144',
                'EMPRESA EXEMPLO TECNOLOGIA LTDA',
                'EXEMPLO TECH',
                'ATIVA',
                '2020-01-15',
                'AVENIDA',
                'PAULISTA',
                '1000',
                'CONJUNTO 10',
                'BELA VISTA',
                '01310100',
                'SAO PAULO',
                'SP',
                '6201500',
                'DESENVOLVIMENTO DE PROGRAMAS DE COMPUTADOR SOB ENCOMENDA',
                '206-2 - SOCIEDADE EMPRESARIA LIMITADA',
                'ME',
                50000.00,
                '2020-01-15',
                'SIM',
                '2020-02-01'
            )
        ]
        
        cursor.executemany('''
            INSERT INTO empresas VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', sample_data)
        
        print("📊 Dados de exemplo inseridos")

class CNPJConsulta:
    """Sistema de consulta CNPJ"""
    
    def __init__(self, db_path: str = "data/cnpj.db"):
        self.db = CNPJDatabase(db_path)
    
    def consultar_cnpj(self, cnpj: str) -> Optional[Dict]:
        """Consulta CNPJ no banco local"""
        # Limpar CNPJ
        cnpj_clean = ''.join(filter(str.isdigit, cnpj))
        
        if len(cnpj_clean) != 14:
            return {"erro": "CNPJ deve ter 14 dígitos"}
        
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM empresas WHERE cnpj = ?", (cnpj_clean,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return dict(result)
        else:
            # Tentar consulta externa se não encontrar
            return self.consultar_receita_federal(cnpj_clean)
    
    def consultar_receita_federal(self, cnpj: str) -> Dict:
        """Consulta API externa da Receita Federal (simulada)"""
        # Em um sistema real, aqui faria chamada para API oficial
        return {
            "erro": "CNPJ não encontrado na base local",
            "sugestao": "Use um dos CNPJs de exemplo: 43227497000198 ou 11222333000144"
        }
    
    def listar_empresas(self, limite: int = 10) -> List[Dict]:
        """Lista empresas cadastradas"""
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM empresas LIMIT ?", (limite,))
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def buscar_por_nome(self, nome: str) -> List[Dict]:
        """Busca empresas por nome"""
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM empresas 
            WHERE razao_social LIKE ? OR nome_fantasia LIKE ?
        ''', (f'%{nome}%', f'%{nome}%'))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def estatisticas(self) -> Dict:
        """Estatísticas do banco"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total empresas
        cursor.execute("SELECT COUNT(*) FROM empresas")
        stats['total_empresas'] = cursor.fetchone()[0]
        
        # Por situação
        cursor.execute('''
            SELECT situacao_cadastral, COUNT(*) 
            FROM empresas 
            GROUP BY situacao_cadastral
        ''')
        stats['por_situacao'] = dict(cursor.fetchall())
        
        # Por UF
        cursor.execute('''
            SELECT uf, COUNT(*) 
            FROM empresas 
            GROUP BY uf 
            ORDER BY COUNT(*) DESC 
            LIMIT 5
        ''')
        stats['top_ufs'] = dict(cursor.fetchall())
        
        conn.close()
        return stats

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Sistema de Consulta CNPJ')
    parser.add_argument('--cnpj', help='CNPJ para consultar')
    parser.add_argument('--nome', help='Buscar por nome da empresa')
    parser.add_argument('--listar', action='store_true', help='Listar empresas')
    parser.add_argument('--stats', action='store_true', help='Mostrar estatísticas')
    parser.add_argument('--web', action='store_true', help='Iniciar interface web')
    
    args = parser.parse_args()
    
    consulta = CNPJConsulta()
    
    print("🏢 Sistema de Consulta CNPJ")
    print("=" * 40)
    
    if args.web:
        print("🌐 Iniciando interface web...")
        from web_interface import app
        app.run(debug=True, port=5000)
    
    elif args.cnpj:
        print(f"🔍 Consultando CNPJ: {args.cnpj}")
        result = consulta.consultar_cnpj(args.cnpj)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.nome:
        print(f"🔍 Buscando empresas com nome: {args.nome}")
        results = consulta.buscar_por_nome(args.nome)
        print(f"📊 Encontradas {len(results)} empresa(s)")
        for empresa in results:
            print(f"  • {empresa['razao_social']} (CNPJ: {empresa['cnpj']})")
    
    elif args.listar:
        print("📋 Listando empresas cadastradas:")
        empresas = consulta.listar_empresas()
        for empresa in empresas:
            print(f"  • {empresa['razao_social']} (CNPJ: {empresa['cnpj']})")
    
    elif args.stats:
        print("📊 Estatísticas do banco:")
        stats = consulta.estatisticas()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    else:
        print("💡 Exemplos de uso:")
        print("  python main.py --cnpj 43227497000198")
        print("  python main.py --nome 'N9 PARTICIPACOES'")
        print("  python main.py --listar")
        print("  python main.py --stats")
        print("  python main.py --web")
        print("\n🌐 Para interface web: python main.py --web")

if __name__ == "__main__":
    main()
