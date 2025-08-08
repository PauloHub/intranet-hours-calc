#!/usr/bin/env python3
"""
Interface Streamlit para Calculadora de Banco de Horas
Versão web genérica para múltiplas intranets
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import urlparse
import time

# Importar módulos locais
try:
    # Tentativa com importação relativa (quando executado como módulo)
    from .banco_horas import BancoHorasAdvanced
    from .utils import (
        init_session_state, 
        format_time, 
        load_css,
        create_monthly_chart, 
        create_cumulative_chart,
        create_summary_metrics,
        download_report
    )
except ImportError:
    # Fallback para importação absoluta (quando executado diretamente)
    from banco_horas import BancoHorasAdvanced
    from utils import (
        init_session_state, 
        format_time, 
        load_css,
        create_monthly_chart, 
        create_cumulative_chart,
        create_summary_metrics,
        download_report
    )

# Configuração da página
st.set_page_config(
    page_title="Calculadora de Banco de Horas",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carregar CSS externo
import os
css_path = os.path.join(os.path.dirname(__file__), '..', 'styles', 'main.css')
load_css(css_path)


def main():
    init_session_state()
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Calculadora de Banco de Horas</h1>
        <p>Interface web para múltiplas intranets</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar para configuração
    with st.sidebar:
        st.header("⚙️ Configuração")
        
        # URL da intranet
        st.subheader("🌐 Intranet")
        url_intranet = st.text_input(
            "URL da Intranet:",
            placeholder="https://intranet.empresa.com",
            help="Digite a URL completa da sua intranet"
        )
        
        # Processar e limpar a URL
        if url_intranet:
            # Remover espaços em branco
            url_intranet = url_intranet.strip()
            
            # Adicionar https:// se não tiver protocolo
            if not url_intranet.startswith(('http://', 'https://')):
                url_intranet = 'https://' + url_intranet
            
            # Extrair apenas o domínio principal (remover paths e parâmetros)
            try:
                parsed = urlparse(url_intranet)
                # Validação básica de segurança
                if not parsed.netloc or parsed.netloc.lower() in ['localhost', '127.0.0.1']:
                    st.warning("⚠️ URLs locais não são permitidas por segurança")
                    url_intranet = ""
                elif parsed.scheme not in ['http', 'https']:
                    st.warning("⚠️ Apenas URLs HTTP/HTTPS são permitidas")
                    url_intranet = ""
                else:
                    url_intranet = f"{parsed.scheme}://{parsed.netloc}"
                    # Exibir URL limpa para o usuário
                    if parsed.netloc:
                        st.info(f"🔗 URL processada: `{url_intranet}`")
            except Exception:
                st.warning("⚠️ URL inválida")
                url_intranet = ""
        
        # Credenciais
        st.subheader("🔐 Credenciais")
        usuario = st.text_input("Usuário:", placeholder="seu.usuario")
        senha = st.text_input("Senha:", type="password")
        
        # Período
        st.subheader("📅 Período")
        
        # Calcular datas padrão
        hoje = datetime.now()
        primeiro_dia_mes_atual = hoje.replace(day=1)
        ultimo_dia_mes_passado = primeiro_dia_mes_atual - timedelta(days=1)
        
        # Data início: 1 ano antes da data fim (último dia do mês passado)
        data_inicio_padrao = ultimo_dia_mes_passado.replace(year=ultimo_dia_mes_passado.year - 1, day=1)
        
        # Calcular limites dinâmicos baseados nas regras
        hoje_date = hoje.date()
        limite_data_fim = hoje_date - timedelta(days=1)  # Data fim deve ser menor que hoje
        limite_data_inicio = hoje_date - timedelta(days=2)  # Data início deve ser menor que hoje - 2 dias
        
        # Data início
        data_inicio = st.date_input(
            "📅 Data Início (Mês/Ano):",
            value=data_inicio_padrao,
            min_value=datetime(2000, 1, 1),
            max_value=limite_data_inicio,
            help="Selecione o mês e ano de início (deve ser anterior a pelo menos 2 dias atrás)"
        )
        
        # Data fim
        data_fim = st.date_input(
            "📅 Data Fim (Mês/Ano):",
            value=ultimo_dia_mes_passado,
            min_value=datetime(2000, 1, 1),
            max_value=limite_data_fim,
            help="Selecione o mês e ano de fim (deve ser anterior a hoje)"
        )
        
        # Extrair mês e ano
        mes_inicio = data_inicio.month
        ano_inicio = data_inicio.year
        mes_fim = data_fim.month
        ano_fim = data_fim.year
        
        # Validação das datas (fallback de segurança)
        hoje_data = datetime.now().date()
        limite_inicio = hoje_data - timedelta(days=2)
        
        # Validação: data fim deve ser anterior a hoje
        if data_fim >= hoje_data:
            st.error("❌ **A data de fim deve ser anterior a hoje!**")
            return
        
        # Validação: data início deve ser anterior a hoje - 2 dias
        if data_inicio >= limite_inicio:
            st.error("❌ **A data de início deve ser anterior a pelo menos 2 dias atrás!**")
            return
        
        # Validação: data fim deve ser maior ou igual à data início
        data_inicio_mes = datetime(ano_inicio, mes_inicio, 1)
        data_fim_mes = datetime(ano_fim, mes_fim, 1)
        
        if data_fim_mes < data_inicio_mes:
            st.error("❌ **Data de fim deve ser maior ou igual à data de início!**")
            return  # Para a execução se as datas forem inválidas
        
        # Botão de processar
        if st.button("🚀 Calcular Banco de Horas", type="primary"):
          # Validação mais rigorosa - verificar se campos não estão vazios ou só com espaços
          if not all([url_intranet and url_intranet.strip(), 
                     usuario and usuario.strip(), 
                     senha and senha.strip()]):
              st.error("❌ Preencha todos os campos!")
          else:
              # Salvar dados na sessão para processamento na área principal
              st.session_state.processing = True
              st.session_state.url_intranet = url_intranet
              st.session_state.usuario = usuario
              st.session_state.senha = senha
              st.session_state.mes_inicio = mes_inicio
              st.session_state.ano_inicio = ano_inicio
              st.session_state.mes_fim = mes_fim
              st.session_state.ano_fim = ano_fim
              st.session_state.results = None  # Limpa resultados anteriores
              st.session_state.error_message = None  # Limpa erros anteriores
              st.session_state.error_details = None


    # ÁREA PRINCIPAL - Controle de fluxo exclusivo
    if st.session_state.processing:
        # === MODO PROCESSAMENTO ===
        # Limpar tudo primeiro
        st.session_state.results = None
        
        # Recuperar dados da sessão
        url_intranet = st.session_state.get('url_intranet', '')
        usuario = st.session_state.get('usuario', '')
        senha = st.session_state.get('senha', '')
        mes_inicio = st.session_state.get('mes_inicio', 1)
        ano_inicio = st.session_state.get('ano_inicio', 2025)
        mes_fim = st.session_state.get('mes_fim', 1)
        ano_fim = st.session_state.get('ano_fim', 2025)
        
        # Interface de progresso - área dedicada
        st.markdown("---")  # Separador visual
        st.info("🔄 **Processando banco de horas...** Aguarde, isso pode levar alguns minutos.")
        
        # Container dedicado apenas para progresso
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            progress_text = st.empty()
            status_text = st.empty()
        
        try:
            # Etapa 1: Inicializar calculadora
            progress_bar.progress(10)
            progress_text.text("Progresso: 10% - Inicializando...")
            status_text.info("🔧 Inicializando calculadora...")
            calc = BancoHorasAdvanced(url_intranet)
            time.sleep(1)
            
            # Etapa 2: fazer_login
            progress_bar.progress(30)
            progress_text.text("Progresso: 30% - Fazendo login...")
            status_text.info("🔐 Fazendo login na intranet...")
            time.sleep(0.5)
            
            if calc.fazer_login(usuario, senha):
                progress_bar.progress(50)
                progress_text.text("Progresso: 50% - Login realizado!")
                status_text.success("✅ Login realizado com sucesso!")
                time.sleep(1)
                
                # Etapa 3: Calcular banco de horas com progresso proporcional
                progress_bar.progress(70)
                progress_text.text("Progresso: 70% - Iniciando cálculos...")
                status_text.info("📊 Calculando banco de horas... Isso pode levar alguns minutos...")
                
                # Função de callback para atualizar progresso durante cálculo
                def update_progress(mes_atual, total_meses, mes_ano):
                    # Progresso de 70% a 90% (20% de range)
                    progresso_base = 70
                    progresso_range = 20
                    
                    # Proteção contra divisão por zero
                    if total_meses > 0:
                        progresso_atual = progresso_base + (progresso_range * mes_atual / total_meses)
                    else:
                        progresso_atual = progresso_base
                    
                    progress_bar.progress(int(progresso_atual))
                    progress_text.text(f"Progresso: {int(progresso_atual)}% - Calculando {mes_ano} ({mes_atual}/{total_meses})")
                    status_text.info(f"📊 Processando mês {mes_ano} ({mes_atual} de {total_meses})...")
                
                total_minutos, detalhes = calc.calcular_banco_horas(
                    mes_inicio, ano_inicio, mes_fim, ano_fim, progress_callback=update_progress
                )
                
                # Etapa 4: Finalizar
                progress_bar.progress(90)
                progress_text.text("Progresso: 90% - Organizando resultados...")
                status_text.info("📋 Organizando resultados...")
                time.sleep(0.5)
                
                # Salvar resultados
                st.session_state.results = {
                    'total_minutos': total_minutos,
                    'detalhes': detalhes,
                    'periodo': f"{mes_inicio:02d}/{ano_inicio} - {mes_fim:02d}/{ano_fim}"
                }
                
                # Marcar que houve mudança nos resultados para recriar cache da tabela
                st.session_state.results_changed = True
                
                # Completar
                progress_bar.progress(100)
                progress_text.text("Progresso: 100% - Concluído!")
                status_text.success("🎉 Cálculo concluído com sucesso!")
                time.sleep(2)
                
            else:
                progress_bar.progress(0)
                progress_text.text("Erro no processo")
                status_text.error("❌ Erro no login. Verifique suas credenciais e URL da intranet.")
                
                # Salvar erro na sessão
                st.session_state.error_message = "❌ Erro no login. Verifique suas credenciais e URL da intranet."
                st.session_state.error_details = [
                    "• Verifique se a URL da intranet está correta",
                    "• Confirme suas credenciais de login", 
                    "• Teste se consegue acessar a intranet pelo navegador"
                ]
                time.sleep(3)
                
        except Exception as e:
            progress_bar.progress(0)
            progress_text.text("Erro durante o processamento")
            status_text.error(f"❌ Erro durante o processamento: {str(e)}")
            
            # Salvar erro na sessão
            st.session_state.error_message = f"❌ Erro durante o processamento: {str(e)}"
            st.session_state.error_details = [
                "• Verifique se a URL da intranet está correta",
                "• Confirme suas credenciais de login",
                "• Teste se consegue acessar a intranet pelo navegador"
            ]
            time.sleep(3)
        
        finally:
            # Limpar credenciais sensíveis da sessão por segurança
            if 'senha' in st.session_state:
                del st.session_state.senha
            if 'usuario' in st.session_state:
                del st.session_state.usuario
            
            # Limpar estado de processamento
            st.session_state.processing = False
            time.sleep(1)
            st.rerun()
    
    elif st.session_state.results:
        # === MODO RESULTADOS ===
        results = st.session_state.results
        total_minutos = results['total_minutos']
        detalhes = results['detalhes']
        
        st.markdown("---")  # Separador visual
        st.header(f"📊 Resultados - Período: {results['periodo']}")
        
        # Métricas resumo
        create_summary_metrics(total_minutos, detalhes)
        
        # Verificar se há dados para exibir
        if not detalhes:
            st.warning("⚠️ Nenhum dado encontrado para o período selecionado.")
            return
        
        # Preparar dados para gráficos
        df = pd.DataFrame([
            {
                'mes_ano': d['mes_ano'],
                'saldo_minutos': d['saldo'],
                'saldo_formatado': format_time(d['saldo']),
                'saldo_horas': d['saldo'] / 60
            }
            for d in detalhes
        ])
        
        # Gráficos - Layout vertical (um em cima do outro)
        st.subheader("📊 Gráficos")
        
        # Gráfico mensal por mês
        fig_monthly = create_monthly_chart(df)
        st.plotly_chart(fig_monthly, use_container_width=True)
        
        # Gráfico cumulativo
        fig_cumulative = create_cumulative_chart(df)
        st.plotly_chart(fig_cumulative, use_container_width=True)
        
        # Tabela detalhada
        st.subheader("📋 Detalhes por Mês")
        
        # Preparar DataFrame para exibição com cores - usar cache para evitar recálculos
        if 'display_df_cache' not in st.session_state or st.session_state.get('results_changed', False):
            display_df = df[['mes_ano', 'saldo_formatado', 'saldo_minutos']].copy()
            display_df['Status'] = display_df['saldo_minutos'].apply(
                lambda x: '🟢 Crédito' if x > 0 else '🔴 Débito' if x < 0 else '⚪ Neutro'
            )
            
            # Remover coluna auxiliar e renomear
            display_df = display_df[['mes_ano', 'saldo_formatado', 'Status']]
            display_df.columns = ['Mês/Ano', 'Saldo', 'Situação']
            
            # Resetar índice para começar com 1
            display_df.reset_index(drop=True, inplace=True)
            display_df.index = display_df.index + 1
            
            # Cache do DataFrame preparado
            st.session_state.display_df_cache = display_df
            st.session_state.results_changed = False
        
        # Usar DataFrame do cache para renderização estável
        cached_df = st.session_state.display_df_cache
        
        # Container para tabela sem altura fixa para evitar linhas vazias
        with st.container():
            st.dataframe(
                cached_df, 
                use_container_width=True
            )
        
        # Download do relatório
        st.subheader("📥 Download")
        report_content = download_report(df, total_minutos)
        
        st.download_button(
            label="📄 Baixar Relatório (TXT)",
            data=report_content,
            file_name=f"relatorio_banco_horas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    
    elif st.session_state.error_message:
        # === MODO ERRO ===
        st.markdown("---")  # Separador visual
        st.error(st.session_state.error_message)
        
        if st.session_state.error_details:
            st.error("💡 **Dicas para solucionar:**")
            for detalhe in st.session_state.error_details:
                st.write(detalhe)
        
        # Botão para tentar novamente
        if st.button("🔄 Tentar Novamente", type="secondary"):
            st.session_state.error_message = None
            st.session_state.error_details = None
            st.rerun()
    
    else:
        # === MODO INICIAL ===
        st.markdown("---")  # Separador visual
        st.info("""
        👋 **Bem-vindo à Calculadora de Banco de Horas!**
        
        **Como usar:**
        1. 🌐 Configure a URL da sua intranet na barra lateral
        2. 🔐 Digite suas credenciais de login
        3. 📅 Defina o período para cálculo
        4. 🚀 Clique em "Calcular Banco de Horas"
        
        **Compatibilidade:**
        - ✅ Funciona com qualquer intranet com layout similar
        - ✅ URLs automáticas: `/ControleAcesso/Seguranca/Login` e `/Horas/FolhaPonto/Relatorio`
        - ✅ Detecção automática de campos de login
        
        **Exemplos de URLs:**
        - `https://intranet.empresa.com`
        - `https://sistema.minhaempresa.com.br`
        - `intranet.outraempresa.com` (https:// será adicionado automaticamente)
        """)
        
        # Informações técnicas
        with st.expander("ℹ️ Informações Técnicas"):
            st.markdown("""
            **Tecnologias utilizadas:**
            - 🐍 Python 3.11
            - 🎨 Streamlit (Interface Web)
            - 📊 Plotly (Gráficos Interativos)
            - 🐳 Docker (Containerização)
            - 🌐 Requests + BeautifulSoup (Web Scraping)
            
            **Funcionalidades:**
            - 📊 Gráficos interativos por mês
            - 📈 Evolução cumulativa do saldo
            - 📋 Tabela detalhada com cores
            - 📥 Download de relatório
            - 🔄 Processamento em tempo real
            - 🛡️ Login seguro com feedback visual
            """)
    
    # Rodapé
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 20px; color: #666; font-size: 14px;">
        <p>💻 <strong>Developed by Paulo Cruz</strong> 🚀</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
