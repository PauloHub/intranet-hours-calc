#!/bin/bash

# Script para construir e executar a aplicação com Docker
# Autor: Sistema automatizado

echo "🐳 CALCULADORA DE BANCO DE HORAS - DOCKER"
echo "=========================================="
echo ""

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado!"
    echo "   Instale o Docker antes de continuar."
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado!"
    echo "   Instale o Docker Compose antes de continuar."
    exit 1
fi

echo "✅ Docker e Docker Compose encontrados!"
echo ""

# Menu de opções
echo "Escolha uma opção:"
echo "1) 🏗️  Construir e executar pela primeira vez"
echo "2) 🚀 Executar aplicação (já construída)"
echo "3) 🔄 Reconstruir e executar (forçar rebuild)"
echo "4) 🛑 Parar aplicação"
echo "5) 📋 Ver logs da aplicação"
echo "6) 🧹 Limpar containers e imagens"
echo ""

read -p "Digite sua escolha (1-6): " escolha

case $escolha in
    1)
        echo "🏗️ Construindo e executando aplicação..."
        docker-compose up --build -d
        echo ""
        echo "✅ Aplicação executando!"
        echo "🌐 Acesse: http://localhost:8501"
        echo "📋 Para ver logs: ./docker_run.sh e escolha opção 5"
        ;;
    2)
        echo "🚀 Executando aplicação..."
        docker-compose up -d
        echo ""
        echo "✅ Aplicação executando!"
        echo "🌐 Acesse: http://localhost:8501"
        ;;
    3)
        echo "🔄 Reconstruindo aplicação..."
        docker-compose down
        docker-compose up --build -d
        echo ""
        echo "✅ Aplicação reconstruída e executando!"
        echo "🌐 Acesse: http://localhost:8501"
        ;;
    4)
        echo "🛑 Parando aplicação..."
        docker-compose down
        echo "✅ Aplicação parada!"
        ;;
    5)
        echo "📋 Logs da aplicação:"
        echo "==============================="
        docker-compose logs -f
        ;;
    6)
        echo "🧹 Limpando containers e imagens..."
        docker-compose down
        docker system prune -f
        echo "✅ Limpeza concluída!"
        ;;
    *)
        echo "❌ Opção inválida!"
        echo "Execute novamente o script e escolha uma opção de 1 a 6."
        exit 1
        ;;
esac

echo ""
echo "🎉 Operação concluída!"
