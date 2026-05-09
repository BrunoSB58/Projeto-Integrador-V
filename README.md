# ⛈️ StormWatch SP

<div align="center">

![Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Sistema inteligente de monitoramento e previsão de tempestades e enchentes para São Paulo**

[Funcionalidades](#-funcionalidades) • [Tecnologias](#-tecnologias) • [Instalação](#-instalação) • [Como Funciona](#-como-funciona) • [IA & Algoritmos](#-ia--algoritmos)

</div>

---

## 📋 Sobre o Projeto

**StormWatch SP** é uma aplicação web desenvolvida em Python com Streamlit que oferece previsões meteorológicas avançadas e alertas de risco de tempestades e enchentes para a região metropolitana de São Paulo. O sistema combina dados meteorológicos em tempo real, modelos de Machine Learning e análise hidrológica para fornecer alertas precisos e personalizados.

### 🎯 Objetivo

Proteger vidas e patrimônio através de alertas antecipados de eventos climáticos extremos, permitindo que cidadãos e autoridades tomem medidas preventivas com antecedência.

---

## ✨ Funcionalidades

### 🔍 Busca e Monitoramento de Localidades
- **Busca inteligente** por endereço, bairro ou coordenadas usando a API Nominatim (OpenStreetMap)
- **Histórico de localidades** consultadas para acesso rápido
- **Visualização em mapa** das coordenadas selecionadas

### 🌦️ Previsão de Tempestades
- **Análise preditiva** usando Random Forest Regressor
- **Classificação de risco** em 4 níveis:
  - 🟢 **Baixo** (< 20 mm)
  - 🟡 **Moderado** (20-40 mm)
  - 🟠 **Alto** (40-80 mm)
  - 🔴 **Crítico** (≥ 80 mm)
- **Probabilidade de precipitação** calculada a partir dos dados meteorológicos

### 🌊 Previsão de Enchentes
- **Modelo de Gradient Boosting** para classificação multiclasse
- **Análise hidrológica** integrando:
  - Precipitação acumulada (3, 7 e 14 dias)
  - Vazão de rios (river discharge)
  - Tendências de precipitação
  - Evapotranspiração
- **14 features** derivadas para máxima precisão

### 📧 Sistema de Alertas
- **Cadastro de usuários** com notificações personalizadas
- **Múltiplos canais**: E-mail e SMS/WhatsApp (via Twilio)
- **Tipos de alerta configuráveis**:
  - Apenas tempestade
  - Apenas enchente
  - Ambos
- **Níveis de risco** filtráveis (moderado, alto, crítico)

### 📊 Visualizações Interativas
- **Gráficos Plotly** com paleta de cores profissional
- **Dashboard meteorológico** com:
  - Temperatura (mín/máx)
  - Precipitação diária
  - Precipitação acumulada
  - Umidade relativa
  - Vazão de rios
- **Interface responsiva** e moderna

---

## 🛠️ Tecnologias

### Core
- **Python 3.8+**
- **Streamlit** - Framework web
- **Pandas** - Manipulação de dados
- **NumPy** - Operações numéricas

### Machine Learning
- **scikit-learn**
  - `RandomForestRegressor` - Previsão de chuva
  - `GradientBoostingClassifier` - Classificação de enchentes
  - `StandardScaler` - Normalização de features
  - `Pipeline` - Encadeamento de transformações

### Visualização
- **Plotly** - Gráficos interativos
- **Streamlit AutoRefresh** - Atualização automática

### APIs e Integração
- **Requests** - Requisições HTTP
- **Open-Meteo API** - Dados meteorológicos
- **Open-Meteo Flood API** - Dados hidrológicos
- **Nominatim/OpenStreetMap** - Geocodificação
- **Twilio** - Envio de SMS
- **SMTP** - Envio de e-mails

### Armazenamento
- **CSV** - Banco de dados local para histórico
- **JSON** - Armazenamento de assinaturas

---

## 🧮 Como Funciona

### 1️⃣ Coleta de Dados

#### Dados Meteorológicos (Open-Meteo)
```python
# Variáveis coletadas:
- temperature_2m_max/min       # Temperatura (°C)
- precipitation_sum            # Precipitação diária (mm)
- precipitation_hours          # Horas de chuva
- precipitation_probability_max # Probabilidade (%)
- relative_humidity_2m_mean    # Umidade relativa (%)
- et0_fao_evapotranspiration  # Evapotranspiração (mm)
```

#### Dados Hidrológicos (Open-Meteo Flood)
```python
- river_discharge              # Vazão do rio (m³/s)
```

### 2️⃣ Engenharia de Features

O sistema deriva **14 features** a partir dos dados brutos:

#### Features de Precipitação
```python
# Acumulados temporais
precip_acum_3d   = soma(chuva, 3 dias)
precip_acum_7d   = soma(chuva, 7 dias)
precip_acum_14d  = soma(chuva, 14 dias)

# Lags (histórico recente)
rain_lag1 = chuva[dia - 1]
rain_lag2 = chuva[dia - 2]

# Tendência
rain_trend = diferença(chuva[hoje], chuva[ontem])
```

#### Features Hidrológicas
```python
# Normalização da vazão
river_discharge_norm = vazao / vazao_maxima

# Tendência da vazão
discharge_trend = diferença(vazao[hoje], vazao[ontem])
```

#### Features Meteorológicas Adicionais
```python
- precipitation_hours          # Duração da chuva
- relative_humidity_2m_mean    # Umidade média
- temperature_2m_min           # Temperatura mínima
- et0_fao_evapotranspiration  # Perda por evaporação
```

### 3️⃣ Modelo de Previsão de Tempestades

**Algoritmo:** Random Forest Regressor

```python
RandomForestRegressor(
    n_estimators=100,      # 100 árvores de decisão
    max_depth=10,          # Profundidade máxima
    random_state=42,
    n_jobs=-1             # Paralelização
)
```

#### Entrada (Features)
```python
X = [
    'precip_acum_7d',
    'rain_lag1', 
    'rain_lag2',
    'rain_trend',
    'precipitation_hours',
    'relative_humidity_2m_mean'
]
```

#### Saída
```python
y_pred = precipitação_prevista (mm)
```

#### Classificação de Risco
```python
if chuva >= 80 mm  OR probabilidade >= 90%:  → CRÍTICO
elif chuva >= 40 mm OR probabilidade >= 70%: → ALTO
elif chuva >= 20 mm OR probabilidade >= 40%: → MODERADO
else:                                         → BAIXO
```

### 4️⃣ Modelo de Previsão de Enchentes

**Algoritmo:** Gradient Boosting Classifier (multiclasse)

```python
GradientBoostingClassifier(
    n_estimators=100,      # 100 estimadores
    max_depth=3,           # Árvores rasas (evita overfitting)
    learning_rate=0.1,     # Taxa de aprendizado
    subsample=0.8,         # 80% dos dados por iteração
    random_state=42
)
```

#### Pipeline de Treinamento
```python
Pipeline([
    ('StandardScaler', ),    # Normalização Z-score
    ('GradientBoosting', )   # Classificador
])
```

#### Geração de Rótulos (Treinamento)
```python
# Critérios combinados (precipitação + vazão)
if precip_7d >= 150 mm OR vazao >= percentil_95:  → CRÍTICO (3)
elif precip_7d >= 100 mm OR vazao >= percentil_85: → ALTO (2)
elif precip_7d >= 60 mm OR vazao >= percentil_70:  → MODERADO (1)
else:                                               → BAIXO (0)
```

#### Entrada (14 Features)
```python
X = [
    'precip_acum_3d',
    'precip_acum_7d',
    'precip_acum_14d',
    'rain_sum',
    'rain_lag1',
    'rain_lag2',
    'rain_trend',
    'precipitation_hours',
    'relative_humidity_2m_mean',
    'temperature_2m_min',
    'et0_fao_evapotranspiration',
    'river_discharge_norm',
    'discharge_trend'
]
```

#### Saída
```python
y_pred ∈ {0: baixo, 1: moderado, 2: alto, 3: crítico}
probabilities = {0: p0, 1: p1, 2: p2, 3: p3}  # Soma = 100%
```

### 5️⃣ Sistema de Alertas

#### Condições de Disparo
```python
# Usuário recebe alerta se:
1. Localidade corresponde à monitorada
2. Tipo de alerta configurado (tempestade/enchente)
3. Nível de risco >= nível configurado
```

#### Canais de Notificação

**E-mail (SMTP)**
```python
servidor = 'smtp.gmail.com:587'
mensagem = HTML formatado com:
    - Nível de risco (emoji + cor)
    - Precipitação prevista
    - Recomendações de segurança
```

**SMS/WhatsApp (Twilio)**
```python
twilio.messages.create(
    to=telefone_usuario,
    from_=numero_twilio,
    body=mensagem_curta
)
```

---

## 📊 Métricas e Thresholds

### Tempestades
| Nível | Precipitação | Probabilidade | Emoji |
|-------|-------------|---------------|-------|
| Baixo | < 20 mm | < 40% | ☀️ |
| Moderado | 20-40 mm | 40-70% | 🌧️ |
| Alto | 40-80 mm | 70-90% | ⛈️ |
| Crítico | ≥ 80 mm | ≥ 90% | 🚨 |

### Enchentes
| Nível | Acumulado 7d | Vazão (percentil) |
|-------|--------------|-------------------|
| Baixo | < 60 mm | < P70 |
| Moderado | 60-100 mm | P70-P85 |
| Alto | 100-150 mm | P85-P95 |
| Crítico | ≥ 150 mm | ≥ P95 |

---

## 🚀 Instalação

### Pré-requisitos
```bash
Python 3.8+
pip
```

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/stormwatch-sp.git
cd stormwatch-sp
```

2. **Instale as dependências**
```bash
pip install streamlit pandas numpy scikit-learn plotly requests twilio streamlit-autorefresh
```

3. **Configure as variáveis de ambiente** (opcional)
```bash
# Para funcionalidade de SMS
export TWILIO_ACCOUNT_SID="seu_account_sid"
export TWILIO_AUTH_TOKEN="seu_auth_token"
export TWILIO_PHONE_NUMBER="seu_numero"

# Para e-mail
export EMAIL_ADDRESS="seu_email@gmail.com"
export EMAIL_PASSWORD="sua_senha_app"
```

4. **Execute a aplicação**
```bash
streamlit run app.py
```

5. **Acesse no navegador**
```
http://localhost:8501
```

---

## 📁 Estrutura do Projeto

```
stormwatch-sp/
├── app.py                 # Ponto de entrada da aplicação
├── frontend.py            # Interface do usuário (UI/UX)
├── backend.py             # Lógica de negócio e ML
├── dados_historicos/      # Armazenamento de CSVs
│   └── dados_*.csv        # Histórico por localidade
├── subscriptions.json     # Cadastros de alertas
└── README.md             # Este arquivo
```

---

## 🧪 Exemplo de Uso

### 1. Buscar Localidade
```python
# Digite um endereço ou bairro
"Av. Paulista, São Paulo"
```

### 2. Visualizar Previsão
```
📊 Próximas 24h
🌡️ Temperatura: 18°C - 26°C
🌧️ Chuva prevista: 12 mm
💧 Probabilidade: 65%
```

### 3. Cadastrar Alerta
```
👤 Nome: João Silva
📧 E-mail: joao@example.com
📱 Telefone: +55 11 99999-9999
🔔 Tipo: Ambos
⚠️ Nível mínimo: Alto
```

### 4. Receber Notificação
```
🚨 TEMPESTADE — 10/05/2026
Chuva prevista: 62 mm | Prob: 85%
⚠️ Evite deslocamentos desnecessários
```

---

## 🎨 Interface

### Tema Visual
- **Paleta de cores**: Azul/Ciano (clima) + Gradientes escuros
- **Tipografia**: Syne (títulos), DM Mono (dados)
- **Componentes**: Cards, alertas coloridos, gráficos Plotly

### Responsividade
- ✅ Desktop (layout wide)
- ✅ Mobile (sidebar colapsável)
- ✅ Atualização automática opcional

---

## 🔬 Algoritmos de Machine Learning

### Random Forest (Tempestades)
**Vantagens:**
- ✅ Robusto a outliers
- ✅ Captura relações não-lineares
- ✅ Não requer normalização
- ✅ Feature importance automática

**Hyperparâmetros otimizados:**
- `n_estimators=100` - Balanceio entre precisão e velocidade
- `max_depth=10` - Evita overfitting mantendo capacidade

### Gradient Boosting (Enchentes)
**Vantagens:**
- ✅ Alta precisão em classificação multiclasse
- ✅ Controle fino de overfitting (subsample, learning_rate)
- ✅ Probabilidades calibradas

**Técnicas aplicadas:**
- `StandardScaler` - Normalização Z-score para features numéricas
- `subsample=0.8` - Stochastic Gradient Boosting (reduz variância)
- `max_depth=3` - Árvores rasas (bias-variance tradeoff)

---

## 📈 Validação e Robustez

### Treinamento Incremental
```python
# Validação temporal (últimos 3 dias como teste)
df_train = histórico[:-3]
df_test = histórico[-3:]
```

### Fallback para Regras
```python
# Se dados insuficientes ou modelo falha:
if len(dados) < 10 OR classes_únicas < 2:
    usar_classificação_por_regras()
```

### Tratamento de Dados Ausentes
```python
# Features faltantes recebem valor 0
features.fillna(0, inplace=True)
```

---

## 🌐 APIs Utilizadas

### Open-Meteo Weather API
- **Endpoint**: `https://api.open-meteo.com/v1/forecast`
- **Dados**: Previsão meteorológica 16 dias
- **Taxa**: Gratuita, sem limite

### Open-Meteo Flood API
- **Endpoint**: `https://flood-api.open-meteo.com/v1/flood`
- **Dados**: Vazão de rios (river discharge)
- **Taxa**: Gratuita

### Nominatim (OpenStreetMap)
- **Endpoint**: `https://nominatim.openstreetmap.org/search`
- **Dados**: Geocodificação de endereços
- **Taxa**: 1 req/segundo

---

## 🔐 Segurança e Privacidade

- ✅ Dados armazenados localmente (CSV/JSON)
- ✅ Sem banco de dados externo
- ✅ Credenciais sensíveis via variáveis de ambiente
- ✅ E-mails/telefones não compartilhados

---

## 🐛 Tratamento de Erros

```python
# Todas as APIs têm fallback
try:
    dados = fetch_api()
except:
    usar_dados_cache() or exibir_mensagem_amigavel()

# Modelo ML com fallback
try:
    previsao = modelo.predict(X)
except:
    previsao = classificacao_por_regras()
```

---

## 📝 Roadmap Futuro

- [ ] Integração com Google Maps para visualização
- [ ] Histórico de alertas enviados
- [ ] Exportação de relatórios PDF
- [ ] API REST para integração externa
- [ ] App mobile nativo (Flutter/React Native)
- [ ] Dashboard para gestão pública
- [ ] Previsão de deslizamentos de terra

---

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👥 Autores

**Equipe StormWatch SP**
- 💻 Desenvolvimento
- 🤖 Machine Learning
- 🎨 UI/UX Design

---

## 📞 Contato

Para dúvidas, sugestões ou parcerias:
- 📧 E-mail: contato@stormwatch.com.br
- 🌐 Website: [stormwatch.com.br](https://stormwatch.com.br)
- 💬 Issues: [GitHub Issues](https://github.com/seu-usuario/stormwatch-sp/issues)

---

<div align="center">

**Feito com ❤️ e ⚡ por desenvolvedores que se importam com vidas**

⭐ Se este projeto foi útil, considere dar uma estrela!

</div>
