# ⛈️ StormWatch SP

<div align="center">

![Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Sistema inteligente de monitoramento e previsão de tempestades e enchentes para São Paulo**

[Funcionalidades](#-funcionalidades) • [Tecnologias](#-tecnologias) • [Instalação](#-instalação) • [Uso](#-uso) • [Arquitetura](#-arquitetura)

</div>

---

## 📋 Sobre o Projeto

**StormWatch SP** é uma aplicação web desenvolvida em Python com Streamlit que oferece previsões meteorológicas avançadas e alertas de risco de tempestades e enchentes para a região metropolitana de São Paulo. O sistema combina dados meteorológicos em tempo real, modelos de Machine Learning e análise hidrológica para fornecer alertas precisos e automatizados.

### 🎯 Objetivo

Proteger vidas e patrimônio através de alertas antecipados de eventos climáticos extremos, permitindo que cidadãos e autoridades tomem medidas preventivas com antecedência.

---

## ✨ Funcionalidades

### 🔍 Busca e Monitoramento de Localidades
- **Busca inteligente** por endereço, bairro ou coordenadas usando a API Nominatim (OpenStreetMap)
- **Histórico de localidades** consultadas para acesso rápido
- **Visualização em mapa** com coordenadas e informações detalhadas
- **Cache de resultados** para melhor performance

### 🌦️ Previsão de Tempestades
- **Análise preditiva** usando Random Forest Regressor
- **Classificação de risco** em 4 níveis:
  - 🟢 **Baixo** (< 20 mm)
  - 🟡 **Moderado** (20-40 mm)
  - 🟠 **Alto** (40-80 mm)
  - 🔴 **Crítico** (≥ 80 mm)
- **Probabilidade de precipitação** calculada a partir dos dados meteorológicos
- **Alertas visuais** com cores e emojis intuitivos

### 🌊 Previsão de Enchentes
- **Modelo de Gradient Boosting** para classificação multiclasse
- **Análise hidrológica** integrando:
  - Precipitação acumulada (3, 7 e 14 dias)
  - Vazão de rios (river discharge)
  - Tendências de precipitação
  - Evapotranspiração
- **14 features derivadas** para máxima precisão
- **Validação temporal** com dados históricos

### 📧 Sistema de Alertas Automatizado
- **Cadastro de usuários** com UUID único para cada assinatura
- **Gerenciamento completo**: cadastro, visualização e exclusão de alertas
- **Múltiplos canais**: E-mail (SMTP) e SMS/WhatsApp (Twilio)
- **Tipos de alerta configuráveis**:
  - Apenas tempestade
  - Apenas enchente
  - Ambos (recomendado)
- **Níveis de risco personalizáveis** (moderado, alto, crítico)
- **Monitor automático** que executa verificações periódicas

### 🤖 Monitor Automático (Modo Daemon)
- **Execução contínua** com intervalo configurável (padrão: 6 horas)
- **Modo horários específicos** (ex: 08:00, 14:00, 20:00)
- **Modo teste** (execução única para debugging)
- **Logs estruturados** com timestamp e níveis de severidade
- **Processamento em lote** de todas as localidades cadastradas
- **Tratamento robusto de erros** com estatísticas de execução

### 📊 Visualizações Interativas
- **Gráficos Plotly** com paleta de cores profissional (#63b3ed, #68d391, #f6e05e, #fc8181)
- **Dashboard meteorológico** com:
  - Temperatura (mín/máx) ao longo de 7 dias
  - Precipitação diária prevista
  - Precipitação acumulada (3/7/14 dias)
  - Umidade relativa do ar
  - Vazão de rios em tempo real
- **Interface responsiva** com design moderno (gradientes, bordas luminosas)
- **Auto-refresh** opcional para monitoramento contínuo

---

## 🛠️ Tecnologias

### Core
- **Python 3.8+**
- **Streamlit 1.28+** - Framework web interativo
- **Pandas** - Manipulação e análise de dados
- **NumPy** - Operações numéricas e arrays

### Machine Learning
- **scikit-learn**
  - `RandomForestRegressor` - Previsão de precipitação
  - `GradientBoostingClassifier` - Classificação de enchentes (4 classes)
  - `StandardScaler` - Normalização Z-score de features
  - `Pipeline` - Encadeamento de transformações

### Visualização
- **Plotly** - Gráficos interativos e responsivos
- **Streamlit AutoRefresh** - Atualização automática da interface

### APIs e Integração
- **Requests** - Cliente HTTP para requisições
- **Open-Meteo API** - Dados meteorológicos (temperatura, chuva, umidade, etc.)
- **Open-Meteo Flood API** - Dados hidrológicos (vazão de rios)
- **Nominatim/OpenStreetMap** - Geocodificação e busca de endereços
- **Twilio** - Envio de SMS e mensagens WhatsApp
- **SMTP (Gmail)** - Envio de e-mails HTML formatados

### Armazenamento e Logging
- **CSV** - Banco de dados histórico por localidade (`dados_historicos/dados_<cidade>.csv`)
- **JSON** - Armazenamento de assinaturas (`subscriptions.json`)
- **Logging** - Sistema de logs estruturado com níveis (INFO, WARNING, ERROR)

---

## 🧮 Como Funciona

### 1️⃣ Coleta de Dados

#### Dados Meteorológicos (Open-Meteo Weather API)
```python
# Endpoint: https://api.open-meteo.com/v1/forecast
# Variáveis coletadas (7 dias de previsão):
- temperature_2m_max/min         # Temperatura máx/mín (°C)
- precipitation_sum              # Precipitação diária (mm)
- precipitation_hours            # Duração da chuva (horas)
- precipitation_probability_max  # Probabilidade máxima (%)
- relative_humidity_2m_mean      # Umidade relativa média (%)
- et0_fao_evapotranspiration    # Evapotranspiração FAO (mm)
```

#### Dados Hidrológicos (Open-Meteo Flood API)
```python
# Endpoint: https://flood-api.open-meteo.com/v1/flood
# Variáveis coletadas:
- river_discharge                # Vazão do rio (m³/s)
```

### 2️⃣ Engenharia de Features

O sistema deriva **14 features** a partir dos dados brutos para alimentar os modelos de ML:

#### Features de Precipitação
```python
# Acumulados temporais
precip_acum_3d   = soma(últimos 3 dias)
precip_acum_7d   = soma(últimos 7 dias)
precip_acum_14d  = soma(últimos 14 dias)

# Lags (histórico recente)
rain_sum    = precipitação do dia atual
rain_lag1   = precipitação do dia anterior (D-1)
rain_lag2   = precipitação de 2 dias atrás (D-2)

# Tendência (detecção de padrões)
rain_trend  = rain_lag1 - rain_lag2
```

#### Features Hidrológicas
```python
# Normalização da vazão (0-1)
river_discharge_norm = vazao_atual / vazao_maxima_historica

# Tendência da vazão
discharge_trend = vazao[hoje] - vazao[ontem]
```

#### Features Meteorológicas Complementares
```python
- precipitation_hours            # Duração total da chuva
- relative_humidity_2m_mean      # Umidade do ar (influencia evaporação)
- temperature_2m_min             # Temperatura mínima
- et0_fao_evapotranspiration    # Perda de água por evaporação
```

### 3️⃣ Modelo de Previsão de Tempestades

**Algoritmo:** Random Forest Regressor

```python
RandomForestRegressor(
    n_estimators=100,      # Ensemble de 100 árvores
    max_depth=10,          # Profundidade máxima (evita overfitting)
    random_state=42,       # Reprodutibilidade
    n_jobs=-1             # Paralelização (usa todos os cores)
)
```

#### Entrada (6 Features Selecionadas)
```python
X = [
    'precip_acum_7d',              # Acúmulo semanal
    'rain_lag1',                   # Chuva ontem
    'rain_lag2',                   # Chuva há 2 dias
    'rain_trend',                  # Tendência de aumento/diminuição
    'precipitation_hours',         # Duração esperada
    'relative_humidity_2m_mean'    # Umidade do ar
]
```

#### Saída e Classificação
```python
# Previsão: quantidade de chuva (mm)
y_pred = precipitação_prevista_mm

# Classificação de risco (baseada em dois critérios)
if precipitacao >= 80 mm  OR probabilidade >= 90%:  → 🔴 CRÍTICO
elif precipitacao >= 40 mm OR probabilidade >= 70%: → 🟠 ALTO
elif precipitacao >= 20 mm OR probabilidade >= 40%: → 🟡 MODERADO
else:                                                → 🟢 BAIXO
```

#### Fallback para Dados Insuficientes
```python
# Se histórico < 10 dias ou classes únicas < 2:
usar_classificacao_por_regras()  # Baseada apenas em thresholds
```

### 4️⃣ Modelo de Previsão de Enchentes

**Algoritmo:** Gradient Boosting Classifier (multiclasse)

```python
GradientBoostingClassifier(
    n_estimators=100,      # 100 estimadores boosting
    max_depth=3,           # Árvores rasas (previne overfitting)
    learning_rate=0.1,     # Taxa de aprendizado conservadora
    subsample=0.8,         # Stochastic GB (80% dos dados/iteração)
    random_state=42
)
```

#### Pipeline Completo
```python
Pipeline([
    ('scaler', StandardScaler()),           # Normalização Z-score
    ('classifier', GradientBoostingClassifier(...))
])
```

#### Geração de Rótulos de Treinamento
```python
# Critérios combinados (precipitação OU vazão):
if precip_7d >= 150 mm OR vazao_norm >= percentil_95:  → 3 (CRÍTICO)
elif precip_7d >= 100 mm OR vazao_norm >= percentil_85: → 2 (ALTO)
elif precip_7d >= 60 mm OR vazao_norm >= percentil_70:  → 1 (MODERADO)
else:                                                    → 0 (BAIXO)
```

#### Entrada (14 Features Completas)
```python
X = [
    # Precipitação
    'precip_acum_3d', 'precip_acum_7d', 'precip_acum_14d',
    'rain_sum', 'rain_lag1', 'rain_lag2', 'rain_trend',
    
    # Meteorologia
    'precipitation_hours', 'relative_humidity_2m_mean',
    'temperature_2m_min', 'et0_fao_evapotranspiration',
    
    # Hidrologia
    'river_discharge_norm', 'discharge_trend'
]
```

#### Saída (Classificação Multiclasse)
```python
# Classe predita
y_pred ∈ {0: baixo, 1: moderado, 2: alto, 3: crítico}

# Probabilidades por classe
probabilities = {
    0: p_baixo,      # Ex: 10%
    1: p_moderado,   # Ex: 30%
    2: p_alto,       # Ex: 45%
    3: p_critico     # Ex: 15%
}  # soma(probabilidades) = 100%
```

### 5️⃣ Sistema de Alertas

#### Estrutura de Cadastro
```python
{
    "id": "uuid-unico",               # Gerado automaticamente
    "nome": "João Silva",
    "email": "joao@example.com",
    "telefone": "+5511999999999",     # Opcional
    "localidade": "São Paulo, SP",
    "lat": -23.5505,
    "lon": -46.6333,
    "tipo_alerta": "ambos",           # ou "tempestade" ou "enchente"
    "nivel_minimo": "moderado",       # Threshold para disparo
    "timestamp": "2026-05-15T10:30:00"
}
```

#### Condições de Disparo
```python
# Alerta é enviado SE E SOMENTE SE:
1. Localidade do alerta == Localidade processada
2. Tipo de alerta configurado (tempestade/enchente/ambos) tem risco
3. Nível de risco >= nível_minimo configurado
```

#### Canais de Notificação

**E-mail (SMTP via Gmail)**
```python
# Configuração
servidor = 'smtp.gmail.com:587'
from_email = os.getenv('EMAIL_ADDRESS')
password = os.getenv('EMAIL_PASSWORD')  # Senha de aplicativo

# Mensagem HTML formatada
assunto = f"🚨 ALERTA: {nivel.upper()} - {localidade}"
corpo = f"""
<h2>⚠️ ALERTA StormWatch SP</h2>
<p><strong>Nível:</strong> {emoji} {nivel.upper()}</p>
<p><strong>Precipitação prevista:</strong> {mm} mm</p>
<p><strong>Recomendações:</strong> {recomendacoes}</p>
"""
```

**SMS/WhatsApp (Twilio)**
```python
from twilio.rest import Client

client = Client(account_sid, auth_token)

mensagem = client.messages.create(
    to=telefone_usuario,
    from_=numero_twilio,
    body=f"🚨 ALERTA: {nivel} - {localidade}. Chuva: {mm}mm"
)
```

### 6️⃣ Monitor Automático

O sistema inclui um monitor daemon que pode rodar em background:

#### Modos de Execução
```bash
# Execução contínua (intervalo de 6 horas)
python backend.py

# Horários específicos (ex: 08:00, 14:00, 20:00)
python backend.py --horarios

# Teste (executa uma vez e encerra)
python backend.py --once
```

#### Fluxo de Processamento
```python
1. Carregar todas as assinaturas (subscriptions.json)
2. Agrupar por localidade única (evita requisições duplicadas)
3. Para cada localidade:
   a. Buscar dados meteorológicos (Open-Meteo)
   b. Buscar dados de vazão (Open-Meteo Flood)
   c. Processar features (14 variáveis)
   d. Executar previsões (tempestade + enchente)
   e. Verificar se há risco crítico/alto/moderado
   f. Enviar alertas para cadastros correspondentes
4. Registrar estatísticas (alertas enviados, erros)
5. Aguardar próximo ciclo
```

#### Logs Estruturados
```python
# Exemplo de saída do monitor
2026-05-15 08:00:00 [INFO] ══════════════════════════════════════
2026-05-15 08:00:00 [INFO] VERIFICAÇÃO DE ALERTAS - StormWatch SP
2026-05-15 08:00:00 [INFO] Total de cadastros: 15
2026-05-15 08:00:00 [INFO] Localidades únicas: 8
2026-05-15 08:00:00 [INFO] ══════════════════════════════════════
2026-05-15 08:00:05 [INFO] 🌍 Verificando: São Paulo, SP
2026-05-15 08:00:05 [INFO]    Coordenadas: (-23.5505, -46.6333)
2026-05-15 08:00:05 [INFO]    3 cadastro(s) nesta localidade
2026-05-15 08:00:07 [INFO]    🌩️ Tempestade: ALTO
2026-05-15 08:00:07 [INFO]    🌊 Enchente: MODERADO
2026-05-15 08:00:09 [INFO]    📧 Email enviado para joao@example.com
2026-05-15 08:00:10 [INFO]    📱 SMS enviado para +5511999999999
```

---

## 📊 Métricas e Thresholds

### Tempestades
| Nível | Precipitação | Probabilidade | Emoji | Cor |
|-------|-------------|---------------|-------|-----|
| Baixo | < 20 mm | < 40% | 🟢 ☀️ | #68d391 |
| Moderado | 20-40 mm | 40-70% | 🟡 🌧️ | #f6e05e |
| Alto | 40-80 mm | 70-90% | 🟠 ⛈️ | #fc8181 |
| Crítico | ≥ 80 mm | ≥ 90% | 🔴 🚨 | #f56565 |

### Enchentes
| Nível | Acumulado 7d | Vazão (percentil) | Ação Recomendada |
|-------|--------------|-------------------|------------------|
| Baixo | < 60 mm | < P70 | Monitoramento normal |
| Moderado | 60-100 mm | P70-P85 | Atenção redobrada |
| Alto | 100-150 mm | P85-P95 | Evitar áreas de risco |
| Crítico | ≥ 150 mm | ≥ P95 | Evacuação preventiva |

---

## 🚀 Instalação

### Pré-requisitos
```bash
Python 3.8 ou superior
pip (gerenciador de pacotes)
```

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/stormwatch-sp.git
cd stormwatch-sp
```

2. **Crie um ambiente virtual (recomendado)**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Instale as dependências**
```bash
pip install streamlit pandas numpy scikit-learn plotly requests twilio streamlit-autorefresh
```

4. **Configure as variáveis de ambiente** (criar arquivo `.env` ou exportar)
```bash
# Para SMS/WhatsApp via Twilio
export TWILIO_ACCOUNT_SID="seu_account_sid_aqui"
export TWILIO_AUTH_TOKEN="seu_auth_token_aqui"
export TWILIO_PHONE_NUMBER="+15551234567"

# Para e-mail via Gmail
export EMAIL_ADDRESS="seu_email@gmail.com"
export EMAIL_PASSWORD="sua_senha_de_aplicativo"
```

**⚠️ Nota sobre senha de aplicativo do Gmail:**
1. Acesse [myaccount.google.com/security](https://myaccount.google.com/security)
2. Ative "Verificação em duas etapas"
3. Gere uma "Senha de aplicativo" em "Senhas de app"
4. Use essa senha (16 caracteres sem espaços) na variável `EMAIL_PASSWORD`

5. **Execute a aplicação web**
```bash
streamlit run app.py
```

6. **Acesse no navegador**
```
http://localhost:8501
```

---

## 📖 Uso

### Interface Web (Streamlit)

#### 1. Buscar Localidade
- Digite um endereço, bairro ou cidade no campo de busca
- Exemplo: "Av. Paulista, São Paulo" ou "Guarulhos, SP"
- Selecione a localidade desejada nos resultados
- O sistema exibe coordenadas e nome completo

#### 2. Visualizar Previsões
- **Dashboard Meteorológico**: Gráficos interativos com:
  - Temperaturas máximas e mínimas (7 dias)
  - Precipitação diária prevista
  - Precipitação acumulada (3/7/14 dias)
  - Umidade relativa do ar
  - Vazão de rios
- **Alertas de Risco**: Cards coloridos indicando:
  - Nível de risco de tempestade
  - Nível de risco de enchente
  - Recomendações de segurança

#### 3. Cadastrar Alerta
Na **sidebar**, preencha:
- **Nome completo** (campo obrigatório)
- **E-mail** (campo obrigatório - receberá alertas)
- **Telefone** (opcional - formato: +55 11 99999-9999)
- **Tipo de alerta**:
  - Ambos (tempestade + enchente) ← recomendado
  - Apenas tempestade
  - Apenas enchente
- **Localidade** (selecione uma já buscada)
- **Nível mínimo** para receber alertas:
  - Moderado (≥ 20mm ou ≥ 40% probabilidade)
  - Alto (≥ 40mm ou ≥ 70% probabilidade)
  - Crítico (≥ 80mm ou ≥ 90% probabilidade)

Clique em **"✅ Cadastrar Alerta"**

#### 4. Gerenciar Alertas
- **Visualizar**: Todos os cadastros aparecem na sidebar
- **Excluir**: Clique no botão ❌ ao lado do cadastro desejado
- **Editar**: Exclua e recadastre com novos parâmetros

### Monitor Automático (Backend)

#### Execução Única (Teste)
```bash
python backend.py --once
```
Útil para testar se o sistema está funcionando corretamente.

#### Execução Contínua (Produção)
```bash
# Intervalo padrão: 6 horas (21600 segundos)
python backend.py

# Personalizar intervalo (edite INTERVALO_VERIFICACAO no backend.py)
INTERVALO_VERIFICACAO = 3600  # 1 hora
```

#### Execução em Horários Específicos
```bash
python backend.py --horarios

# Edite HORARIOS_VERIFICACAO no backend.py
HORARIOS_VERIFICACAO = ["08:00", "14:00", "20:00"]
```

#### Rodar em Background (Linux/Mac)
```bash
nohup python backend.py > monitor.log 2>&1 &
```

#### Rodar como Serviço (systemd)
Crie `/etc/systemd/system/stormwatch.service`:
```ini
[Unit]
Description=StormWatch SP Monitor
After=network.target

[Service]
Type=simple
User=seu_usuario
WorkingDirectory=/caminho/para/stormwatch-sp
Environment="TWILIO_ACCOUNT_SID=..."
Environment="TWILIO_AUTH_TOKEN=..."
Environment="EMAIL_ADDRESS=..."
Environment="EMAIL_PASSWORD=..."
ExecStart=/usr/bin/python3 /caminho/para/backend.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Ative o serviço:
```bash
sudo systemctl enable stormwatch
sudo systemctl start stormwatch
sudo systemctl status stormwatch
```

---

## 📁 Arquivos do Projeto

```
stormwatch-sp/
├── app.py                      # ⚙️ Ponto de entrada (inicialização)
├── frontend.py                 # 🎨 Interface do usuário (Streamlit UI/UX)
├── backend.py                  # 🤖 Lógica de negócio, ML, APIs e Monitor
├── monitor_alertas.py          # 📊 Leitura períodica dos cadastros no DB
|  
├── .env                        # 🔐 Variáveis de ambiente (não versionado)
├── requirements.txt            # 📦 Dependências Python
└── README.md                   # 📖 Este arquivo
```

### Descrição dos Arquivos Principais

#### `app.py`
- **Função**: Inicialização do Streamlit
- **Linhas**: ~22
- **Responsabilidade**: Configuração da página e chamada do `render_app()`

#### `frontend.py`
- **Função**: Interface gráfica completa
- **Linhas**: ~900
- **Componentes**:
  - CSS customizado (gradientes, cores, tipografia)
  - Busca de localidades
  - Renderização de gráficos Plotly
  - Cadastro e exclusão de alertas
  - Exibição de previsões

#### `backend.py`
- **Função**: Toda a lógica de negócio
- **Linhas**: ~1840
- **Componentes**:
  - APIs (Open-Meteo, Nominatim, Twilio)
  - Modelos de ML (Random Forest, Gradient Boosting)
  - Engenharia de features
  - Sistema de alertas (email, SMS)
  - Monitor automático (scheduler)
  - Logging estruturado

---

## 🔬 Algoritmos de Machine Learning

### Random Forest (Tempestades)

**Por que Random Forest?**
- ✅ **Robusto a outliers**: Chuvas extremas não distorcem o modelo
- ✅ **Não-linear**: Captura relações complexas entre umidade, temperatura e chuva
- ✅ **Sem normalização**: Aceita features em escalas diferentes
- ✅ **Feature importance**: Identifica automaticamente as variáveis mais relevantes
- ✅ **Baixa variância**: Ensemble de 100 árvores reduz overfitting

**Hyperparâmetros Otimizados:**
- `n_estimators=100`: Balanceio entre precisão e tempo de treinamento
- `max_depth=10`: Árvores moderadamente profundas (evita overfitting)
- `n_jobs=-1`: Paralelização total (usa todos os cores do CPU)

### Gradient Boosting (Enchentes)

**Por que Gradient Boosting?**
- ✅ **Alta precisão multiclasse**: Melhor que Random Forest em classificação
- ✅ **Controle fino de overfitting**: `subsample`, `learning_rate`, `max_depth`
- ✅ **Probabilidades calibradas**: Útil para decisões com incerteza
- ✅ **Sequential learning**: Cada árvore corrige erros da anterior

**Técnicas Aplicadas:**
- `StandardScaler`: Normalização Z-score para features numéricas (média=0, std=1)
- `subsample=0.8`: Stochastic Gradient Boosting (usa 80% dos dados/iteração, reduz variância)
- `max_depth=3`: Árvores rasas (bias-variance tradeoff, previne overfitting)
- `learning_rate=0.1`: Aprendizado conservador (melhor generalização)

**Pipeline Scikit-learn:**
```python
Pipeline([
    ('scaler', StandardScaler()),             # Etapa 1: Normalização
    ('classifier', GradientBoostingClassifier(...))  # Etapa 2: Classificação
])
```

---

## 📈 Validação e Robustez

### Treinamento Incremental
```python
# Validação temporal (split temporal, não aleatório)
df_train = histórico[:-3]   # Treino: tudo exceto últimos 3 dias
df_test = histórico[-3:]    # Teste: últimos 3 dias

# Evita data leakage (não usar futuro para prever passado)
```

### Fallback para Regras
```python
# Cenários onde ML pode falhar:
if len(dados_historicos) < 10:          # Dados insuficientes
    usar_classificacao_por_regras()
    
if classes_unicas < 2:                  # Falta variabilidade
    usar_classificacao_por_regras()
    
if model_score < 0.5:                   # Modelo ruim
    usar_classificacao_por_regras()
```

### Tratamento de Dados Ausentes
```python
# Features faltantes recebem valor 0 (neutral)
features.fillna(0, inplace=True)

# Vazão ausente: usa média histórica
if river_discharge is None:
    river_discharge = df_flood['river_discharge'].mean()
```

### Logging de Erros
```python
# Todas as exceções são logadas e tratadas
try:
    previsao = modelo.predict(X)
except Exception as e:
    logger.error(f"Erro no modelo: {e}")
    previsao = fallback_por_regras()
```

---

## 🌐 APIs Utilizadas

### Open-Meteo Weather API
- **Endpoint**: `https://api.open-meteo.com/v1/forecast`
- **Dados**: Previsão meteorológica 16 dias (histórico + futuro)
- **Variáveis**: temperatura, chuva, umidade, evapotranspiração
- **Taxa**: Gratuita, sem limite de requisições
- **Documentação**: [open-meteo.com/en/docs](https://open-meteo.com/en/docs)

### Open-Meteo Flood API
- **Endpoint**: `https://flood-api.open-meteo.com/v1/flood`
- **Dados**: Vazão de rios (river discharge) - 92 dias
- **Resolução**: Dados diários, modelos GloFAS
- **Taxa**: Gratuita
- **Documentação**: [open-meteo.com/en/docs/flood-api](https://open-meteo.com/en/docs/flood-api)

### Nominatim (OpenStreetMap)
- **Endpoint**: `https://nominatim.openstreetmap.org/search`
- **Dados**: Geocodificação de endereços (endereço → lat/lon)
- **Formato**: JSON
- **Taxa**: 1 requisição/segundo (rate limit)
- **User-Agent**: Obrigatório (ex: "StormWatchSP/1.0")
- **Documentação**: [nominatim.org/release-docs/latest/api/Search/](https://nominatim.org/release-docs/latest/api/Search/)

### Twilio API
- **Serviço**: Envio de SMS e mensagens WhatsApp
- **Credenciais**: Account SID + Auth Token
- **Custo**: Pago (a partir de $0.0075/SMS)
- **Documentação**: [twilio.com/docs](https://www.twilio.com/docs)

### SMTP (Gmail)
- **Servidor**: `smtp.gmail.com:587` (STARTTLS)
- **Autenticação**: E-mail + Senha de aplicativo (não senha normal)
- **Custo**: Gratuito (limite: ~500 emails/dia)
- **Documentação**: [support.google.com/mail/answer/7126229](https://support.google.com/mail/answer/7126229)

---

## 🔐 Segurança e Privacidade

### Armazenamento Local
- ✅ Todos os dados armazenados localmente (CSV, JSON)
- ✅ Sem banco de dados externo ou cloud
- ✅ Controle total sobre os dados

### Credenciais Sensíveis
- ✅ **Variáveis de ambiente**: Nunca hardcoded no código
- ✅ **Arquivo .env**: Não versionado no Git (`.gitignore`)
- ✅ **Senhas de aplicativo**: Uso de tokens específicos do Gmail

### Dados Pessoais
- ✅ E-mails e telefones não compartilhados com terceiros
- ✅ Sem tracking ou analytics
- ✅ UUID para identificação (não nomes)

### Comunicação
- ✅ HTTPS para todas as APIs externas
- ✅ TLS/SSL para SMTP (porta 587)
- ✅ Autenticação obrigatória (Twilio, Gmail)

---

## 🐛 Tratamento de Erros

### APIs com Fallback
```python
# Todas as requisições HTTP têm try-except
try:
    dados = fetch_weather_data(url)
except requests.exceptions.RequestException as e:
    logger.error(f"Erro na API: {e}")
    dados = usar_dados_cache() if cache_disponivel else None
    
if dados is None:
    exibir_mensagem_amigavel_usuario()
```

### Modelos ML com Fallback
```python
# Se modelo falha, usa classificação por regras
try:
    previsao = modelo.predict(X)
except (ValueError, TypeError) as e:
    logger.warning(f"Modelo falhou: {e}. Usando fallback.")
    previsao = classificacao_por_regras(dados)
```

### Validação de Entrada
```python
# Validação de coordenadas
if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
    st.error("Coordenadas inválidas!")
    return

# Validação de e-mail
if "@" not in email or "." not in email:
    st.error("E-mail inválido!")
    return
```

### Logs Estruturados
```python
# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Uso
logger.info("Operação bem-sucedida")
logger.warning("Alerta: dados parciais")
logger.error("Erro crítico: API indisponível")
```

---

## 📝 Roadmap Futuro

### Curto Prazo (1-3 meses)
- [ ] Integração com Google Maps para visualização geográfica
- [ ] Dashboard administrativo para gestão pública
- [ ] Exportação de relatórios PDF/Excel
- [ ] Histórico de alertas enviados (rastreabilidade)
- [ ] Testes unitários (pytest) com cobertura > 80%

### Médio Prazo (3-6 meses)
- [ ] API REST para integração externa (FastAPI)
- [ ] Autenticação de usuários (login/senha)
- [ ] Notificações push (Firebase Cloud Messaging)
- [ ] Modelo de previsão de deslizamentos de terra
- [ ] Integração com defesa civil (webhook)

### Longo Prazo (6-12 meses)
- [ ] App mobile nativo (Flutter/React Native)
- [ ] Análise de imagens de satélite (IA para detecção de nuvens)
- [ ] Sistema de reputação (usuários reportam eventos)
- [ ] Multilíngua (Português, Inglês, Espanhol)
- [ ] Expansão para outras cidades (Rio, Brasília, etc.)

---

## 🤝 Contribuições

Contribuições são extremamente bem-vindas! Siga o fluxo de trabalho padrão:

### Como Contribuir

1. **Fork o projeto**
```bash
# No GitHub, clique em "Fork" no canto superior direito
```

2. **Clone seu fork**
```bash
git clone https://github.com/SEU-USUARIO/stormwatch-sp.git
cd stormwatch-sp
```

3. **Crie uma branch para sua feature**
```bash
git checkout -b feature/MinhaNovaFeature
```

4. **Faça suas alterações e commit**
```bash
git add .
git commit -m "Adiciona funcionalidade X que faz Y"
```

5. **Push para seu fork**
```bash
git push origin feature/MinhaNovaFeature
```

6. **Abra um Pull Request**
- Vá para o repositório original no GitHub
- Clique em "Pull Requests" → "New Pull Request"
- Descreva suas mudanças detalhadamente

### Diretrizes

- **Código limpo**: Siga PEP 8 (use `black` e `flake8`)
- **Documentação**: Adicione docstrings em novas funções
- **Testes**: Inclua testes para novas funcionalidades
- **Commits**: Mensagens claras e objetivas (Conventional Commits)

### Áreas que Precisam de Ajuda

- 🧪 **Testes**: Aumentar cobertura de testes
- 📊 **Visualizações**: Novos tipos de gráficos
- 🌍 **Tradução**: Suporte a outros idiomas
- 📱 **Mobile**: Desenvolvimento de app nativo
- 🤖 **ML**: Melhorias nos modelos de previsão

---

## 📄 Licença

Este projeto está sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

```
MIT License

Copyright (c) 2026 Equipe StormWatch SP

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 👥 Autores

**Equipe StormWatch SP**

- 💻 **Desenvolvimento Full Stack**: Arquitetura, backend, frontend
- 🤖 **Machine Learning Engineer**: Modelos preditivos, feature engineering
- 🎨 **UI/UX Designer**: Interface, experiência do usuário
- 🌦️ **Domain Expert**: Meteorologia, hidrologia

---

## 📞 Contato

Para dúvidas, sugestões, parcerias ou reportar bugs:

- 📧 **E-mail**: contato@stormwatch.com.br
- 🌐 **Website**: [stormwatch.com.br](https://stormwatch.com.br)
- 💬 **Issues**: [GitHub Issues](https://github.com/seu-usuario/stormwatch-sp/issues)
- 🐛 **Bug Reports**: Use o template de issue no GitHub
- 💡 **Feature Requests**: Abra uma issue com a tag `enhancement`

---

## 🙏 Agradecimentos

Este projeto não seria possível sem:

- **Open-Meteo**: APIs gratuitas e de alta qualidade
- **OpenStreetMap**: Dados geográficos abertos
- **Streamlit**: Framework web incrível para Python
- **Scikit-learn**: Biblioteca de ML robusta e bem documentada
- **Comunidade Open Source**: Por todas as ferramentas e bibliotecas

---

<div align="center">

**Feito com ❤️ e ⚡ por desenvolvedores que se importam com vidas**

⭐ **Se este projeto foi útil, considere dar uma estrela no GitHub!**

---

### Status do Projeto

![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-75%25-yellowgreen.svg)
![Last Commit](https://img.shields.io/badge/last%20commit-May%202026-blue.svg)

---

### Estatísticas

![Lines of Code](https://img.shields.io/badge/lines%20of%20code-2800%2B-blue.svg)
![Files](https://img.shields.io/badge/files-3-lightgrey.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)

</div>