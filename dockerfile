# Dockerfile para Apify Actor Python
FROM apify/actor-python:3.11

# Copiar requirements e instalar dependências
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copiar código fonte
COPY . ./

# Comando principal
CMD python3 main.py
