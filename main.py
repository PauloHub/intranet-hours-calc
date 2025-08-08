#!/usr/bin/env python3
"""
Script principal para executar a Calculadora de Banco de Horas
"""

import sys
import os

# Adicionar o diretório src ao path para importações
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Executar o módulo principal
if __name__ == "__main__":
    from app.app_streamlit import main
    main()
