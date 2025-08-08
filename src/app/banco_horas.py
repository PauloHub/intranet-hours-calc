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
import random


class BancoHorasAdvanced:
    def __init__(self, base_url):
        self.session = requests.Session()
        
        # User-Agent mais realista e randomizado
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
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
                
        except requests.exceptions.Timeout:
            # Timeout específico
            return False
        except requests.exceptions.ConnectionError:
            # Erro de conexão
            return False
        except requests.exceptions.RequestException:
            # Outros erros de requisição
            return False
        except Exception:
            # Outros erros inesperados
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
        
        # Múltiplas estratégias de busca
        estrategias = [
            self._buscar_por_classe,
            self._buscar_por_texto,
            self._buscar_por_estrutura_tabela
        ]
        
        for estrategia in estrategias:
            func_deve, emp_deve = estrategia(soup)
            if func_deve > 0 or emp_deve > 0:
                funcionario_deve_minutos = func_deve
                empresa_deve_minutos = emp_deve
                break
        
        return empresa_deve_minutos - funcionario_deve_minutos
    
    def _buscar_por_classe(self, soup):
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
            
        return func_deve, emp_deve
    
    def _buscar_por_texto(self, soup):
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
                
        return func_deve, emp_deve
    
    def _buscar_por_estrutura_tabela(self, soup):
        """Busca percorrendo toda a estrutura da tabela"""
        func_deve = 0
        emp_deve = 0
        
        for tr in soup.find_all('tr'):
            texto_linha = tr.get_text().lower()
            
            if 'funcionário deve' in texto_linha:
                func_deve = self._extrair_tempo_da_linha(tr, 'funcionário deve')
            elif 'empresa deve' in texto_linha:
                emp_deve = self._extrair_tempo_da_linha(tr, 'empresa deve')
                
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
            try:
                horas, minutos = map(int, padrao_tempo[-1])
                
                # Validação básica: minutos não podem ser >= 60
                if minutos >= 60:
                    return 0
                
                tempo_minutos = horas * 60 + minutos
                return tempo_minutos
            except (ValueError, IndexError):
                return 0
            
        return 0
    
    def processar_mes_com_retry(self, mes_ano, max_tentativas=3):
        """Processa um mês com tentativas múltiplas e backoff exponencial"""
        for tentativa in range(max_tentativas):
            try:
                url_mes = f"{self.relatorio_url}?mesAno={quote(mes_ano)}"
                
                # Timeout progressivo
                timeout = 10 + (tentativa * 5)
                response = self.session.get(url_mes, timeout=timeout)
                
                if response.status_code == 200:
                    saldo = self.extrair_horas_avancado(response.content)
                    return saldo
                    
            except requests.exceptions.Timeout:
                if tentativa < max_tentativas - 1:
                    # Backoff exponencial: 2, 4, 8 segundos
                    wait_time = 2 ** (tentativa + 1)
                    time.sleep(wait_time)
            except requests.exceptions.RequestException:
                if tentativa < max_tentativas - 1:
                    wait_time = 2 ** (tentativa + 1)
                    time.sleep(wait_time)
            except Exception:
                if tentativa < max_tentativas - 1:
                    wait_time = 2 ** (tentativa + 1)
                    time.sleep(wait_time)
        
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
        
        # Proteção contra lista vazia de meses
        if not meses:
            return 0, []
        
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
