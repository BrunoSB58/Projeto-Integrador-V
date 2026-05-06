# ⛈️ StormWatch — Previsão de Tempestades com Busca Dinâmica

## O que mudou?

O sistema foi reformulado para **eliminar a lista fixa de bairros/URLs hardcoded**.
Agora você pode pesquisar **qualquer cidade, bairro ou endereço do mundo**.

---

## 🚀 Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 🗺️ Como funciona a busca de localidade

1. Digite o nome da cidade, bairro ou endereço na barra de pesquisa
2. Clique em **🔍 Buscar** — o sistema consulta a **Open-Meteo Geocoding API**
3. Selecione a localidade correta na lista de resultados
4. Clique em **✔️ Usar esta localidade**
5. Os dados meteorológicos são carregados automaticamente via Open-Meteo

```
Barra de pesquisa → Geocoding API → lat/lon → Weather API → Análise + ML
```

**Não são necessárias chaves de API** para Open-Meteo.

---

## 🔄 O que foi removido

| Antes | Depois |
|---|---|
| `neighborhoods = {"Capão Redondo": os.environ.get("API_...")}` | ❌ Removido |
| Variáveis de ambiente com URLs fixas | ❌ Removidas |
| `selectbox` com lista hardcoded | ✅ Campo de texto com busca |

---

## ⚙️ Variáveis de ambiente ainda necessárias

Apenas para alertas por SMS/e-mail (opcionais):

```env
# .env
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

SENDGRID_API_KEY=...
FROM_EMAIL=seu@email.com
```

O app funciona normalmente **sem essas variáveis** — apenas os alertas ficam desativados.

---

## 📁 Estrutura

```
storm_app/
├── app.py          # Interface Streamlit — busca dinâmica de localidade
├── backend.py      # Geocoding, fetch meteorológico, ML, alertas
├── requirements.txt
├── Dados/          # CSVs históricos salvos por localidade
│   └── subscriptions.csv
└── .env            # (opcional) credenciais Twilio/SendGrid
```

---

## 🆕 Novas funções no `backend.py`

| Função | Descrição |
|---|---|
| `search_location(query)` | Geocodifica texto → lista de localidades com lat/lon |
| `build_weather_url(lat, lon, days)` | Monta URL da Open-Meteo a partir de coordenadas |
| `forecast_storm(df)` | Retorna dict com nível de risco, probabilidade e mensagem |

---

## 💡 Exemplos de pesquisa

- `Capão Redondo` → resulta em Capão Redondo, São Paulo — Brasil
- `Jardim Angela` → múltiplos resultados, escolha SP
- `Rio de Janeiro` → cidade inteira
- `Manaus, AM` → cidade + estado
- `Porto Alegre` → mostra resultados do Brasil e outros países
