#!/usr/bin/env python3
"""
Utilitários para a Calculadora de Banco de Horas
Funções auxiliares para formatação e manipulação de dados
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import io
import re


def init_session_state():
    """Inicializa o estado da sessão"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'calculator' not in st.session_state:
        st.session_state.calculator = None
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'error_message' not in st.session_state:
        st.session_state.error_message = None
    if 'error_details' not in st.session_state:
        st.session_state.error_details = None


def format_time(minutes):
    """Formata minutos em HH:MM ou em minutos se menor que 1 hora"""
    if minutes == 0:
        return "00:00"
    
    # Se for menor que 60 minutos (menos de 1 hora), exibir em minutos
    if abs(minutes) < 60:
        sign = "-" if minutes < 0 else "+"
        return f"{sign}{abs(minutes)}min"
    
    # Caso contrário, exibir em formato HH:MM
    hours = abs(minutes) // 60
    mins = abs(minutes) % 60
    sign = "-" if minutes < 0 else "+"
    return f"{sign}{hours:02d}:{mins:02d}"


def load_css(css_file):
    """Carrega arquivo CSS e aplica no Streamlit de forma segura"""
    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # Sanitização básica: remover conteúdo potencialmente perigoso
        # Remove possíveis scripts ou imports externos
        css_content = re.sub(r'@import\s+url\([^)]*\);?', '', css_content)
        css_content = re.sub(r'javascript:', '', css_content, flags=re.IGNORECASE)
        
        st.markdown(f"""
        <style>
        {css_content}
        </style>
        """, unsafe_allow_html=True)
        
    except FileNotFoundError:
        st.warning(f"⚠️ Arquivo CSS não encontrado: {css_file}")
    except Exception as e:
        st.warning(f"⚠️ Erro ao carregar CSS: {str(e)}")


def create_monthly_chart(df):
    """Cria gráfico mensal de banco de horas"""
    fig = go.Figure()
    
    # Proteção contra DataFrame vazio
    if df.empty:
        fig.add_annotation(
            text="Nenhum dado disponível",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        fig.update_layout(
            title='Banco de Horas por Mês',
            height=400
        )
        return fig
    
    # Cores baseadas no saldo
    colors = ['#28a745' if x > 0 else '#dc3545' if x < 0 else '#6c757d' for x in df['saldo_minutos']]
    
    fig.add_trace(go.Bar(
        x=df['mes_ano'],
        y=df['saldo_horas'],
        text=df['saldo_formatado'],
        textposition='outside',
        marker_color=colors,
        hovertemplate='<b>%{x}</b><br>Saldo: %{text}<br><extra></extra>'
    ))
    
    fig.update_layout(
        title='Banco de Horas por Mês',
        xaxis_title='Mês/Ano',
        yaxis_title='Horas',
        showlegend=False,
        height=400,
        xaxis_tickangle=-45
    )
    
    # Linha zero
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    return fig


def create_cumulative_chart(df):
    """Cria gráfico cumulativo de banco de horas"""
    # Proteção contra DataFrame vazio
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Nenhum dado disponível",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        fig.update_layout(
            title='Evolução Cumulativa do Banco de Horas',
            height=400
        )
        return fig
    
    # Criar uma cópia do DataFrame para não alterar o original
    df_work = df.copy()
    
    try:
        # Converter mes_ano para datetime para ordenação correta
        df_work['data_ordenacao'] = pd.to_datetime(df_work['mes_ano'], format='%m/%Y')
        
        # Ordenar por data cronológica
        df_sorted = df_work.sort_values('data_ordenacao')
        
    except Exception:
        # Fallback: se der erro na conversão, usar ordenação simples
        # Isso pode acontecer se o formato for diferente do esperado
        df_sorted = df_work.sort_values('mes_ano')
    
    # Calcular valores cumulativos
    df_sorted['saldo_cumulativo'] = df_sorted['saldo_minutos'].cumsum()
    df_sorted['saldo_cum_horas'] = df_sorted['saldo_cumulativo'] / 60
    
    fig = go.Figure()
    
    # Linha cumulativa
    fig.add_trace(go.Scatter(
        x=df_sorted['mes_ano'],
        y=df_sorted['saldo_cum_horas'],
        mode='lines+markers',
        name='Saldo Cumulativo',
        line=dict(width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{x}</b><br>Acumulado: %{y:.1f}h<br><extra></extra>'
    ))
    
    fig.update_layout(
        title='Evolução Cumulativa do Banco de Horas',
        xaxis_title='Mês/Ano',
        yaxis_title='Horas Acumuladas',
        height=400,
        xaxis_tickangle=-45
    )
    
    # Linha zero
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    return fig


def create_summary_metrics(total_minutes, details):
    """Cria métricas resumo"""
    # Proteção contra lista vazia
    if not details:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("⚪ Saldo Final", "00:00", "Sem dados")
        with col2:
            st.metric("🟢 Meses Positivos", 0)
        with col3:
            st.metric("🔴 Meses Negativos", 0)
        with col4:
            st.metric("⚪ Meses Neutros", 0)
        return
    
    positive_months = sum(1 for d in details if d['saldo'] > 0)
    negative_months = sum(1 for d in details if d['saldo'] < 0)
    neutral_months = sum(1 for d in details if d['saldo'] == 0)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        saldo_formatado = format_time(total_minutes)
        if total_minutes > 0:
            st.metric("🟢 Saldo Final", saldo_formatado, "Crédito")
        elif total_minutes < 0:
            st.metric("🔴 Saldo Final", saldo_formatado, "Débito")
        else:
            st.metric("⚪ Saldo Final", "00:00", "Neutro")
    
    with col2:
        st.metric("🟢 Meses Positivos", positive_months)
    
    with col3:
        st.metric("🔴 Meses Negativos", negative_months)
    
    with col4:
        st.metric("⚪ Meses Neutros", neutral_months)


def download_report(df, total_minutes):
    """Gera relatório para download"""
    buffer = io.StringIO()
    
    buffer.write("RELATÓRIO DE BANCO DE HORAS\n")
    buffer.write("=" * 50 + "\n\n")
    buffer.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
    
    buffer.write("DETALHES POR MÊS:\n")
    buffer.write("-" * 30 + "\n")
    
    # Proteção contra DataFrame vazio
    if df.empty:
        buffer.write("Nenhum dado disponível para o período selecionado.\n")
    else:
        for _, row in df.iterrows():
            status = "CRÉDITO" if row['saldo_minutos'] > 0 else "DÉBITO" if row['saldo_minutos'] < 0 else "NEUTRO"
            buffer.write(f"{row['mes_ano']}: {row['saldo_formatado']} ({status})\n")
    
    buffer.write(f"\nRESULTADO FINAL:\n")
    buffer.write("-" * 20 + "\n")
    total_formatted = format_time(total_minutes)
    if total_minutes > 0:
        buffer.write(f"SALDO POSITIVO: {total_formatted}\n")
        buffer.write("A empresa deve horas ao funcionário\n")
    elif total_minutes < 0:
        buffer.write(f"SALDO NEGATIVO: {total_formatted}\n")
        buffer.write("O funcionário deve horas à empresa\n")
    else:
        buffer.write(f"SALDO ZERADO: {total_formatted}\n")
        buffer.write("Situação equilibrada\n")
    
    return buffer.getvalue()
