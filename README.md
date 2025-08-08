# Calculadora de Banco de Horas - Genérica

**Versão 1.0 - Modular + Docker** 🐳

Aplicação para calcular banco de horas de intranets com interface web moderna e arquitetura modular.

## 🚀 Execução Rápida

### 🐳 Docker (Recomendado)
```bash
./docker_run.sh
# Acesse: http://localhost:8501
```

### 💻 Execução Local
```bash
pip install -r requirements.txt
streamlit run src/app/app_streamlit.py
# OU usar o script principal
python main.py
```

## �️ Estrutura do Projeto

```
intranet-hours-calc/
├── 🎨 Código Fonte
│   └── src/
│       ├── app/                     # Módulos Python da aplicação
│       │   ├── __init__.py
│       │   ├── app_streamlit.py     # Interface Streamlit principal
│       │   ├── banco_horas.py       # Módulo de web scraping (BancoHorasAdvanced)
│       │   └── utils.py             # Funções utilitárias e gráficos
│       └── styles/
│           └── main.css             # CSS externo organizados
├── 🐳 Docker & Deploy
│   ├── Dockerfile                   # Container da aplicação
│   ├── docker-compose.yml           # Orquestração de serviços
│   ├── docker_run.sh               # Script de execução rápida
│   └── build.sh                    # Script de build
├── 📦 Configuração
│   ├── main.py                     # Script principal de execução
│   └── requirements.txt            # Dependências Python
└── 📖 Documentação
    └── README.md                   # Esta documentação
```

## 🌐 Compatibilidade

Funciona com intranets que tenham:
- URLs: `/ControleAcesso/Seguranca/Login` e `/Horas/FolhaPonto/Relatorio`  
- HTML com classes `text-primary` e `text-danger`

**Exemplos suportados:**
- `https://intranet.empresa.com`
- `intranet.empresa.com` (https:// adicionado automaticamente)

## ✨ Principais Funcionalidades

- ✅ **Arquitetura modular**: Separação clara de responsabilidades
- ✅ **Interface web moderna**: Streamlit com CSS externo
- ✅ **Gráficos interativos**: Plotly com barras mensais + evolução cumulativa
- ✅ **Métricas visuais**: Saldo final com cores automáticas  
- ✅ **Tabela detalhada**: Status por mês com ordenação
- ✅ **Download de relatórios**: Arquivos completos com timestamp
- ✅ **Design responsivo**: Mobile e desktop
- ✅ **Barra de progresso**: Feedback visual em tempo real
- ✅ **Docker**: Containerização completa
- ✅ **Multi-estratégia**: 3 métodos de parsing HTML
- ✅ **Retry inteligente**: Até 3 tentativas por mês
- ✅ **100% genérico**: Sem referências específicas

## 🎯 Como Usar

1. Execute `./docker_run.sh` ou `streamlit run src/app/app_streamlit.py` ou `python main.py`
2. Acesse http://localhost:8501
3. Configure URL da intranet na sidebar
4. Digite credenciais e período desejado
5. Visualize gráficos, métricas e download do relatório

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| **Erro de login** | Verifique credenciais e URL da intranet |
| **Timeout/Conexão** | Teste conexão com intranet manualmente |
| **Docker não inicia** | `docker-compose logs -f` para ver logs |
| **Progresso travado** | Aguarde, pode levar alguns minutos por mês |
| **URL inválida** | Sistema formata automaticamente URLs |

## 📚 Dependências

```txt
requests==2.31.0           # HTTP requests
beautifulsoup4==4.12.2     # HTML parsing  
python-dateutil==2.8.2     # Date utilities
streamlit==1.28.1          # Web interface
plotly==5.17.0             # Interactive charts
pandas==2.1.3              # Data manipulation
lxml==4.9.3                # XML/HTML parser
```

## 🔧 Comandos Úteis

```bash
# Docker
./docker_run.sh              # Executar com Docker
docker-compose up -d         # Executar em background
docker-compose logs -f       # Ver logs em tempo real
docker-compose down          # Parar aplicação

# Local
streamlit run src/app/app_streamlit.py --server.port 8501
python main.py               # Script principal alternativo
pip install -r requirements.txt
```

## ☕ Apoie o Projeto

Se este projeto te ajudou, considere fazer uma doação via PIX:

```
🔑 PIX: 688afa4e-252a-4901-81c6-8c130ce5f4b3
```

**Por que doar?**
- 💻 Desenvolvimento contínuo e novas funcionalidades  
- 🐛 Correções de bugs e manutenção ativa
- 📚 Documentação e tutoriais atualizados
- 🚀 Suporte para implementação

## 🤝 Contribuição

Projeto open source (MIT) - adapte para sua intranet e contribua!

---

**🎉 Setup em 1 comando • Arquitetura modular • Gráficos interativos**
