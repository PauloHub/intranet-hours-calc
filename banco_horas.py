#!/usr/bin/env python3
"""
Classe principal para cálculo de banco de horas
Contém toda a lógica de web scraping e processamento
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time


class BancoHorasAdvanced:
    def __init__(self, base_url):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = base_url
        self.login_url = f"{self.base_url}/ControleAcesso/Seguranca/Login?ReturnUrl=%2fHoras%2fFolhaPonto%2fRelatorio"
        self.relatorio_url = f"{self.base_url}/Horas/FolhaPonto/Relatorio"
        
    def fazer_login(self, usuario, senha):
        """Faz login no sistema com verificações adicionais"""
        try:
            # Acessar página de login
            login_page = self.session.get(self.login_url, timeout=10)
            soup = BeautifulSoup(login_page.content, 'html.parser')
            
            # Encontrar formulário de login
            form = soup.find('form')
            if not form:
                return False
            
            # Coletar campos ocultos
            login_data = {}
            for inp in soup.find_all('input', {'type': 'hidden'}):
                name = inp.get('name')
                value = inp.get('value')
                if name and value:
                    login_data[name] = value
            
            # Encontrar nomes dos campos de usuário e senha
            user_field = soup.find('input', {'type': 'text'}) or soup.find('input', {'name': re.compile(r'[Uu]ser|[Uu]suario|[Ll]ogin', re.I)})
            pass_field = soup.find('input', {'type': 'password'}) or soup.find('input', {'name': re.compile(r'[Pp]ass|[Ss]enha', re.I)})
            
            if user_field and pass_field:
                user_name = user_field.get('name', 'Login')
                pass_name = pass_field.get('name', 'Senha')
                login_data[user_name] = usuario
                login_data[pass_name] = senha
            else:
                # Fallback para nomes padrão
                login_data.update({
                    'Login': usuario,
                    'Senha': senha,
                    'username': usuario,
                    'password': senha,
                    'user': usuario,
                    'pass': senha
                })
            
            # Fazer login
            response = self.session.post(self.login_url, data=login_data, timeout=10)
            
            # Verificar sucesso
            return self._verificar_login_sucesso(response)
                
        except Exception:
            return False
    
    def _verificar_login_sucesso(self, response):
        """Verifica se o login foi bem-sucedido"""
        # Verificações múltiplas
        url_ok = "login" not in response.url.lower()
        status_ok = response.status_code == 200
        
        # Verificar conteúdo da página
        texto_pagina = response.text.lower()
        tem_erro = any([
            "erro de login" in texto_pagina,
            "credenciais inválidas" in texto_pagina,
            "usuário ou senha" in texto_pagina,
            "senha incorreta" in texto_pagina,
            "acesso negado" in texto_pagina
        ])
        
        sucesso = status_ok and url_ok and not tem_erro
        return sucesso
    
    def extrair_horas_avancado(self, html_content):
        """Extração mais robusta dos dados de horas"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        funcionario_deve_minutos = 0
        empresa_deve_minutos = 0
        
        # Calcular folgas a compensar
        folgas_compensar_minutos = self._calcular_folgas_compensar(soup)
        
        # Múltiplas estratégias de busca
        estrategias = [
            self._buscar_por_classe,
            self._buscar_por_texto,
            self._buscar_por_estrutura_tabela
        ]
        
        for estrategia in estrategias:
            func_deve, emp_deve = estrategia(soup, folgas_compensar_minutos)
            if func_deve > 0 or emp_deve > 0:
                funcionario_deve_minutos = func_deve
                empresa_deve_minutos = emp_deve
                break
        
        return empresa_deve_minutos - funcionario_deve_minutos
    
    def _calcular_folgas_compensar(self, soup):
        """Calcula o total de folgas a compensar em minutos"""
        # Buscar por "<td>folga a compensar</td>" (case insensitive)
        folgas_encontradas = soup.find_all('td', string=re.compile(r'folga\s+a\s+compensar', re.I))
        
        if folgas_encontradas:
            quantidade_folgas = len(folgas_encontradas)
            # Cada folga = 8 horas = 480 minutos
            folgas_minutos = quantidade_folgas * 8 * 60
            return folgas_minutos
        
        return 0
    
    def _aplicar_folgas_compensadas(self, func_deve, emp_deve, folgas_compensar_minutos):
        """Aplica a lógica de folgas compensadas com transferência entre func_deve e emp_deve"""
        
        # Cenário 1: Funcionário deve horas (func_deve > 0)
        if func_deve > 0:
            # Subtrair folgas do que o funcionário deve
            func_deve_resultado = func_deve - folgas_compensar_minutos
            
            if func_deve_resultado < 0:
                # Funcionário deveria mais folgas do que deve horas
                # Transferir o excesso para empresa deve (positivo)
                excesso = abs(func_deve_resultado)
                func_deve = 0
                emp_deve = emp_deve + excesso
            else:
                # Funcionário ainda deve horas após compensar folgas
                func_deve = func_deve_resultado
        
        # Cenário 2: Empresa deve horas (emp_deve > 0)
        elif emp_deve > 0:
            # Somar folgas ao que a empresa deve
            emp_deve_resultado = emp_deve + folgas_compensar_minutos
            emp_deve = emp_deve_resultado
        
        # Cenário 3: Nenhum dos dois deve (valores zerados)
        # Neste caso, as folgas compensadas vão para empresa deve
        elif func_deve == 0 and emp_deve == 0:
            emp_deve = folgas_compensar_minutos
            
        return func_deve, emp_deve
    
    def _buscar_por_classe(self, soup, folgas_compensar_minutos=0):
        """Busca usando classes CSS"""
        func_deve = 0
        emp_deve = 0
        
        # Funcionário deve (text-primary)
        tr_primary = soup.find('tr', class_='text-primary')
        if tr_primary:
            func_deve = self._extrair_tempo_da_linha(tr_primary, 'funcionário deve')
        
        # Empresa deve (text-danger)
        tr_danger = soup.find('tr', class_='text-danger')
        if tr_danger:
            emp_deve = self._extrair_tempo_da_linha(tr_danger, 'empresa deve')
        
        # Aplicar lógica de folgas compensadas com transferência
        if folgas_compensar_minutos > 0:
            func_deve, emp_deve = self._aplicar_folgas_compensadas(func_deve, emp_deve, folgas_compensar_minutos)
            
        return func_deve, emp_deve
    
    def _buscar_por_texto(self, soup, folgas_compensar_minutos=0):
        """Busca por texto específico"""
        func_deve = 0
        emp_deve = 0
        
        # Procurar por qualquer elemento contendo os textos
        for elemento in soup.find_all(string=re.compile(r'funcionário deve', re.I)):
            tr = elemento.find_parent('tr')
            if tr:
                func_deve = self._extrair_tempo_da_linha(tr, 'funcionário deve')
                break
        
        for elemento in soup.find_all(string=re.compile(r'empresa deve', re.I)):
            tr = elemento.find_parent('tr')
            if tr:
                emp_deve = self._extrair_tempo_da_linha(tr, 'empresa deve')
                break
        
        # Aplicar lógica de folgas compensadas com transferência
        if folgas_compensar_minutos > 0:
            func_deve, emp_deve = self._aplicar_folgas_compensadas(func_deve, emp_deve, folgas_compensar_minutos)
                
        return func_deve, emp_deve
    
    def _buscar_por_estrutura_tabela(self, soup, folgas_compensar_minutos=0):
        """Busca percorrendo toda a estrutura da tabela"""
        func_deve = 0
        emp_deve = 0
        
        for tr in soup.find_all('tr'):
            texto_linha = tr.get_text().lower()
            
            if 'funcionário deve' in texto_linha:
                func_deve = self._extrair_tempo_da_linha(tr, 'funcionário deve')
            elif 'empresa deve' in texto_linha:
                emp_deve = self._extrair_tempo_da_linha(tr, 'empresa deve')
        
        # Aplicar lógica de folgas compensadas com transferência
        if folgas_compensar_minutos > 0:
            func_deve, emp_deve = self._aplicar_folgas_compensadas(func_deve, emp_deve, folgas_compensar_minutos)
                
        return func_deve, emp_deve
    
    def _extrair_tempo_da_linha(self, tr, tipo_busca):
        """Extrai o tempo de uma linha da tabela"""
        if not tr:
            return 0
            
        # Procurar por padrões de tempo (HH:MM)
        texto_completo = tr.get_text()
        padrao_tempo = re.findall(r'\b(\d{1,3}):(\d{2})\b', texto_completo)
        
        if padrao_tempo:
            # Pegar o último tempo encontrado (geralmente é o valor que queremos)
            horas, minutos = map(int, padrao_tempo[-1])
            tempo_minutos = horas * 60 + minutos
            return tempo_minutos
            
        return 0
    
    def processar_mes_com_retry(self, mes_ano, max_tentativas=3):
        """Processa um mês com tentativas múltiplas"""
        for tentativa in range(max_tentativas):
            try:
                url_mes = f"{self.relatorio_url}?mesAno={quote(mes_ano)}"
                
                response = self.session.get(url_mes, timeout=15)
                
                if response.status_code == 200:
                    saldo = self.extrair_horas_avancado(response.content)
                    return saldo
                    
            except Exception:
                if tentativa < max_tentativas - 1:
                    time.sleep(2)  # Aguardar antes de tentar novamente
        
        return 0
    
    def minutos_para_tempo(self, minutos):
        """Converte minutos para formato HH:MM ou em minutos se menor que 1 hora"""
        if minutos == 0:
            return "00:00"
        
        # Se for menor que 60 minutos (menos de 1 hora), exibir em minutos
        if abs(minutos) < 60:
            sinal = "-" if minutos < 0 else "+"
            return f"{sinal}{abs(minutos)}min"
        
        # Caso contrário, exibir em formato HH:MM
        horas = abs(minutos) // 60
        mins = abs(minutos) % 60
        sinal = "-" if minutos < 0 else "+"
        return f"{sinal}{horas:02d}:{mins:02d}"
    
    def gerar_lista_meses(self, mes_inicio, ano_inicio, mes_fim, ano_fim):
        """Gera lista de meses no formato MM/YYYY"""
        meses = []
        data_atual = datetime(ano_inicio, mes_inicio, 1)
        data_fim = datetime(ano_fim, mes_fim, 1)
        
        while data_atual <= data_fim:
            mes_ano = data_atual.strftime("%m/%Y")
            meses.append(mes_ano)
            data_atual += relativedelta(months=1)
        
        return meses
    
    def calcular_banco_horas(self, mes_inicio, ano_inicio, mes_fim, ano_fim, progress_callback=None):
        """Calcula o banco de horas total no período especificado"""
        meses = self.gerar_lista_meses(mes_inicio, ano_inicio, mes_fim, ano_fim)
        
        total_minutos = 0
        detalhes = []
        total_meses = len(meses)
        
        for i, mes_ano in enumerate(meses):
            saldo_mes = self.processar_mes_com_retry(mes_ano)
            total_minutos += saldo_mes
            detalhes.append({
                'mes_ano': mes_ano,
                'saldo': saldo_mes,
                'saldo_formatado': self.minutos_para_tempo(saldo_mes)
            })
            
            # Callback de progresso se fornecido
            if progress_callback:
                mes_atual = i + 1
                progress_callback(mes_atual, total_meses, mes_ano)
            
            # Pausa pequena entre requisições
            time.sleep(0.5)
        
        return total_minutos, detalhes
