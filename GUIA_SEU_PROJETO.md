# 🎯 GUIA ESPECÍFICO PARA SEU PROJETO
## Backend.py já está completo! ✅

---

## 📋 SITUAÇÃO ATUAL

✅ Seu `backend.py` JÁ TEM tudo implementado:
- Funções de envio (SMS via Twilio + Email via SendGrid)
- Banco de dados PostgreSQL
- Sistema de IDs alfanuméricos
- Previsões de IA (Random Forest + Gradient Boosting)
- Geocodificação restrita a São Paulo

❌ O que estava FALTANDO:
- Sistema de monitoramento em segundo plano
- Verificação automática periódica
- Envio automático de alertas

✅ Agora você TEM:
- `monitor_alertas.py` → resolve tudo isso!

---

## 🚀 INSTALAÇÃO SIMPLIFICADA (4 PASSOS)

### **PASSO 1: Adicionar arquivos ao projeto**

```
seu_projeto/
├── app.py                      # ← já existe
├── frontend.py                 # ← já existe  
├── backend.py                  # ← já existe (COMPLETO!)
├── monitor_alertas.py          # ← 🆕 ADICIONAR ESTE
├── testar_monitor.py           # ← 🆕 ADICIONAR (opcional)
├── .env                        # ← 🆕 CONFIGURAR (veja abaixo)
├── Dados/                      # ← já existe
```

### **PASSO 2: Configurar variáveis de ambiente**

Crie o arquivo `.env` na raiz do projeto com suas credenciais:

```bash
# Banco de dados (você já deve ter configurado)
PG_DBNAME=stormwatch
PG_USER=postgres
PG_PASSWORD=sua_senha
PG_HOST=localhost
PG_PORT=5432

# Twilio (para SMS)
TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=seu_token
TWILIO_PHONE_NUMBER=+5511999999999

# SendGrid (para email)
SENDGRID_API_KEY=SG.xxxxxxxx
FROM_EMAIL=seu_email@dominio.com
```

**Onde conseguir essas credenciais:**
- **Twilio**: https://www.twilio.com/try-twilio (US$ 15 grátis)
- **SendGrid**: https://sendgrid.com/ (100 emails/dia grátis)

### **PASSO 3: Instalar dependência do PostgreSQL (se necessário)**

```bash
pip install psycopg2-binary
```

Você provavelmente já tem instalado, mas confirme.

### **PASSO 4: Testar e rodar**

```bash
# Testar se está tudo OK
python testar_monitor.py

# Executar uma vez (teste)
python monitor_alertas.py --once

# Rodar continuamente
python monitor_alertas.py
```

---

## 🔧 AJUSTES NECESSÁRIOS NO MONITOR_ALERTAS.PY

Seu backend retorna DataFrames do PostgreSQL, então preciso ajustar o `monitor_alertas.py` para funcionar com isso.

### **MODIFICAÇÃO NECESSÁRIA:**

No arquivo `monitor_alertas.py`, localize a função `verificar_e_enviar_alertas()` (linha ~75) e modifique:

**ANTES:**
```python
# 1. Carregar todos os cadastros
subs = load_subscriptions()
estatisticas["total_cadastros"] = len(subs)

if not subs:
    logger.warning("Nenhum cadastro encontrado.")
    return estatisticas

logger.info(f"📋 {len(subs)} cadastro(s) encontrado(s)")

# 2. Agrupar cadastros por localidade
cadastros_por_loc = {}
for sub in subs:
    loc_key = (sub["lat"], sub["lon"])
```

**DEPOIS:**
```python
# 1. Carregar todos os cadastros (retorna DataFrame)
df_subs = load_subscriptions()
estatisticas["total_cadastros"] = len(df_subs)

if df_subs.empty:
    logger.warning("Nenhum cadastro encontrado.")
    return estatisticas

logger.info(f"📋 {len(df_subs)} cadastro(s) encontrado(s)")

# 2. Converter DataFrame para lista de dicts
subs = df_subs.to_dict('records')

# 3. Agrupar cadastros por localidade
cadastros_por_loc = {}
for sub in subs:
    # IMPORTANTE: Seu banco não tem lat/lon, precisa buscar da API!
    # Você precisa armazenar lat/lon no banco também
    # Por enquanto, vamos buscar via geocoding:
    localidade = sub["localidade"]
    
    # Buscar coordenadas
    from backend import search_location
    locs = search_location(localidade)
    if not locs:
        logger.warning(f"   ⚠️ Coordenadas não encontradas para {localidade}")
        continue
    
    lat = locs[0]["lat"]
    lon = locs[0]["lon"]
    
    loc_key = (lat, lon)
```

---

## ⚠️ PROBLEMA CRÍTICO IDENTIFICADO

Olhando seu banco de dados, vejo que você **NÃO está salvando as coordenadas (lat/lon)** na tabela `subscriptions`!

Veja sua tabela atual:
```sql
CREATE TABLE IF NOT EXISTS subscriptions (
    id VARCHAR(10) PRIMARY KEY,
    nome VARCHAR(255),
    email VARCHAR(255) NOT NULL,
    telefone VARCHAR(50),
    localidade VARCHAR(255) NOT NULL,  -- ← só o nome!
    tipo_alerta VARCHAR(50) NOT NULL,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### **SOLUÇÃO: Adicionar colunas lat/lon**

Execute este SQL no seu PostgreSQL:

```sql
ALTER TABLE subscriptions 
ADD COLUMN latitude DECIMAL(10, 6),
ADD COLUMN longitude DECIMAL(10, 6);
```

E modifique a função `save_subscriptions()` no `backend.py`:

**ADICIONAR os parâmetros lat e lon:**

Localize a linha ~112 no seu backend.py:

```python
def save_subscriptions(df_novo: pd.DataFrame) -> str:
    conn = get_db_connection()
    cur = conn.cursor()
    cadastro_id = get_unique_subscription_id()
    query = sql.SQL("""
        INSERT INTO subscriptions (id, nome, email, telefone, localidade, tipo_alerta, latitude, longitude)
        VALUES (%(id)s, %(nome)s, %(email)s, %(telefone)s, %(localidade)s, %(tipo_alerta)s, %(latitude)s, %(longitude)s)
    """)
    for _, row in df_novo.iterrows():
        cur.execute(query, {
            "id": cadastro_id,
            "nome": row["nome"],
            "email": row["email"],
            "telefone": row["telefone"],
            "localidade": row["localidade"],
            "tipo_alerta": row["tipo_alerta"],
            "latitude": row.get("latitude"),      # ← NOVO
            "longitude": row.get("longitude"),    # ← NOVO
        })
    conn.commit()
    cur.close()
    conn.close()
    return cadastro_id
```

E na função `load_subscriptions()` (linha ~89):

```python
def load_subscriptions() -> pd.DataFrame:
    conn = get_db_connection()
    df = pd.read_sql(
        "SELECT id, nome, email, telefone, localidade, tipo_alerta, latitude, longitude FROM subscriptions ORDER BY data_cadastro DESC",
        conn
    )
    conn.close()
    return df
```

---

## 📝 CHECKLIST FINAL

- [ ] Adicionei `monitor_alertas.py` ao projeto
- [ ] Configurei o arquivo `.env` com credenciais
- [ ] Executei `ALTER TABLE` para adicionar lat/lon
- [ ] Modifiquei `save_subscriptions()` no backend.py
- [ ] Modifiquei `load_subscriptions()` no backend.py
- [ ] Testei com `python testar_monitor.py`
- [ ] Testei com `python monitor_alertas.py --once`
- [ ] Configurei para rodar automaticamente

---

## 🎉 DEPOIS DISSO

Seu sistema estará completo e funcionando com:
- ✅ Interface Streamlit para usuários
- ✅ Cadastro em PostgreSQL com coordenadas
- ✅ Monitor rodando em segundo plano 24/7
- ✅ Alertas automáticos via SMS (Twilio) e Email (SendGrid)
- ✅ IA analisando riscos constantemente

---

**Qualquer dúvida, é só avisar!** 😊
