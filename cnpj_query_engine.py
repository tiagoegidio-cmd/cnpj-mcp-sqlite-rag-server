#!/usr/bin/env python3
"""
CNPJ Query Engine
Motor de consulta para base CNPJ no Google Drive
Projetado para uso com Claude Projetos em tempo real
"""

import pandas as pd
import sqlite3
from typing import Dict, List, Optional, Any, Union
import re
import json
from datetime import datetime
from google_drive_connector import GoogleDriveCNPJConnector

class CNPJQueryEngine:
    """Motor de consulta CNPJ otimizado para Claude Projetos"""
    
    def __init__(self, connector: GoogleDriveCNPJConnector = None):
        """
        Inicializa motor de consulta
        
        Args:
            connector: Conector do Google Drive (opcional)
        """
        self.connector = connector or GoogleDriveCNPJConnector()
        self.data_cache = {}
        self.last_update = None
        
    def load_data_source(self, force_reload: bool = False) -> bool:
        """
        Carrega fonte de dados do Google Drive
        
        Args:
            force_reload: Forçar recarregamento dos dados
            
        Returns:
            True se carregamento foi bem-sucedido
        """
        try:
            if not force_reload and self.data_cache:
                return True
            
            # Verificar fontes disponíveis
            sources = self.connector.get_available_data_sources()
            
            if not sources["primary_source"]:
                raise Exception("Nenhuma fonte de dados encontrada no Google Drive")
            
            # Carregar fonte primária (SQLite preferencial)
            if sources["recommended_source"] == "sqlite":
                conn = self.connector.download_file_content(
                    sources["primary_source"]["id"], 
                    "sqlite"
                )
                self.data_cache["connection"] = conn
                self.data_cache["type"] = "sqlite"
                
            else:
                # Carregar CSV ou Parquet como fallback
                for backup in sources["backup_sources"]:
                    if backup["name"].endswith('.csv'):
                        df = self.connector.download_file_content(backup["id"], "csv")
                        self.data_cache["dataframe"] = df
                        self.data_cache["type"] = "pandas"
                        break
            
            self.last_update = datetime.now()
            return True
            
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return False
    
    def normalize_cnpj(self, cnpj: str) -> str:
        """
        Normaliza CNPJ removendo formatação
        
        Args:
            cnpj: CNPJ com ou sem formatação
            
        Returns:
            CNPJ apenas com números
        """
        if not cnpj:
            return ""
        
        # Remove tudo que não é dígito
        return re.sub(r'\D', '', str(cnpj))
    
    def validate_cnpj(self, cnpj: str) -> bool:
        """
        Valida formato do CNPJ
        
        Args:
            cnpj: CNPJ para validar
            
        Returns:
            True se CNPJ é válido
        """
        cnpj_clean = self.normalize_cnpj(cnpj)
        
        # Verificar se tem 14 dígitos
        if len(cnpj_clean) != 14:
            return False
            
        # Verificar se não são todos iguais
        if len(set(cnpj_clean)) == 1:
            return False
            
        return True
    
    def format_cnpj(self, cnpj: str) -> str:
        """
        Formata CNPJ para exibição
        
        Args:
            cnpj: CNPJ sem formatação
            
        Returns:
            CNPJ formatado (XX.XXX.XXX/XXXX-XX)
        """
        cnpj_clean = self.normalize_cnpj(cnpj)
        
        if len(cnpj_clean) != 14:
            return cnpj
            
        return f"{cnpj_clean[:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:]}"
    
    def query_cnpj(self, cnpj: str) -> Dict[str, Any]:
        """
        Consulta CNPJ específico na base
        
        Args:
            cnpj: CNPJ para consultar
            
        Returns:
            Dados da empresa ou erro
        """
        # Validar CNPJ
        if not self.validate_cnpj(cnpj):
            return {
                "error": "CNPJ inválido",
                "message": "CNPJ deve ter 14 dígitos válidos",
                "cnpj_input": cnpj
            }
        
        # Carregar dados se necessário
        if not self.load_data_source():
            return {
                "error": "Erro ao acessar base de dados",
                "message": "Não foi possível conectar ao Google Drive"
            }
        
        cnpj_clean = self.normalize_cnpj(cnpj)
        
        try:
            if self.data_cache["type"] == "sqlite":
                return self._query_sqlite(cnpj_clean)
            elif self.data_cache["type"] == "pandas":
                return self._query_pandas(cnpj_clean)
            else:
                return {"error": "Tipo de dados não suportado"}
                
        except Exception as e:
            return {
                "error": "Erro na consulta",
                "message": str(e),
                "cnpj": cnpj_clean
            }
    
    def _query_sqlite(self, cnpj: str) -> Dict[str, Any]:
        """Consulta usando SQLite"""
        conn = self.data_cache["connection"]
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM empresas WHERE cnpj = ?", (cnpj,))
        result = cursor.fetchone()
        
        if not result:
            return {
                "error": "CNPJ não encontrado",
                "cnpj": cnpj,
                "cnpj_formatted": self.format_cnpj(cnpj)
            }
        
        # Obter nomes das colunas
        columns = [desc[0] for desc in cursor.description]
        
        # Criar dicionário com os dados
        empresa_data = dict(zip(columns, result))
        
        # Formatar dados para resposta
        return self._format_empresa_response(empresa_data)
    
    def _query_pandas(self, cnpj: str) -> Dict[str, Any]:
        """Consulta usando Pandas DataFrame"""
        df = self.data_cache["dataframe"]
        
        # Buscar empresa
        empresa = df[df['cnpj'] == cnpj]
        
        if empresa.empty:
            return {
                "error": "CNPJ não encontrado",
                "cnpj": cnpj,
                "cnpj_formatted": self.format_cnpj(cnpj)
            }
        
        # Converter para dicionário
        empresa_data = empresa.iloc[0].to_dict()
        
        return self._format_empresa_response(empresa_data)
    
    def _format_empresa_response(self, data: Dict) -> Dict[str, Any]:
        """
        Formata resposta da empresa para Claude
        
        Args:
            data: Dados brutos da empresa
            
        Returns:
            Dados formatados para resposta
        """
        return {
            "success": True,
            "cnpj": data.get('cnpj'),
            "cnpj_formatted": self.format_cnpj(data.get('cnpj', '')),
            "dados_cadastrais": {
                "razao_social": data.get('razao_social'),
                "nome_fantasia": data.get('nome_fantasia', ''),
                "situacao_cadastral": data.get('situacao_cadastral'),
                "data_situacao_cadastral": data.get('data_situacao_cadastral'),
                "natureza_juridica": data.get('natureza_juridica'),
                "porte_empresa": data.get('porte_empresa'),
                "capital_social": data.get('capital_social'),
                "data_inicio_atividade": data.get('data_inicio_atividade'),
                "opcao_simples": data.get('opcao_simples')
            },
            "endereco": {
                "tipo_logradouro": data.get('tipo_logradouro'),
                "logradouro": data.get('logradouro'),
                "numero": data.get('numero'),
                "complemento": data.get('complemento'),
                "bairro": data.get('bairro'),
                "cep": data.get('cep'),
                "municipio": data.get('municipio'),
                "uf": data.get('uf'),
                "endereco_completo": self._format_endereco_completo(data)
            },
            "atividade_economica": {
                "cnae_principal": data.get('cnae_principal'),
                "cnae_descricao": data.get('cnae_descricao')
            },
            "contato": {
                "telefone": data.get('telefone', ''),
                "email": data.get('email', '')
            },
            "metadata": {
                "fonte": "Google Drive - Base CNPJ",
                "ultima_atualizacao": self.last_update.isoformat() if self.last_update else None,
                "consulta_realizada_em": datetime.now().isoformat()
            }
        }
    
    def _format_endereco_completo(self, data: Dict) -> str:
        """Formata endereço completo"""
        partes = []
        
        if data.get('tipo_logradouro') and data.get('logradouro'):
            partes.append(f"{data['tipo_logradouro']} {data['logradouro']}")
        elif data.get('logradouro'):
            partes.append(data['logradouro'])
            
        if data.get('numero'):
            partes.append(f"nº {data['numero']}")
            
        if data.get('complemento'):
            partes.append(data['complemento'])
            
        if data.get('bairro'):
            partes.append(f"- {data['bairro']}")
            
        if data.get('municipio') and data.get('uf'):
            partes.append(f"- {data['municipio']}/{data['uf']}")
            
        if data.get('cep'):
            cep = data['cep']
            if len(cep) == 8:
                cep = f"{cep[:5]}-{cep[5:]}"
            partes.append(f"- CEP: {cep}")
        
        return ", ".join(partes)
    
    def search_by_name(self, nome: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca empresas por nome/razão social
        
        Args:
            nome: Nome ou parte do nome para buscar
            limit: Limite de resultados
            
        Returns:
            Lista de empresas encontradas
        """
        if not self.load_data_source():
            return []
        
        try:
            if self.data_cache["type"] == "sqlite":
                return self._search_sqlite_by_name(nome, limit)
            elif self.data_cache["type"] == "pandas":
                return self._search_pandas_by_name(nome, limit)
            else:
                return []
                
        except Exception as e:
            print(f"Erro na busca por nome: {e}")
            return []
    
    def _search_sqlite_by_name(self, nome: str, limit: int) -> List[Dict[str, Any]]:
        """Busca por nome usando SQLite"""
        conn = self.data_cache["connection"]
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cnpj, razao_social, nome_fantasia, situacao_cadastral, municipio, uf
            FROM empresas 
            WHERE razao_social LIKE ? OR nome_fantasia LIKE ?
            LIMIT ?
        """, (f'%{nome}%', f'%{nome}%', limit))
        
        results = cursor.fetchall()
        columns = ['cnpj', 'razao_social', 'nome_fantasia', 'situacao_cadastral', 'municipio', 'uf']
        
        empresas = []
        for row in results:
            empresa = dict(zip(columns, row))
            empresa['cnpj_formatted'] = self.format_cnpj(empresa['cnpj'])
            empresas.append(empresa)
        
        return empresas
    
    def _search_pandas_by_name(self, nome: str, limit: int) -> List[Dict[str, Any]]:
        """Busca por nome usando Pandas"""
        df = self.data_cache["dataframe"]
        
        # Busca case-insensitive
        mask = (
            df['razao_social'].str.contains(nome, case=False, na=False) |
            df['nome_fantasia'].str.contains(nome, case=False, na=False)
        )
        
        resultados = df[mask].head(limit)
        
        empresas = []
        for _, row in resultados.iterrows():
            empresa = row.to_dict()
            empresa['cnpj_formatted'] = self.format_cnpj(empresa['cnpj'])
            empresas.append(empresa)
        
        return empresas
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas da base de dados
        
        Returns:
            Estatísticas gerais
        """
        if not self.load_data_source():
            return {"error": "Não foi possível carregar dados"}
        
        try:
            if self.data_cache["type"] == "sqlite":
                return self._get_sqlite_statistics()
            elif self.data_cache["type"] == "pandas":
                return self._get_pandas_statistics()
            else:
                return {"error": "Tipo de dados não suportado"}
                
        except Exception as e:
            return {"error": f"Erro ao calcular estatísticas: {e}"}
    
    def _get_sqlite_statistics(self) -> Dict[str, Any]:
        """Estatísticas usando SQLite"""
        conn = self.data_cache["connection"]
        cursor = conn.cursor()
        
        # Total de empresas
        cursor.execute("SELECT COUNT(*) FROM empresas")
        total_empresas = cursor.fetchone()[0]
        
        # Por situação cadastral
        cursor.execute("SELECT situacao_cadastral, COUNT(*) FROM empresas GROUP BY situacao_cadastral")
        por_situacao = dict(cursor.fetchall())
        
        # Por UF
        cursor.execute("SELECT uf, COUNT(*) FROM empresas GROUP BY uf ORDER BY COUNT(*) DESC LIMIT 10")
        por_uf = dict(cursor.fetchall())
        
        # Por porte
        cursor.execute("SELECT porte_empresa, COUNT(*) FROM empresas GROUP BY porte_empresa")
        por_porte = dict(cursor.fetchall())
        
        return {
            "total_empresas": total_empresas,
            "por_situacao_cadastral": por_situacao,
            "por_uf": por_uf,
            "por_porte": por_porte,
            "fonte": "SQLite Database",
            "ultima_atualizacao": self.last_update.isoformat() if self.last_update else None
        }
    
    def _get_pandas_statistics(self) -> Dict[str, Any]:
        """Estatísticas usando Pandas"""
        df = self.data_cache["dataframe"]
        
        stats = {
            "total_empresas": len(df),
            "fonte": "CSV/Parquet File",
            "ultima_atualizacao": self.last_update.isoformat() if self.last_update else None
        }
        
        # Adicionar estatísticas se colunas existirem
        if 'situacao_cadastral' in df.columns:
            stats["por_situacao_cadastral"] = df['situacao_cadastral'].value_counts().to_dict()
            
        if 'uf' in df.columns:
            stats["por_uf"] = df['uf'].value_counts().head(10).to_dict()
            
        if 'porte_empresa' in df.columns:
            stats["por_porte"] = df['porte_empresa'].value_counts().to_dict()
        
        return stats

# Exemplo de uso para Claude Projetos
def consultar_cnpj_para_claude(cnpj: str) -> str:
    """
    Função simplificada para Claude consultar CNPJ
    
    Args:
        cnpj: CNPJ para consultar
        
    Returns:
        Resposta formatada para Claude
    """
    engine = CNPJQueryEngine()
    resultado = engine.query_cnpj(cnpj)
    
    if "error" in resultado:
        return f"❌ Erro: {resultado['error']} - {resultado.get('message', '')}"
    
    # Formatar resposta amigável
    dados = resultado["dados_cadastrais"]
    endereco = resultado["endereco"]
    
    resposta = f"""
🏢 **CONSULTA CNPJ: {resultado['cnpj_formatted']}**

📋 **Dados Cadastrais:**
• Razão Social: {dados['razao_social']}
• Nome Fantasia: {dados['nome_fantasia'] or 'Não informado'}
• Situação: {dados['situacao_cadastral']}
• Porte: {dados['porte_empresa']}
• Capital Social: R$ {dados['capital_social']:,.2f}

📍 **Endereço:**
{endereco['endereco_completo']}

💼 **Atividade:**
• CNAE: {resultado['atividade_economica']['cnae_principal']} - {resultado['atividade_economica']['cnae_descricao']}

📊 **Fonte:** {resultado['metadata']['fonte']}
🕒 **Atualizado em:** {resultado['metadata']['ultima_atualizacao']}
"""
    
    return resposta

if __name__ == "__main__":
    # Teste para desenvolvimento
    print(consultar_cnpj_para_claude("43227497000198"))
