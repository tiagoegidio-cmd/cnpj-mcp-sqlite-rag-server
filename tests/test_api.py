#!/usr/bin/env python3
"""
Testes unitários para o Sistema CNPJ
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
import sys

# Adicionar pasta pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import CNPJConsulta, CNPJDatabase
from web_interface import app

class TestCNPJDatabase:
    """Testes para o banco de dados"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_cnpj.db")
        self.db = CNPJDatabase(self.db_path)
    
    def test_database_creation(self):
        """Testa criação do banco"""
        assert Path(self.db_path).exists()
        
    def test_sample_data_inserted(self):
        """Testa se dados de exemplo foram inseridos"""
        consulta = CNPJConsulta(self.db_path)
        empresas = consulta.listar_empresas()
        assert len(empresas) >= 2
        
    def test_database_schema(self):
        """Testa estrutura do banco"""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar se tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='empresas'")
        result = cursor.fetchone()
        assert result is not None
        
        # Verificar colunas
        cursor.execute("PRAGMA table_info(empresas)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        required_columns = ['cnpj', 'razao_social', 'situacao_cadastral', 'municipio', 'uf']
        for col in required_columns:
            assert col in column_names
        
        conn.close()

class TestCNPJConsulta:
    """Testes para consultas CNPJ"""
    
    def setup_method(self):
        """Setup para cada teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_cnpj.db")
        self.consulta = CNPJConsulta(self.db_path)
    
    def test_consultar_cnpj_existente(self):
        """Testa consulta de CNPJ existente"""
        resultado = self.consulta.consultar_cnpj("43227497000198")
        
        assert "erro" not in resultado
        assert resultado["cnpj"] == "43227497000198"
        assert resultado["razao_social"] == "N9 PARTICIPACOES SOCIEDADE SIMPLES"
        assert resultado["situacao_cadastral"] == "ATIVA"
    
    def test_consultar_cnpj_inexistente(self):
        """Testa consulta de CNPJ inexistente"""
        resultado = self.consulta.consultar_cnpj("99999999999999")
        
        assert "erro" in resultado
        assert "não encontrado" in resultado["erro"]
    
    def test_consultar_cnpj_invalido(self):
        """Testa consulta com CNPJ inválido"""
        resultado = self.consulta.consultar_cnpj("123")
        
        assert "erro" in resultado
        assert "14 dígitos" in resultado["erro"]
    
    def test_listar_empresas(self):
        """Testa listagem de empresas"""
        empresas = self.consulta.listar_empresas()
        
        assert isinstance(empresas, list)
        assert len(empresas) >= 2
        
        # Verificar se primeiro resultado tem campos obrigatórios
        empresa = empresas[0]
        assert "cnpj" in empresa
        assert "razao_social" in empresa
        assert "situacao_cadastral" in empresa
    
    def test_buscar_por_nome(self):
        """Testa busca por nome"""
        resultados = self.consulta.buscar_por_nome("N9")
        
        assert isinstance(resultados, list)
        assert len(resultados) >= 1
        
        # Verificar se encontrou a empresa correta
        empresa = resultados[0]
        assert "N9" in empresa["razao_social"]
    
    def test_buscar_por_nome_inexistente(self):
        """Testa busca por nome inexistente"""
        resultados = self.consulta.buscar_por_nome("EMPRESA_INEXISTENTE_XYZ")
        
        assert isinstance(resultados, list)
        assert len(resultados) == 0
    
    def test_estatisticas(self):
        """Testa geração de estatísticas"""
        stats = self.consulta.estatisticas()
        
        assert isinstance(stats, dict)
        assert "total_empresas" in stats
        assert "por_situacao" in stats
        assert "top_ufs" in stats
        
        assert stats["total_empresas"] >= 2
        assert isinstance(stats["por_situacao"], dict)
        assert isinstance(stats["top_ufs"], dict)

class TestWebInterface:
    """Testes para interface web"""
    
    def setup_method(self):
        """Setup para cada teste"""
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_index_page(self):
        """Testa página inicial"""
        response = self.client.get('/')
        assert response.status_code == 200
        assert b'Sistema de Consulta CNPJ' in response.data
    
    def test_api_consultar_existente(self):
        """Testa API de consulta com CNPJ existente"""
        response = self.client.get('/api/consultar/43227497000198')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["cnpj"] == "43227497000198"
        assert "razao_social" in data
    
    def test_api_consultar_inexistente(self):
        """Testa API de consulta com CNPJ inexistente"""
        response = self.client.get('/api/consultar/99999999999999')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "erro" in data
    
    def test_api_listar(self):
        """Testa API de listagem"""
        response = self.client.get('/api/listar')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) >= 2
    
    def test_api_stats(self):
        """Testa API de estatísticas"""
        response = self.client.get('/api/stats')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "total_empresas" in data
        assert "por_situacao" in data
        assert "top_ufs" in data

class TestDataValidation:
    """Testes de validação de dados"""
    
    def test_cnpj_format_validation(self):
        """Testa validação de formato CNPJ"""
        consulta = CNPJConsulta()
        
        # CNPJs válidos
        valid_cnpjs = [
            "43227497000198",
            "11222333000144"
        ]
        
        for cnpj in valid_cnpjs:
            resultado = consulta.consultar_cnpj(cnpj)
            # Não deve ter erro de formato
            if "erro" in resultado:
                assert "14 dígitos" not in resultado["erro"]
        
        # CNPJs inválidos
        invalid_cnpjs = [
            "123",
            "12345678901234567890",
            "abcd1234567890",
            ""
        ]
        
        for cnpj in invalid_cnpjs:
            resultado = consulta.consultar_cnpj(cnpj)
            assert "erro" in resultado

def test_integration_full_flow():
    """Teste de integração completo"""
    # Criar sistema temporário
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "integration_test.db")
    
    # 1. Inicializar banco
    db = CNPJDatabase(db_path)
    assert Path(db_path).exists()
    
    # 2. Fazer consulta
    consulta = CNPJConsulta(db_path)
    resultado = consulta.consultar_cnpj("43227497000198")
    
    # 3. Verificar resultado
    assert "erro" not in resultado
    assert resultado["cnpj"] == "43227497000198"
    
    # 4. Testar listagem
    empresas = consulta.listar_empresas()
    assert len(empresas) >= 2
    
    # 5. Testar estatísticas
    stats = consulta.estatisticas()
    assert stats["total_empresas"] >= 2
    
    print("✅ Teste de integração completo passou!")

if __name__ == "__main__":
    # Executar teste de integração diretamente
    test_integration_full_flow()
    print("🧪 Execute: pytest tests/test_api.py -v")
