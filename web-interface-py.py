#!/usr/bin/env python3
"""
Interface Web para Sistema CNPJ
Flask + Bootstrap para consultas simples
"""

from flask import Flask, render_template_string, request, jsonify
from main import CNPJConsulta
import json

app = Flask(__name__)
consulta = CNPJConsulta()

# Template HTML inline
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Consulta CNPJ</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .card { box-shadow: 0 8px 32px rgba(0,0,0,0.1); border: none; border-radius: 15px; }
        .btn-primary { background: linear-gradient(45deg, #667eea, #764ba2); border: none; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        .result-card { margin-top: 20px; animation: fadeIn 0.5s; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .loading { display: none; }
        .status-ativa { color: #28a745; }
        .status-inativa { color: #dc3545; }
    </style>
</head>
<body>
    <div class="container my-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                
                <!-- Header -->
                <div class="text-center mb-4">
                    <h1 class="text-white mb-3">
                        <i class="fas fa-building"></i>
                        Sistema de Consulta CNPJ
                    </h1>
                    <p class="text-white-50">Consulte dados de empresas de forma simples e rápida</p>
                </div>

                <!-- Search Card -->
                <div class="card">
                    <div class="card-body p-4">
                        <form id="consultaForm">
                            <div class="row">
                                <div class="col-md-8">
                                    <label class="form-label">CNPJ (apenas números)</label>
                                    <input type="text" 
                                           class="form-control form-control-lg" 
                                           id="cnpjInput" 
                                           placeholder="00000000000000"
                                           maxlength="14"
                                           pattern="[0-9]*">
                                    <div class="form-text">Formato: <span id="cnpjFormatted">00.000.000/0000-00</span></div>
                                </div>
                                <div class="col-md-4 d-flex align-items-end">
                                    <button type="submit" class="btn btn-primary btn-lg w-100">
                                        <i class="fas fa-search"></i>
                                        Consultar
                                    </button>
                                </div>
                            </div>
                        </form>

                        <!-- Loading -->
                        <div class="loading text-center mt-3">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Carregando...</span>
                            </div>
                            <p class="mt-2">Consultando CNPJ...</p>
                        </div>
                    </div>
                </div>

                <!-- Examples -->
                <div class="card mt-3">
                    <div class="card-body">
                        <h6 class="card-title">CNPJs de Exemplo:</h6>
                        <div class="d-flex gap-2 flex-wrap">
                            <button class="btn btn-outline-secondary btn-sm exemplo-btn" data-cnpj="43227497000198">
                                43.227.497/0001-98
                            </button>
                            <button class="btn btn-outline-secondary btn-sm exemplo-btn" data-cnpj="11222333000144">
                                11.222.333/0001-44
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Results -->
                <div id="resultados"></div>

                <!-- Actions -->
                <div class="card mt-3">
                    <div class="card-body">
                        <h6 class="card-title">Outras Ações:</h6>
                        <div class="d-flex gap-2 flex-wrap">
                            <button class="btn btn-info btn-sm" onclick="listarEmpresas()">
                                <i class="fas fa-list"></i> Listar Empresas
                            </button>
                            <button class="btn btn-success btn-sm" onclick="mostrarEstatisticas()">
                                <i class="fas fa-chart-bar"></i> Estatísticas
                            </button>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Format CNPJ input
        document.getElementById('cnpjInput').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\\D/g, '');
            e.target.value = value;
            
            // Format display
            if (value.length === 14) {
                let formatted = value.replace(/(\\d{2})(\\d{3})(\\d{3})(\\d{4})(\\d{2})/, '$1.$2.$3/$4-$5');
                document.getElementById('cnpjFormatted').textContent = formatted;
            } else {
                document.getElementById('cnpjFormatted').textContent = '00.000.000/0000-00';
            }
        });

        // Form submit
        document.getElementById('consultaForm').addEventListener('submit', function(e) {
            e.preventDefault();
            let cnpj = document.getElementById('cnpjInput').value;
            if (cnpj.length === 14) {
                consultarCNPJ(cnpj);
            } else {
                alert('CNPJ deve ter 14 dígitos');
            }
        });

        // Example buttons
        document.querySelectorAll('.exemplo-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                let cnpj = this.dataset.cnpj;
                document.getElementById('cnpjInput').value = cnpj;
                document.getElementById('cnpjInput').dispatchEvent(new Event('input'));
                consultarCNPJ(cnpj);
            });
        });

        // Consultar CNPJ
        function consultarCNPJ(cnpj) {
            document.querySelector('.loading').style.display = 'block';
            document.getElementById('resultados').innerHTML = '';

            fetch('/api/consultar/' + cnpj)
                .then(response => response.json())
                .then(data => {
                    document.querySelector('.loading').style.display = 'none';
                    mostrarResultado(data);
                })
                .catch(error => {
                    document.querySelector('.loading').style.display = 'none';
                    mostrarErro('Erro na consulta: ' + error.message);
                });
        }

        // Mostrar resultado
        function mostrarResultado(data) {
            let html = '';
            
            if (data.erro) {
                html = `
                    <div class="card result-card">
                        <div class="card-body">
                            <div class="alert alert-warning">
                                <i class="fas fa-exclamation-triangle"></i>
                                ${data.erro}
                                ${data.sugestao ? '<br><small>' + data.sugestao + '</small>' : ''}
                            </div>
                        </div>
                    </div>
                `;
            } else {
                let situacaoClass = data.situacao_cadastral === 'ATIVA' ? 'status-ativa' : 'status-inativa';
                html = `
                    <div class="card result-card">
                        <div class="card-header">
                            <h5 class="mb-0">
                                <i class="fas fa-building text-primary"></i>
                                ${data.razao_social}
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Dados Principais</h6>
                                    <p><strong>CNPJ:</strong> ${formatCNPJ(data.cnpj)}</p>
                                    <p><strong>Nome Fantasia:</strong> ${data.nome_fantasia || 'Não informado'}</p>
                                    <p><strong>Situação:</strong> <span class="${situacaoClass}"><strong>${data.situacao_cadastral}</strong></span></p>
                                    <p><strong>Porte:</strong> ${data.porte_empresa}</p>
                                    <p><strong>Capital Social:</strong> R$ ${parseFloat(data.capital_social || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2})}</p>
                                </div>
                                <div class="col-md-6">
                                    <h6>Endereço</h6>
                                    <p>${data.tipo_logradouro || ''} ${data.logradouro}, ${data.numero}</p>
                                    ${data.complemento ? '<p>' + data.complemento + '</p>' : ''}
                                    <p>${data.bairro} - ${data.municipio}/${data.uf}</p>
                                    <p>CEP: ${data.cep ? data.cep.replace(/(\\d{5})(\\d{3})/, '$1-$2') : ''}</p>
                                </div>
                            </div>
                            <div class="row mt-3">
                                <div class="col-12">
                                    <h6>Atividade Econômica</h6>
                                    <p><strong>CNAE Principal:</strong> ${data.cnae_principal} - ${data.cnae_descricao}</p>
                                    <p><strong>Natureza Jurídica:</strong> ${data.natureza_juridica}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            document.getElementById('resultados').innerHTML = html;
        }

        // Listar empresas
        function listarEmpresas() {
            document.querySelector('.loading').style.display = 'block';
            
            fetch('/api/listar')
                .then(response => response.json())
                .then(data => {
                    document.querySelector('.loading').style.display = 'none';
                    let html = `
                        <div class="card result-card">
                            <div class="card-header">
                                <h5 class="mb-0">
                                    <i class="fas fa-list text-info"></i>
                                    Empresas Cadastradas
                                </h5>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-hover">
                                        <thead>
                                            <tr>
                                                <th>CNPJ</th>
                                                <th>Razão Social</th>
                                                <th>Situação</th>
                                                <th>UF</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                    `;
                    
                    data.forEach(empresa => {
                        let situacaoClass = empresa.situacao_cadastral === 'ATIVA' ? 'status-ativa' : 'status-inativa';
                        html += `
                            <tr style="cursor: pointer;" onclick="consultarCNPJ('${empresa.cnpj}')">
                                <td>${formatCNPJ(empresa.cnpj)}</td>
                                <td>${empresa.razao_social}</td>
                                <td><span class="${situacaoClass}">${empresa.situacao_cadastral}</span></td>
                                <td>${empresa.uf}</td>
                            </tr>
                        `;
                    });
                    
                    html += `
                                        </tbody>
                                    </table>
                                </div>
                                <small class="text-muted">Clique em uma linha para ver detalhes</small>
                            </div>
                        </div>
                    `;
                    
                    document.getElementById('resultados').innerHTML = html;
                });
        }

        // Mostrar estatísticas
        function mostrarEstatisticas() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    let html = `
                        <div class="card result-card">
                            <div class="card-header">
                                <h5 class="mb-0">
                                    <i class="fas fa-chart-bar text-success"></i>
                                    Estatísticas do Banco
                                </h5>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-4">
                                        <div class="text-center">
                                            <h3 class="text-primary">${data.total_empresas}</h3>
                                            <p>Total de Empresas</p>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <h6>Por Situação</h6>
                                        <ul class="list-unstyled">
                    `;
                    
                    for (let [situacao, count] of Object.entries(data.por_situacao)) {
                        html += `<li>${situacao}: <strong>${count}</strong></li>`;
                    }
                    
                    html += `
                                        </ul>
                                    </div>
                                    <div class="col-md-4">
                                        <h6>Top UFs</h6>
                                        <ul class="list-unstyled">
                    `;
                    
                    for (let [uf, count] of Object.entries(data.top_ufs)) {
                        html += `<li>${uf}: <strong>${count}</strong></li>`;
                    }
                    
                    html += `
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    document.getElementById('resultados').innerHTML = html;
                });
        }

        // Format CNPJ
        function formatCNPJ(cnpj) {
            return cnpj.replace(/(\\d{2})(\\d{3})(\\d{3})(\\d{4})(\\d{2})/, '$1.$2.$3/$4-$5');
        }

        // Mostrar erro
        function mostrarErro(message) {
            document.getElementById('resultados').innerHTML = `
                <div class="card result-card">
                    <div class="card-body">
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-circle"></i>
                            ${message}
                        </div>
                    </div>
                </div>
            `;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Página principal"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/consultar/<cnpj>')
def api_consultar(cnpj):
    """API para consultar CNPJ"""
    try:
        resultado = consulta.consultar_cnpj(cnpj)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/listar')
def api_listar():
    """API para listar empresas"""
    try:
        empresas = consulta.listar_empresas(20)
        return jsonify(empresas)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """API para estatísticas"""
    try:
        stats = consulta.estatisticas()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/buscar/<termo>')
def api_buscar(termo):
    """API para buscar por nome"""
    try:
        resultados = consulta.buscar_por_nome(termo)
        return jsonify(resultados)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
