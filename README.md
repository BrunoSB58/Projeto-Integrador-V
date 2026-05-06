# 🧠 Melhorias nos Modelos de Previsão — StormWatch SP

## Resumo das alterações

Os modelos de machine learning responsáveis pela previsão de **tempestades** e **enchentes** foram reformulados para aumentar a confiabilidade, a precisão e a capacidade de generalização, mantendo o treinamento instantâneo (on‑the‑fly) a cada consulta.

---

## ⛈️ Tempestade — de Regressão Linear para Random Forest

**Antes:** uma regressão linear usava apenas o índice da data (`date_num`) para prever a chuva do dia seguinte.

**Agora:** um **RandomForestRegressor** leve (20 árvores, profundidade máxima 4) considera múltiplas variáveis meteorológicas recentes:

- `rain_lag1`, `rain_lag2` — chuva dos dias anteriores
- `precipitation_hours` — horas de precipitação
- `precipitation_probability_max` — probabilidade máxima de chuva fornecida pela API
- `relative_humidity_2m_mean` — umidade média
- `rain_trend` — tendência (diferença) da chuva

**Por que é melhor?**  
O Random Forest captura relações não lineares e interações entre variáveis (ex.: chuva persistente + alta probabilidade → tempestade), reduz falsos negativos e é menos sensível a *outliers* do que a regressão linear.

---

## 🌊 Enchente — Gradient Boosting com novas features e validação

**Antes:** Gradient Boosting Classifier com um conjunto limitado de variáveis.

**Agora:** o modelo foi **expandido** com três novas *features* e um pequeno esquema de validação:

**Novas features:**
- `temperature_2m_min` — temperatura mínima (solos quentes e úmidos favorecem enchentes)
- `et0_fao_evapotranspiration` — evapotranspiração de referência (indicador de saturação do solo)
- `discharge_trend` — tendência da descarga do rio (variação recente da vazão)

**Validação interna:**  
Os últimos 3 dias do histórico são reservados para teste. Se o modelo treinado com os dados restantes falhar ou não tiver classes suficientes, o sistema recorre automaticamente às regras de limiares (*fallback*).

**Configuração ajustada:**
- `n_estimators=100`, `max_depth=3`, `learning_rate=0.1`, `subsample=0.8`
- Pipeline com `StandardScaler` + `GradientBoostingClassifier`

**Por que é melhor?**  
As novas variáveis permitem que o modelo entenda melhor a condição do solo e a dinâmica do rio, antecipando enchentes mesmo quando a chuva acumulada ainda não atingiu os limiares críticos.

---

## ⚡ Desempenho e integração

- Ambos os modelos são treinados **a cada requisição** com os dados históricos já disponíveis (90 dias meteorológicos, 180 dias de rios).
- O tempo de treinamento é de **milissegundos**, sem necessidade de pré‑processamento ou servidores externos.
- A interface do usuário e as assinaturas de alerta continuam funcionando exatamente da mesma forma – apenas as funções `forecast_storm()` e `forecast_flood()` em `backend.py` foram alteradas.

---

## 📁 Arquivo afetado

- `backend.py` – funções `forecast_storm()`, `forecast_flood()` e novas auxiliares `_extra_features()`.

---

**Essas melhorias tornam o StormWatch SP mais preciso e preparado para eventos climáticos extremos, sem adicionar complexidade operacional.**