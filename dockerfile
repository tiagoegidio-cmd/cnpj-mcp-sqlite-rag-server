# Dockerfile para Apify Actor Python com MCP
FROM apify/actor-python:3.11

# Copiar requirements e instalar dependências
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copiar código fonte
COPY . ./

# Suporte para MCP
ENV MCP_ENABLED=true

# Comando principal (mantém compatibilidade)
CMD python3 main.py
