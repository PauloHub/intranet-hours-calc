# Calculadora de Banco de Horas - Docker
FROM python:3.11-slim

# Metadados
LABEL maintainer="Sistema automatizado"
LABEL description="Calculadora genérica de banco de horas com interface Streamlit"
LABEL version="1.0"

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (para otimizar cache do Docker)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY *.py ./
COPY *.md ./
COPY styles/ ./styles/

# Criar diretório para dados temporários
RUN mkdir -p /app/temp

# Expor porta do Streamlit
EXPOSE 8501

# Configurar Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Comando para executar a aplicação
CMD ["streamlit", "run", "app_streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]
