"""
backend.py — StormWatch SP
  • Geocodificação restrita ao estado de São Paulo
  • Previsão de Tempestade via Random Forest Regressor
  • Previsão de Enchente via Gradient Boosting (Open-Meteo Flood API)
  • Alertas por SMS (Twilio) e E-mail (SendGrid)
  • Cadastros persistidos em PostgreSQL
  • Histórico meteorológico persistido em PostgreSQL (substitui CSV)
"""

import os
import re
import requests
import pandas as pd
import numpy as np
import string
import random
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression  # mantido para fallback se necessário
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from dotenv import load_dotenv
import sendgrid
from sendgrid.helpers.mail import Mail
from twilio.rest import Client
import psycopg2
from psycopg2 import sql

load_dotenv()

# ─── Endpoints Open-Meteo ────────────────────────────────────────────
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_BASE  = "https://api.open-meteo.com/v1/forecast"
FLOOD_BASE    = "https://flood-api.open-meteo.com/v1/flood"

DAILY_WEATHER_VARS = [
    "rain_sum",
    "precipitation_sum",
    "precipitation_hours",
    "precipitation_probability_max",
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "relative_humidity_2m_mean",
    "windspeed_10m_max",
    "et0_fao_evapotranspiration",
    "shortwave_radiation_sum",
]

# Limiares de risco (mm acumulados)
STORM_THRESH = {"moderado": 20,  "alto": 50,  "critico": 80}
FLOOD_THRESH = {"moderado": 40,  "alto": 100, "critico": 180}

# Percentis de descarga do rio
DISCHARGE_PERCENTIL = {"moderado": 60, "alto": 80, "critico": 95}

# Nomes aceitos para o estado de São Paulo
_SP_ADMIN1 = {"são paulo", "sao paulo", "sp", "estado de são paulo"}


# ════════════════════════════════════════════════════════════════════
#  GERAÇÃO DE ID ALFANUMÉRICO
# ════════════════════════════════════════════════════════════════════

def generate_unique_id(length: int = 6) -> str:
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def get_unique_subscription_id() -> str:
    conn = get_db_connection()
    cur = conn.cursor()
    for _ in range(10):
        new_id = generate_unique_id(6)
        cur.execute("SELECT id FROM subscriptions WHERE id = %s", (new_id,))
        if cur.fetchone() is None:
            cur.close()
            conn.close()
            return new_id
    cur.close()
    conn.close()
    raise Exception("Não foi possível gerar um ID único após 10 tentativas.")


# ════════════════════════════════════════════════════════════════════
#  CONEXÃO COM BANCO DE DADOS POSTGRESQL
# ════════════════════════════════════════════════════════════════════

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("PG_DBNAME", "stormwatch"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", ""),
        host=os.getenv("PG_HOST", "localhost"),
        port=os.getenv("PG_PORT", "5432")
    )


def init_database():
    """Cria as tabelas necessárias no banco de dados."""
    conn = get_db_connection()
    cur = conn.cursor()
    # Tabela de inscrições (já existente)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id VARCHAR(10) PRIMARY KEY,
            nome VARCHAR(255),
            email VARCHAR(255) NOT NULL,
            telefone VARCHAR(50),
            localidade VARCHAR(255) NOT NULL,
            tipo_alerta VARCHAR(50) NOT NULL,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Nova tabela para histórico meteorológico
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weather_history (
            id SERIAL PRIMARY KEY,
            location_key VARCHAR(255) NOT NULL,
            data DATE NOT NULL,
            rain_sum DOUBLE PRECISION,
            precipitation_sum DOUBLE PRECISION,
            precipitation_hours DOUBLE PRECISION,
            precipitation_probability_max DOUBLE PRECISION,
            temperature_2m_max DOUBLE PRECISION,
            temperature_2m_min DOUBLE PRECISION,
            temperature_2m_mean DOUBLE PRECISION,
            relative_humidity_2m_mean DOUBLE PRECISION,
            windspeed_10m_max DOUBLE PRECISION,
            et0_fao_evapotranspiration DOUBLE PRECISION,
            shortwave_radiation_sum DOUBLE PRECISION,
            precip_acum_3d DOUBLE PRECISION,
            precip_acum_7d DOUBLE PRECISION,
            precip_acum_14d DOUBLE PRECISION,
            rain_lag1 DOUBLE PRECISION,
            rain_lag2 DOUBLE PRECISION,
            rain_trend DOUBLE PRECISION,
            UNIQUE(location_key, data)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def load_subscriptions() -> pd.DataFrame:
    conn = get_db_connection()
    df = pd.read_sql(
        "SELECT id, nome, email, telefone, localidade, tipo_alerta FROM subscriptions ORDER BY data_cadastro DESC",
        conn
    )
    conn.close()
    return df


def save_subscriptions(df_novo: pd.DataFrame) -> str:
    conn = get_db_connection()
    cur = conn.cursor()
    cadastro_id = get_unique_subscription_id()
    query = sql.SQL("""
        INSERT INTO subscriptions (id, nome, email, telefone, localidade, tipo_alerta)
        VALUES (%(id)s, %(nome)s, %(email)s, %(telefone)s, %(localidade)s, %(tipo_alerta)s)
    """)
    for _, row in df_novo.iterrows():
        cur.execute(query, {
            "id": cadastro_id,
            "nome": row["nome"],
            "email": row["email"],
            "telefone": row["telefone"],
            "localidade": row["localidade"],
            "tipo_alerta": row["tipo_alerta"]
        })
    conn.commit()
    cur.close()
    conn.close()
    return cadastro_id


def remove_subscription_by_id(cadastro_id: str) -> dict:
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nome, email, localidade FROM subscriptions WHERE id = %s",
            (cadastro_id.upper(),)
        )
        resultado = cur.fetchone()
        if resultado is None:
            cur.close()
            conn.close()
            return {
                "success": False,
                "message": f"❌ Cadastro com ID **{cadastro_id.upper()}** não encontrado.",
                "dados": None
            }
        dados_deletados = {
            "id": resultado[0],
            "nome": resultado[1],
            "email": resultado[2],
            "localidade": resultado[3]
        }
        cur.execute("DELETE FROM subscriptions WHERE id = %s", (cadastro_id.upper(),))
        conn.commit()
        cur.close()
        conn.close()
        return {
            "success": True,
            "message": f"✅ Cadastro **{cadastro_id.upper()}** removido com sucesso!",
            "dados": dados_deletados
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Erro ao remover cadastro: {str(e)}",
            "dados": None
        }


def remove_subscription_by_email(email: str) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM subscriptions WHERE email = %s", (email,))
    removidos = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return removidos > 0


# ════════════════════════════════════════════════════════════════════
#  GEOCODIFICAÇÃO — restrita ao estado de São Paulo
# ════════════════════════════════════════════════════════════════════

def search_location(query: str, count: int = 10) -> list[dict]:
    if not query or len(query.strip()) < 2:
        return []
    try:
        resp = requests.get(
            GEOCODING_URL,
            params={
                "name":        query.strip(),
                "count":       count,
                "language":    "pt",
                "format":      "json",
                "countrycode": "BR",
            },
            timeout=10,
        )
        resp.raise_for_status()
        raw = resp.json().get("results", [])
        locations = []
        for r in raw:
            admin1 = r.get("admin1", "")
            if admin1.lower().strip() not in _SP_ADMIN1:
                continue
            name    = r.get("name", "")
            country = r.get("country", "Brasil")
            locations.append({
                "display_name": f"{name}, {admin1} — {country}",
                "name":         name,
                "lat":          r.get("latitude"),
                "lon":          r.get("longitude"),
                "admin1":       admin1,
                "country":      country,
            })
        return locations
    except Exception:
        return []


# ════════════════════════════════════════════════════════════════════
#  CONSTRUÇÃO DE URLs
# ════════════════════════════════════════════════════════════════════

def build_weather_url(lat: float, lon: float, forecast_days: int = 7) -> str:
    variables = ",".join(DAILY_WEATHER_VARS)
    return (
        f"{WEATHER_BASE}"
        f"?latitude={lat}&longitude={lon}"
        f"&daily={variables}"
        f"&past_days=90&forecast_days={forecast_days}"
        f"&timezone=America%2FSao_Paulo"
    )


def build_flood_url(lat: float, lon: float, forecast_days: int = 7) -> str:
    return (
        f"{FLOOD_BASE}"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=river_discharge"
        f"&past_days=180&forecast_days={forecast_days}"
        f"&timezone=America%2FSao_Paulo"
    )


# ════════════════════════════════════════════════════════════════════
#  ALERTAS — SMS e E-mail
# ════════════════════════════════════════════════════════════════════

def send_sms_alert(phone: str, message: str) -> dict:
    try:
        client = Client(
            os.environ["TWILIO_ACCOUNT_SID"],
            os.environ["TWILIO_AUTH_TOKEN"],
        )
        msg = client.messages.create(
            body=message, from_=os.environ["TWILIO_PHONE_NUMBER"], to=phone
        )
        return {"success": True, "sid": msg.sid}
    except KeyError as e:
        return {"success": False, "error": f"Variável faltando: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_email_alert(email: str, subject: str, html_message: str) -> dict:
    api_key    = os.environ.get("SENDGRID_API_KEY")
    from_email = os.environ.get("FROM_EMAIL")
    if not api_key or not from_email:
        return {"success": False, "error": "SENDGRID_API_KEY / FROM_EMAIL não configurados."}
    try:
        sg   = sendgrid.SendGridAPIClient(api_key=api_key)
        mail = Mail(from_email=from_email, to_emails=email,
                    subject=subject, html_content=html_message)
        resp = sg.send(mail)
        return {"success": True} if resp.status_code in (200, 202) \
               else {"success": False, "error": f"Status HTTP {resp.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ════════════════════════════════════════════════════════════════════
#  DADOS METEOROLÓGICOS
# ════════════════════════════════════════════════════════════════════

def fetch_weather_data(api_url: str) -> dict | None:
    try:
        resp = requests.get(api_url, timeout=15)
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None


def process_weather_data(json_data: dict | None) -> pd.DataFrame | None:
    if not json_data:
        return None
    daily = json_data.get("daily", {})
    if not daily:
        return None

    df = pd.DataFrame({"data": pd.to_datetime(daily.get("time", []))})
    for var in DAILY_WEATHER_VARS:
        if var in daily:
            df[var] = daily[var]
    for col in ["rain_sum", "precipitation_sum", "precipitation_hours"]:
        if col not in df.columns:
            df[col] = 0.0
    df.fillna(0, inplace=True)
    return _enrich_features(df) if not df.empty else None


def _enrich_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("data").reset_index(drop=True)
    df["precip_acum_3d"]  = df["precipitation_sum"].rolling(3,  min_periods=1).sum()
    df["precip_acum_7d"]  = df["precipitation_sum"].rolling(7,  min_periods=1).sum()
    df["precip_acum_14d"] = df["precipitation_sum"].rolling(14, min_periods=1).sum()
    df["rain_lag1"]       = df["rain_sum"].shift(1).fillna(0)
    df["rain_lag2"]       = df["rain_sum"].shift(2).fillna(0)
    df["rain_trend"]      = df["rain_sum"].diff().fillna(0)
    return df


# ════════════════════════════════════════════════════════════════════
#  DADOS DE RIOS (Flood API – GloFAS)
# ════════════════════════════════════════════════════════════════════

def fetch_flood_data(lat: float, lon: float, forecast_days: int = 7) -> pd.DataFrame | None:
    try:
        resp = requests.get(build_flood_url(lat, lon, forecast_days), timeout=15)
        if resp.status_code != 200:
            return None
        daily = resp.json().get("daily", {})
        if not daily or "river_discharge" not in daily:
            return None
        df = pd.DataFrame({
            "data":            pd.to_datetime(daily["time"]),
            "river_discharge": daily["river_discharge"],
        })
        df["river_discharge"] = pd.to_numeric(df["river_discharge"], errors="coerce").fillna(0)
        return df
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════
#  IA — PREVISÃO DE TEMPESTADE (Random Forest)
# ════════════════════════════════════════════════════════════════════

def forecast_storm(df: pd.DataFrame) -> dict:
    vazio = {"nivel": "sem_dados", "mensagem": "Dados insuficientes.",
             "chuva_prevista": None, "prob_chuva": None, "data": None}

    feature_cols = [
        "rain_lag1", "rain_lag2", "precipitation_hours",
        "precipitation_probability_max", "relative_humidity_2m_mean",
        "rain_trend"
    ]
    # Garantir que as features existam
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0.0

    df_valid = df.dropna(subset=["rain_sum"] + feature_cols)
    if len(df_valid) < 5:
        return vazio

    # Construir X e y (y = rain_sum do dia seguinte)
    X = df_valid[feature_cols].iloc[:-1]
    y = df_valid["rain_sum"].shift(-1).iloc[:-1].dropna()
    X = X.loc[y.index]

    if len(X) < 3:
        return vazio

    next_date = df["data"].max() + pd.Timedelta(days=1)

    modelo = RandomForestRegressor(
        n_estimators=20,
        max_depth=4,
        random_state=42,
        n_jobs=1
    )
    modelo.fit(X, y)

    # Previsão para o próximo dia
    X_pred = df_valid[feature_cols].iloc[-1:].fillna(0)
    pred_rain = max(0.0, float(modelo.predict(X_pred)[0]))

    prob_media = None
    if "precipitation_probability_max" in df.columns:
        vals = df["precipitation_probability_max"].dropna()
        if not vals.empty:
            prob_media = float(vals.mean())

    t = STORM_THRESH
    if   pred_rain >= t["critico"] or (prob_media and prob_media >= 90): nivel = "critico"
    elif pred_rain >= t["alto"]    or (prob_media and prob_media >= 70): nivel = "alto"
    elif pred_rain >= t["moderado"]or (prob_media and prob_media >= 40): nivel = "moderado"
    else:                                                                  nivel = "baixo"

    return {
        "nivel":          nivel,
        "chuva_prevista": round(pred_rain, 1),
        "prob_chuva":     round(prob_media, 1) if prob_media is not None else None,
        "data":           next_date.strftime("%Y-%m-%d"),
        "mensagem":       _msg_storm(nivel, pred_rain, prob_media, next_date),
    }


def _msg_storm(nivel, chuva, prob, data) -> str:
    p  = f" | Prob.: {prob:.0f}%" if prob is not None else ""
    dt = data.strftime("%d/%m/%Y")
    return {
        "critico":  f"🚨 TEMPESTADE SEVERA — {dt}: {chuva:.1f} mm previstos{p}. Risco extremo!",
        "alto":     f"⛈️ TEMPESTADE — {dt}: {chuva:.1f} mm previstos{p}.",
        "moderado": f"🌧️ CHUVA MODERADA — {dt}: {chuva:.1f} mm previstos{p}.",
        "baixo":    f"☀️ SEM RISCO — {dt}: {chuva:.1f} mm previstos{p}.",
    }.get(nivel, "☀️ Sem risco.")


# ════════════════════════════════════════════════════════════════════
#  FUNÇÕES AUXILIARES PARA ENCHENTE
# ════════════════════════════════════════════════════════════════════

def _gerar_rotulos(df_w: pd.DataFrame, df_f: pd.DataFrame | None) -> pd.Series:
    t  = FLOOD_THRESH
    c3 = df_w["precip_acum_7d"] >= t["critico"]
    c2 = df_w["precip_acum_7d"] >= t["alto"]
    c1 = df_w["precip_acum_7d"] >= t["moderado"]

    if df_f is not None and not df_f.empty:
        m    = df_w[["data"]].merge(df_f[["data", "river_discharge"]], on="data", how="left")
        disc = m["river_discharge"].fillna(0)
        all_ = df_f["river_discharge"].dropna()
        if not all_.empty:
            qc = all_.quantile(DISCHARGE_PERCENTIL["critico"]  / 100)
            qa = all_.quantile(DISCHARGE_PERCENTIL["alto"]     / 100)
            qm = all_.quantile(DISCHARGE_PERCENTIL["moderado"] / 100)
            c3 |= (disc >= qc)
            c2 |= (disc >= qa)
            c1 |= (disc >= qm)

    r = pd.Series(0, index=df_w.index)
    r[c1] = 1; r[c2] = 2; r[c3] = 3
    return r


_FLOOD_FEATURES = [
    "precip_acum_3d", "precip_acum_7d", "precip_acum_14d",
    "rain_sum", "rain_lag1", "rain_lag2", "rain_trend",
    "precipitation_hours", "relative_humidity_2m_mean",
    "temperature_2m_min",                    # NOVO
    "et0_fao_evapotranspiration",           # NOVO
    "river_discharge_norm",
    "discharge_trend",                      # NOVO
]


def _extra_features(df_w: pd.DataFrame, df_flood: pd.DataFrame | None) -> pd.DataFrame:
    """Adiciona colunas derivadas para o modelo de enchente."""
    if df_flood is not None and not df_flood.empty:
        mg = df_w.merge(df_flood[["data","river_discharge"]].rename(
            columns={"river_discharge": "_dr"}), on="data", how="left")
        df_w["_dr"] = mg["_dr"].fillna(0).values
        mx = df_w["_dr"].max()
        df_w["river_discharge_norm"] = df_w["_dr"] / (mx if mx > 0 else 1.0)
        df_w["discharge_trend"] = df_w["_dr"].diff().fillna(0)
    else:
        df_w["_dr"] = 0.0
        df_w["river_discharge_norm"] = 0.0
        df_w["discharge_trend"] = 0.0

    for col in ["precipitation_hours", "relative_humidity_2m_mean",
                "temperature_2m_min", "et0_fao_evapotranspiration"]:
        if col not in df_w.columns:
            df_w[col] = 0.0
    return df_w


# ════════════════════════════════════════════════════════════════════
#  IA — PREVISÃO DE ENCHENTE (Gradient Boosting Aprimorado)
# ════════════════════════════════════════════════════════════════════

def forecast_flood(df_weather: pd.DataFrame, df_flood: pd.DataFrame | None) -> dict:
    vazio = {"nivel": "sem_dados",
             "mensagem": "Dados insuficientes para previsão de enchente.",
             "acum_7d": None, "discharge_atual": None,
             "prob_classes": None, "data": None}

    df_w = df_weather.copy()
    if df_w.empty or len(df_w) < 4:
        return vazio

    df_w = _extra_features(df_w, df_flood)
    df_w["risco_enchente"] = _gerar_rotulos(df_w, df_flood)

    feats_ok = [f for f in _FLOOD_FEATURES if f in df_w.columns]
    df_train = df_w.dropna(subset=feats_ok)

    acum_7d    = float(df_w["precip_acum_7d"].iloc[-1]) if "precip_acum_7d" in df_w.columns else 0.0
    disc_atual = float(df_w["_dr"].iloc[-1]) if df_flood is not None else None
    next_date  = df_w["data"].max() + pd.Timedelta(days=1)

    if len(df_train) < 10 or df_train["risco_enchente"].nunique() < 2:
        return _flood_regras(acum_7d, disc_atual, next_date, df_flood)

    # Validação simples: reservar últimos 3 dias como teste (apenas para garantir robustez)
    df_train_main = df_train.iloc[:-3]
    if len(df_train_main) < 5:
        return _flood_regras(acum_7d, disc_atual, next_date, df_flood)

    try:
        clf = Pipeline([
            ("sc", StandardScaler()),
            ("gb", GradientBoostingClassifier(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
            )),
        ])
        clf.fit(df_train_main[feats_ok].values, df_train_main["risco_enchente"].values)

        X_pred = df_train[feats_ok].iloc[-1:].fillna(0)
        pred_class = int(clf.predict(X_pred)[0])
        if hasattr(clf, "predict_proba"):
            probs = clf.predict_proba(X_pred)[0]
            prob_dict = {int(c): round(float(p)*100, 1) for c, p in zip(clf.classes_, probs)}
        else:
            prob_dict = None
        # Garantir que todas as classes apareçam
        if prob_dict is not None:
            for c in [0,1,2,3]:
                prob_dict.setdefault(c, 0.0)
        else:
            prob_dict = None

        nivel = {0:"baixo", 1:"moderado", 2:"alto", 3:"critico"}.get(pred_class, "baixo")
        return {
            "nivel":           nivel,
            "mensagem":        _msg_flood(nivel, acum_7d, disc_atual, next_date),
            "acum_7d":         round(acum_7d, 1),
            "discharge_atual": round(disc_atual, 2) if disc_atual is not None else None,
            "prob_classes":    prob_dict,
            "data":            next_date.strftime("%Y-%m-%d"),
        }
    except Exception:
        return _flood_regras(acum_7d, disc_atual, next_date, df_flood)


def _flood_regras(acum_7d, disc, next_date, df_flood) -> dict:
    t = FLOOD_THRESH
    nivel = ("critico"  if acum_7d >= t["critico"]  else
             "alto"     if acum_7d >= t["alto"]     else
             "moderado" if acum_7d >= t["moderado"] else "baixo")
    return {
        "nivel":           nivel,
        "mensagem":        _msg_flood(nivel, acum_7d, disc if df_flood is not None else None, next_date),
        "acum_7d":         round(acum_7d, 1),
        "discharge_atual": round(disc, 2) if disc is not None else None,
        "prob_classes":    None,
        "data":            next_date.strftime("%Y-%m-%d"),
    }


def _msg_flood(nivel, acum_7d, disc, data) -> str:
    dt    = data.strftime("%d/%m/%Y") if hasattr(data, "strftime") else str(data)
    d_str = f" | Rio: {disc:.1f} m³/s" if disc and disc > 0 else ""
    return {
        "critico":  f"🚨 ENCHENTE CRÍTICA — {dt}: Acumulado 7d = {acum_7d:.0f} mm{d_str}. Evacue áreas de risco!",
        "alto":     f"🌊 RISCO ALTO DE ENCHENTE — {dt}: Acumulado 7d = {acum_7d:.0f} mm{d_str}.",
        "moderado": f"⚠️ RISCO MODERADO DE ENCHENTE — {dt}: Acumulado 7d = {acum_7d:.0f} mm{d_str}.",
        "baixo":    f"✅ SEM RISCO DE ENCHENTE — {dt}: Acumulado 7d = {acum_7d:.0f} mm{d_str}.",
    }.get(nivel, "✅ Sem risco.")


def _chave(name: str) -> str:
    return re.sub(r"[^\w\-]", "_", name.lower()).strip("_")


# ════════════════════════════════════════════════════════════════════
#  HISTÓRICO METEOROLÓGICO (POSTGRESQL) — substitui arquivos CSV
# ════════════════════════════════════════════════════════════════════

def update_historical_data(df_new: pd.DataFrame, location_name: str) -> tuple[str, pd.DataFrame]:
    """
    Persiste os dados no banco (tabela weather_history) e retorna
    o histórico completo da localidade.
    """
    # Garantir que a tabela exista
    init_database()

    key = _chave(location_name)
    filename = f"dados_{key}.csv"  # mantido para compatibilidade com frontend (download)

    conn = get_db_connection()
    try:
        # 1. Recuperar dados existentes do banco
        existing = pd.read_sql_query(
            "SELECT * FROM weather_history WHERE location_key = %s ORDER BY data",
            conn,
            params=(key,),
        )
        if not existing.empty:
            existing = existing.drop(columns=["id", "location_key"], errors="ignore")
            existing["data"] = pd.to_datetime(existing["data"])
    except Exception:
        existing = pd.DataFrame()

    # 2. Combinar histórico existente com os novos dados
    if not existing.empty:
        combined = (pd.concat([existing, df_new])
                    .drop_duplicates(subset=["data"])
                    .sort_values("data")
                    .reset_index(drop=True))
    else:
        combined = df_new.copy()

    # 3. Substituir registros antigos da localidade e inserir os combinados
    with conn.cursor() as cur:
        cur.execute("DELETE FROM weather_history WHERE location_key = %s", (key,))

        # ⚠️ CORREÇÃO: excluir 'data' da lista dinâmica, pois já é inserida separadamente
        cols = [col for col in combined.columns if col != "data"]

        placeholders = sql.SQL(", ").join([sql.Placeholder() for _ in cols])
        insert_sql = sql.SQL(
            "INSERT INTO weather_history (location_key, data, {}) VALUES (%s, %s, {}) ON CONFLICT DO NOTHING"
        ).format(
            sql.SQL(", ").join([sql.Identifier(col) for col in cols]),
            placeholders
        )

        records = []
        for _, row in combined.iterrows():
            date_val = row["data"].date() if hasattr(row["data"], "date") else row["data"]
            values = [key, date_val] + [row[col] for col in cols]
            records.append(tuple(values))

        cur.executemany(insert_sql, records)
        conn.commit()

    conn.close()
    return filename, combined