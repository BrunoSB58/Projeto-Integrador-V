"""
frontend.py — StormWatch SP
Interface completa do usuário (UI/UX)
  • Sidebar com cadastro e exclusão
  • Busca de localidades
  • Visualização de previsões e gráficos
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

from backend import (
    search_location, build_weather_url,
    fetch_weather_data, process_weather_data,
    fetch_flood_data, forecast_storm, forecast_flood,
    update_historical_data, load_subscriptions, save_subscriptions,
    send_sms_alert, send_email_alert,
    remove_subscription_by_id,
)


# ════════════════════════════════════════════════════════════════════
#  CONFIGURAÇÕES E CONSTANTES
# ════════════════════════════════════════════════════════════════════

# Paleta de cores para gráficos Plotly
COR = {
    "baixo":    "#68d391",
    "moderado": "#f6e05e",
    "alto":     "#fc8181",
    "critico":  "#f56565",
    "azul":     "#63b3ed",
    "azul2":    "#2b6cb0",
    "laranja":  "#f6ad55",
}

PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(11,17,32,0.65)",
    font=dict(color="#a0aec0", family="Syne"),
    xaxis=dict(gridcolor="rgba(74,85,104,0.3)", zeroline=False),
    yaxis=dict(gridcolor="rgba(74,85,104,0.3)", zeroline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    margin=dict(l=10, r=10, t=40, b=10),
)


# ════════════════════════════════════════════════════════════════════
#  FUNÇÕES DE RENDERIZAÇÃO
# ════════════════════════════════════════════════════════════════════

def apply_custom_css():
    """Aplica CSS customizado para toda a interface"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] { font-family: 'Syne', sans-serif; }

    /* Hero */
    .hero {
        background: linear-gradient(135deg, #0b1120 0%, #111827 55%, #0d2540 100%);
        border: 1px solid rgba(99,179,237,0.2); border-radius: 18px;
        padding: 2.4rem 3rem 2rem; margin-bottom: 1.8rem;
        position: relative; overflow: hidden;
    }
    .hero::before {
        content: '⛈️'; font-size: 10rem; opacity: .05;
        position: absolute; right: 2.5rem; top: -1.5rem; line-height: 1;
    }
    .hero h1 {
        font-size: 2.6rem; font-weight: 800; margin: 0;
        background: linear-gradient(90deg, #63b3ed, #90cdf4, #bee3f8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero .sub  { color: #718096; margin: .4rem 0 .8rem; font-size: 1rem; }
    .hero .badge {
        display: inline-block;
        background: rgba(99,179,237,0.1); border: 1px solid rgba(99,179,237,0.3);
        border-radius: 20px; padding: .15rem .8rem;
        font-size: .75rem; color: #63b3ed; font-weight: 700; letter-spacing: .5px;
        margin-right: .4rem;
    }

    /* Cartão de localidade */
    .loc-card {
        background: linear-gradient(145deg,#1a2332,#111827);
        border: 1px solid rgba(99,179,237,0.22); border-radius: 12px;
        padding: 1rem 1.5rem; margin-bottom: .5rem;
    }
    .loc-name   { color: #e2e8f0; font-weight: 700; font-size: 1.05rem; }
    .loc-sub    { color: #4a5568; font-size: .82rem; margin: .1rem 0; }
    .loc-coords { font-family: 'DM Mono',monospace; color: #63b3ed; font-size: .75rem; }

    /* Alertas */
    .alerta-critico  { background:linear-gradient(135deg,#3d0f0f,#1a0505);
                       border:2px solid #f56565; border-radius:13px; padding:1.3rem 1.6rem; margin:.6rem 0; }
    .alerta-alto     { background:linear-gradient(135deg,#2d1a1a,#1a0f0f);
                       border:1.5px solid #fc8181; border-radius:13px; padding:1.3rem 1.6rem; margin:.6rem 0; }
    .alerta-moderado { background:linear-gradient(135deg,#2d2510,#1a1a08);
                       border:1.5px solid #f6e05e; border-radius:13px; padding:1.3rem 1.6rem; margin:.6rem 0; }
    .alerta-baixo    { background:linear-gradient(135deg,#0f2820,#081a0f);
                       border:1.5px solid #68d391; border-radius:13px; padding:1.3rem 1.6rem; margin:.6rem 0; }
    .alerta-titulo   { font-weight: 800; font-size: 1.08rem; margin-bottom: .3rem; }
    .alerta-texto    { color: #e2e8f0; font-size: .93rem; line-height: 1.5; }

    /* Section title */
    .sec-title {
        color: #63b3ed; font-weight: 700; font-size: 1.1rem;
        border-left: 3px solid #63b3ed; padding-left: .6rem;
        margin: 1.8rem 0 .8rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg,#0b1120 0%,#111827 100%);
        border-right: 1px solid rgba(99,179,237,0.08);
    }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #a0aec0 !important; }

    /* Inputs */
    input[type="text"], input[type="email"] { border-radius: 8px !important; }
    .campo-obrigatorio { color: #fc8181; font-size: .75rem; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)


def initialize_session_state():
    """Inicializa variáveis de estado da sessão"""
    for k, v in [("loc_results", []), ("selected_loc", None), ("loc_history", [])]:
        if k not in st.session_state:
            st.session_state[k] = v


def render_sidebar():
    """Renderiza a sidebar completa com cadastro e exclusão"""
    with st.sidebar:
        st.markdown("## ⛈️ StormWatch SP")

        # ── Cadastro de Alertas ─────────────────────────────────────
        st.markdown("### 📋 Cadastro de Alertas")

        loc_sidebar = st.session_state.get("selected_loc")
        opcoes_loc = list({l["display_name"] for l in st.session_state.get("loc_history", [])})
        if loc_sidebar and loc_sidebar["display_name"] not in opcoes_loc:
            opcoes_loc.insert(0, loc_sidebar["display_name"])

        st.markdown('<span class="campo-obrigatorio" style="font-size: .7rem;">★ Campos obrigatórios</span>',
                    unsafe_allow_html=True)

        # ✨ CORRIGIDO: Removido 'value', usando apenas 'key' para controle completo
        nome_cad = st.text_input(
            "👤 Nome completo",
            placeholder="Seu nome",
            key="cad_nome"
        )

        st.markdown("**📧 E-mail** &nbsp;<span class='campo-obrigatorio' style='font-size: .7rem;'>★ obrigatório</span>",
                    unsafe_allow_html=True)
        email_cad = st.text_input(
            "email_sidebar",
            label_visibility="collapsed",
            placeholder="seuemail@exemplo.com",
            key="cad_email"
        )

        tel_cad = st.text_input(
            "📱 Telefone (WhatsApp/SMS)",
            placeholder="+55 11 99999-9999",
            key="cad_tel"
        )

        # ✨ CORRIGIDO: Selectbox de tipo de alerta
        tipo_cad = st.selectbox(
            "🔔 Tipo de alerta",
            ["Ambos (Tempestade + Enchente)", "Apenas Tempestade", "Apenas Enchente"],
            key="cad_tipo"
        )

        st.markdown("**📍 Localidade para alerta** &nbsp;<span class='campo-obrigatorio' style='font-size: .7rem;'>★ obrigatório</span>",
                    unsafe_allow_html=True)

        if opcoes_loc:
            loc_cad = st.selectbox(
                "loc_cad_sidebar",
                opcoes_loc,
                label_visibility="collapsed",
                key="cad_loc"
            )
        else:
            loc_cad = st.text_input(
                "loc_cad_txt_sidebar",
                label_visibility="collapsed",
                placeholder="Pesquise uma localidade primeiro",
                key="cad_loc_txt"
            )

        tipo_map = {
            "Ambos (Tempestade + Enchente)": "ambos",
            "Apenas Tempestade": "tempestade",
            "Apenas Enchente":   "enchente",
        }

        # ✨ Botões lado a lado: Cadastrar e Limpar
        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            btn_cadastrar = st.button("✅ Cadastrar", use_container_width=True, type="primary", key="cad_btn")

        with col_btn2:
            btn_limpar = st.button("🧹 Limpar", use_container_width=True, type="secondary", key="btn_limpar")

        # ✨ CORRIGIDO: Lógica do botão Limpar (agora deleta as chaves, evitando StreamlitAPIException)
        if btn_limpar:
            # Remove as chaves dos widgets para que voltem aos seus valores padrão
            for chave in ["cad_nome", "cad_email", "cad_tel", "cad_tipo", "cad_loc", "cad_loc_txt"]:
                if chave in st.session_state:
                    del st.session_state[chave]

            # Limpa a mensagem de sucesso, se existir
            if "cadastro_sucesso" in st.session_state:
                del st.session_state["cadastro_sucesso"]

            # Recarrega para atualizar a interface
            st.rerun()

        # ✨ Lógica do botão Cadastrar
        if btn_cadastrar:
            if not email_cad:
                st.error("❌ O campo **E-mail** é obrigatório.")
            elif "@" not in email_cad or "." not in email_cad.split("@")[-1]:
                st.error("❌ Informe um **e-mail válido** (ex: nome@dominio.com).")
            elif not loc_cad:
                st.error("❌ Selecione ou pesquise uma **localidade** antes de cadastrar.")
            else:
                subs_df = load_subscriptions()
                ja_existe = ((subs_df["email"] == email_cad) &
                             (subs_df["localidade"] == loc_cad)).any()
                if ja_existe:
                    st.warning("⚠️ Este e-mail já está cadastrado para esta localidade.")
                else:
                    nova_linha = pd.DataFrame([{
                        "nome":        nome_cad.strip() if nome_cad else "",
                        "email":       email_cad.strip(),
                        "telefone":    tel_cad.strip() if tel_cad else "",
                        "localidade":  loc_cad,
                        "tipo_alerta": tipo_map.get(tipo_cad, "ambos"),
                    }])
                    cadastro_id = save_subscriptions(nova_linha)

                    # Armazena a mensagem de sucesso
                    st.session_state["cadastro_sucesso"] = {
                        "nome": nome_cad or email_cad,
                        "id": cadastro_id,
                        "tipo": tipo_cad.lower(),
                        "email": email_cad,
                        "localidade": loc_cad
                    }

                    # ✨ CORRIGIDO: Limpa os campos após cadastro (deletando as chaves)
                    for chave in ["cad_nome", "cad_email", "cad_tel", "cad_tipo", "cad_loc", "cad_loc_txt"]:
                        if chave in st.session_state:
                            del st.session_state[chave]

                    # Recarrega para limpar os campos visualmente e mostrar o sucesso
                    st.rerun()

        # Exibe a mensagem de sucesso se existir
        if st.session_state.get("cadastro_sucesso"):
            sucesso = st.session_state["cadastro_sucesso"]
            st.success(
                f"✅ **{sucesso['nome']}** cadastrado com sucesso!\n\n"
                f"🆔 **Seu código de ID: {sucesso['id']}**\n\n"
                f"📝 **IMPORTANTE:** Anote este código! Ele será necessário para cancelar o cadastro.\n\n"
                f"Alertas de **{sucesso['tipo']}** serão enviados para "
                f"**{sucesso['email']}** sobre **{sucesso['localidade']}**."
            )
            st.info("💡 Use o botão **🧹 Limpar** acima para limpar a mensagem e fazer um novo cadastro.")

        st.markdown("---")

        # ── Cancelar Cadastro ────────────────────────────────────────
        st.markdown("### 🗑️ Cancelar Cadastro de Alertas")
        st.caption("Digite o código ID recebido no cadastro:")

        # Campo de texto para ID alfanumérico
        id_para_excluir = st.text_input(
            "Código ID",
            placeholder="Ex: A7K3P2",
            key="id_excluir",
            label_visibility="collapsed",
            max_chars=10
        ).strip().upper()

        if st.button("🗑️ Excluir Cadastro", use_container_width=True, type="secondary", key="btn_excluir"):
            if id_para_excluir:
                resultado = remove_subscription_by_id(id_para_excluir)

                if resultado["success"]:
                    dados = resultado["dados"]
                    st.success(resultado["message"])
                    st.info(
                        f"**Dados removidos:**\n"
                        f"- ID: {dados['id']}\n"
                        f"- Nome: {dados['nome'] or 'Não informado'}\n"
                        f"- E-mail: {dados['email']}\n"
                        f"- Localidade: {dados['localidade']}"
                    )
                else:
                    st.error(resultado["message"])
            else:
                st.warning("⚠️ Digite um código ID válido (ex: A7K3P2).")

        st.markdown("---")

        # ── Horizonte de previsão ────────────────────────────────────
        st.markdown("### 🔭 Horizonte de Previsão")
        forecast_period = st.selectbox(
            "Dias", ("1", "3", "7"), index=2,
            format_func=lambda x: f"{x} dia{'s' if x != '1' else ''}",
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.markdown("""
        <small style='color:#4a5568'>
        <b>Dados:</b> CETESB - Open-Meteo Forecast API<br>
        <b>Histórico:</b> 90 dias (3 meses)<br>
        <b>Enchentes:</b> Open-Meteo Flood API (GloFAS)<br>
        <b>Histórico Rios:</b> 180 dias (6 meses)<br>
        <b>Geocoding:</b> CETESB (apenas SP)<br>
        <b>Alertas:</b> Twilio SMS + SendGrid E-mail<br><br>
        Nenhuma chave de API necessária para dados.
        </small>
        """, unsafe_allow_html=True)

        return forecast_period

def render_header():
    """Renderiza o cabeçalho principal"""
    st.markdown("""
    <div class="hero">
      <h1>⛈️ StormWatch SP</h1>
      <p class="sub">Previsão de <strong>tempestades</strong> e <strong>enchentes</strong>
         com Inteligência Artificial — CETESB - Open-Meteo API</p>
      <span class="badge">📍 Estado de São Paulo</span>
      <span class="badge">🌊 Flood API GloFAS</span>
      <span class="badge">🤖 ML em tempo real</span>
    </div>
    """, unsafe_allow_html=True)


def render_location_search():
    """Renderiza seção de busca de localidade"""
    st.markdown('<div class="sec-title">🔍 Buscar Localidades no Estado de São Paulo</div>', unsafe_allow_html=True)

    col_input, col_btn = st.columns([5, 1])
    with col_input:
        query = st.text_input(
            "busca", label_visibility="collapsed",
            placeholder="Pesquise por Cidades ou Distritos - Ex: Capão Redondo  |  Guarulhos  |  Campinas  |  Santos  |  Sorocaba",
        )
    with col_btn:
        buscar = st.button("🔍 Buscar", use_container_width=True, type="primary")

    st.caption("🗺️ Pesquisa limitada ao **estado de São Paulo, Brasil** — Os resultados são filtrados das estações da CETESB.")

    if buscar and query:
        with st.spinner("Pesquisando localidades no estado de São Paulo..."):
            resultados = search_location(query, count=10)
        if resultados:
            st.session_state.loc_results = resultados
        else:
            st.warning(
                "⚠️ Nenhuma localidade encontrada no estado de São Paulo. "
                "Verifique o nome digitado ou tente um bairro / município próximo."
            )
            st.session_state.loc_results = []


def render_location_results():
    """Renderiza resultados da busca de localidade"""
    if st.session_state.loc_results:
        st.markdown('<div class="sec-title">📍 Selecione a localidade</div>', unsafe_allow_html=True)
        opcoes  = [r["display_name"] for r in st.session_state.loc_results]
        escolha = st.selectbox("Localidade encontrada", opcoes, label_visibility="collapsed")
        loc_obj = next((r for r in st.session_state.loc_results if r["display_name"] == escolha), None)

        if loc_obj:
            st.markdown(f"""
            <div class="loc-card">
              <div class="loc-name">📍 {loc_obj['name']}</div>
              <div class="loc-sub">{loc_obj.get('admin1','')} &nbsp;·&nbsp; {loc_obj.get('country','Brasil')}</div>
              <div class="loc-coords">Lat: {loc_obj['lat']:.4f} &nbsp;|&nbsp; Lon: {loc_obj['lon']:.4f}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"✔️ Analisar  '{loc_obj['name']}'", use_container_width=True):
                st.session_state.selected_loc = loc_obj
                if loc_obj not in st.session_state.loc_history:
                    st.session_state.loc_history.append(loc_obj)
                st.session_state.loc_results = []
                st.rerun()


def render_kpis(df_weather, df_flood):
    """Renderiza KPIs principais"""
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("🌧️ Chuva total (período)",    f"{df_weather['rain_sum'].sum():.1f} mm")
    k2.metric("📅 Acumulado 7 dias",         f"{df_weather['precip_acum_7d'].iloc[-1]:.1f} mm")
    k3.metric("🌡️ Temp. máx. média",         f"{df_weather['temperature_2m_max'].mean():.1f} °C")
    k4.metric("💧 Umidade média",            f"{df_weather['relative_humidity_2m_mean'].mean():.0f} %")
    k5.metric("🌊 Descarga do rio (atual)" if df_flood is not None else "💨 Vento máx. médio",
              f"{df_flood['river_discharge'].iloc[-1]:.1f} m³/s"
              if df_flood is not None else
              f"{df_weather['windspeed_10m_max'].mean():.1f} km/h")


def render_forecast_tab(df_weather, df_flood, loc):
    """Renderiza aba de previsão IA"""
    storm = forecast_storm(df_weather)
    flood = forecast_flood(df_weather, df_flood)

    COR_NIVEL = {"critico": "#f56565", "alto": "#fc8181",
                 "moderado": "#f6e05e", "baixo": "#68d391", "sem_dados": "#718096"}

    col_s, col_f = st.columns(2)

    # ── Tempestade ────────────────────────────────────
    with col_s:
        st.markdown("#### ⛈️ Previsão de Tempestade")
        n = storm["nivel"]
        css = f"alerta-{n}" if n in COR_NIVEL else "alerta-baixo"
        titulo = {"critico": "🚨 TEMPESTADE SEVERA", "alto": "⛈️ TEMPESTADE",
                  "moderado": "🌧️ CHUVA MODERADA",   "baixo": "☀️ SEM RISCO",
                  "sem_dados": "ℹ️ SEM DADOS"}
        st.markdown(f"""
        <div class="{css}">
          <div class="alerta-titulo" style="color:{COR_NIVEL.get(n,'#718096')}">{titulo.get(n,'')}</div>
          <div class="alerta-texto">{storm['mensagem']}</div>
        </div>
        """, unsafe_allow_html=True)

        if storm["chuva_prevista"] is not None:
            m1, m2 = st.columns(2)
            m1.metric("💧 Chuva prevista (ML)", f"{storm['chuva_prevista']} mm")
            if storm["prob_chuva"] is not None:
                m2.metric("☔ Prob. precipitação", f"{storm['prob_chuva']:.0f}%")

    # ── Enchente ──────────────────────────────────────
    with col_f:
        st.markdown("#### 🌊 Previsão de Enchente")
        fn = flood["nivel"]
        css_f = f"alerta-{fn}" if fn in COR_NIVEL else "alerta-baixo"
        titulo_f = {"critico": "🚨 ENCHENTE CRÍTICA",     "alto": "🌊 RISCO ALTO DE ENCHENTE",
                    "moderado": "⚠️ RISCO MODERADO",       "baixo": "✅ SEM RISCO DE ENCHENTE",
                    "sem_dados": "ℹ️ SEM DADOS"}
        st.markdown(f"""
        <div class="{css_f}">
          <div class="alerta-titulo" style="color:{COR_NIVEL.get(fn,'#718096')}">{titulo_f.get(fn,'')}</div>
          <div class="alerta-texto">{flood['mensagem']}</div>
        </div>
        """, unsafe_allow_html=True)

        if flood["acum_7d"] is not None:
            m3, m4 = st.columns(2)
            m3.metric("🌧️ Acumulado 7 dias", f"{flood['acum_7d']} mm")
            if flood["discharge_atual"] is not None:
                m4.metric("🌊 Descarga do rio", f"{flood['discharge_atual']} m³/s")

    # ── Gráfico probabilidades ────────────────────────
    if flood.get("prob_classes"):
        st.markdown('<div class="sec-title">Probabilidades por Nível de Risco — Enchente (Modelo GBR)</div>',
                    unsafe_allow_html=True)
        pc  = flood["prob_classes"]
        fig_prob = go.Figure(go.Bar(
            x=["✅ Baixo", "⚠️ Moderado", "🌊 Alto", "🚨 Crítico"],
            y=[pc.get(0,0), pc.get(1,0), pc.get(2,0), pc.get(3,0)],
            marker_color=[COR["baixo"], COR["moderado"], COR["alto"], COR["critico"]],
            text=[f"{v:.1f}%" for v in [pc.get(0,0), pc.get(1,0), pc.get(2,0), pc.get(3,0)]],
            textposition="outside",
        ))
        fig_prob.update_layout(PLOTLY_BASE)
        fig_prob.update_layout(height=280,
                               yaxis=dict(range=[0,115], title="%",
                                          gridcolor="rgba(74,85,104,0.3)"))
        st.plotly_chart(fig_prob, use_container_width=True)

    # ── Envio de alertas ──────────────────────────────
    s_critico = storm["nivel"] in ("alto", "critico")
    f_critico = flood["nivel"] in ("alto", "critico")
    if s_critico or f_critico:
        subs_df = load_subscriptions()
        target  = subs_df[subs_df["localidade"] == loc["display_name"]]
        if not target.empty:
            with st.expander(f"📢 Enviar alertas para {len(target)} inscrito(s)"):
                if st.button("🚀 Enviar alertas agora", type="primary"):
                    for _, row in target.iterrows():
                        tipo = str(row.get("tipo_alerta", "ambos")).lower()
                        msgs = []
                        if tipo in ("ambos", "tempestade") and s_critico:
                            msgs.append(storm["mensagem"])
                        if tipo in ("ambos", "enchente") and f_critico:
                            msgs.append(flood["mensagem"])
                        if not msgs:
                            continue
                        msg_txt = " | ".join(msgs)
                        r_sms = send_sms_alert(row["telefone"], msg_txt)
                        r_email = send_email_alert(
                            row["email"], "⛈️ Alerta StormWatch SP",
                            f"<strong>{msg_txt}</strong>",
                        )
                        st.write(f"SMS → {row['telefone']}: {'✅' if r_sms['success'] else '❌ '+r_sms.get('error','')}")
                        st.write(f"E-mail → {row['email']}: {'✅' if r_email['success'] else '❌ '+r_email.get('error','')}")
        else:
            st.info(f"ℹ️ Nenhum inscrito cadastrado para **{loc['name']}**. Use a barra lateral para se cadastrar.")


def render_precipitation_tab(df_history):
    """Renderiza aba de precipitação"""
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        x=df_history["data"], y=df_history["rain_sum"],
        name="Chuva diária (mm)",
        marker=dict(color=df_history["rain_sum"],
                    colorscale=[[0,"#1a2332"],[.5,COR["azul2"]],[1,COR["azul"]]]),
    ))
    if "precipitation_probability_max" in df_history.columns:
        fig1.add_trace(go.Scatter(
            x=df_history["data"], y=df_history["precipitation_probability_max"],
            name="Prob. chuva (%)", yaxis="y2",
            line=dict(color=COR["moderado"], width=2, dash="dot"),
        ))
        fig1.update_layout(yaxis2=dict(
            title="%", overlaying="y", side="right", range=[0,100],
            gridcolor="rgba(0,0,0,0)"))
    if "precip_acum_7d" in df_history.columns:
        fig1.add_trace(go.Scatter(
            x=df_history["data"], y=df_history["precip_acum_7d"],
            name="Acumulado 7d (mm)", line=dict(color=COR["laranja"], width=2),
        ))
    fig1.update_layout(**PLOTLY_BASE, height=420,
                       title="Precipitação Diária e Probabilidade de Chuva",
                       yaxis_title="mm")
    st.plotly_chart(fig1, use_container_width=True)


def render_temperature_tab(df_history):
    """Renderiza aba de temperatura"""
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_history["data"], y=df_history["temperature_2m_max"],
        name="Temp. Máx.", fill="tonexty",
        line=dict(color=COR["alto"], width=2),
        fillcolor="rgba(252,129,129,0.08)"))
    if "temperature_2m_mean" in df_history.columns:
        fig2.add_trace(go.Scatter(
            x=df_history["data"], y=df_history["temperature_2m_mean"],
            name="Temp. Média", line=dict(color=COR["moderado"], width=1.5, dash="dot")))
    fig2.add_trace(go.Scatter(
        x=df_history["data"], y=df_history["temperature_2m_min"],
        name="Temp. Mín.", line=dict(color=COR["azul"], width=2)))
    fig2.update_layout(**PLOTLY_BASE, height=380, title="Temperatura (°C)", yaxis_title="°C")
    st.plotly_chart(fig2, use_container_width=True)


def render_humidity_tab(df_history):
    """Renderiza aba de umidade e vento"""
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df_history["data"], y=df_history["relative_humidity_2m_mean"],
        name="Umidade (%)", fill="tozeroy",
        line=dict(color=COR["azul"], width=2),
        fillcolor="rgba(99,179,237,0.10)"))
    if "windspeed_10m_max" in df_history.columns:
        fig3.add_trace(go.Scatter(
            x=df_history["data"], y=df_history["windspeed_10m_max"],
            name="Vento máx. (km/h)", yaxis="y2",
            line=dict(color=COR["baixo"], width=2)))
        fig3.update_layout(yaxis2=dict(
            title="km/h", overlaying="y", side="right",
            gridcolor="rgba(0,0,0,0)"))
    fig3.update_layout(**PLOTLY_BASE, height=380, title="Umidade e Velocidade do Vento",
                       yaxis_title="%")
    st.plotly_chart(fig3, use_container_width=True)


def render_river_tab(df_flood):
    """Renderiza aba de dados de rios"""
    if df_flood is not None and not df_flood.empty:
        hoje       = pd.Timestamp.now().normalize()
        df_f_hist  = df_flood[df_flood["data"] <  hoje]
        df_f_fore  = df_flood[df_flood["data"] >= hoje]

        fig_r = go.Figure()
        if not df_f_hist.empty:
            fig_r.add_trace(go.Scatter(
                x=df_f_hist["data"], y=df_f_hist["river_discharge"],
                name="Histórico (m³/s)", fill="tozeroy",
                line=dict(color=COR["azul"], width=2),
                fillcolor="rgba(99,179,237,0.10)"))
        if not df_f_fore.empty:
            fig_r.add_trace(go.Scatter(
                x=df_f_fore["data"], y=df_f_fore["river_discharge"],
                name="Previsão GloFAS (m³/s)",
                line=dict(color=COR["laranja"], width=2.5, dash="dot"),
                mode="lines+markers", marker=dict(size=7)))

        q80 = float(df_flood["river_discharge"].quantile(0.80))
        q95 = float(df_flood["river_discharge"].quantile(0.95))
        fig_r.add_hline(y=q80, line_dash="dash", line_color=COR["alto"],
                        annotation_text="Limiar Alto (P80)", annotation_position="top left")
        fig_r.add_hline(y=q95, line_dash="dash", line_color=COR["critico"],
                        annotation_text="Limiar Crítico (P95)", annotation_position="top left")

        fig_r.update_layout(**PLOTLY_BASE, height=440,
                            title="Descarga de Rio — Histórico + Previsão (Open-Meteo Flood API / GloFAS)",
                            yaxis_title="m³/s")
        st.plotly_chart(fig_r, use_container_width=True)
        st.caption(
            f"Percentis calculados sobre **{len(df_flood)}** dias de dados. "
            "P80 = risco alto · P95 = risco crítico."
        )
    else:
        st.info("🌊 Dados de descarga de rios não disponíveis para esta localidade.")
        st.markdown(
            "A Open-Meteo Flood API (GloFAS) pode não cobrir todos os pontos do estado de SP — "
            "principalmente em bacias pequenas ou urbanas sem monitoramento hidráulico ativo. "
            "Mesmo sem os dados de rios, o modelo de enchente ainda usa a precipitação acumulada."
        )


def render_footer(df_history, csv_filename):
    """Renderiza rodapé com download e histórico"""
    st.markdown("---")
    col_dl, col_hist = st.columns([1, 2])
    with col_dl:
        csv_data = df_history.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar CSV Meteorológico", data=csv_data,
            file_name=csv_filename.split("/")[-1], mime="text/csv",
            use_container_width=True,
        )
    with col_hist:
        if st.session_state.loc_history:
            st.caption("**Localidades pesquisadas nesta sessão:**")
            st.caption("  ·  ".join(l["display_name"] for l in st.session_state.loc_history))

    st.markdown("""
    <p style='text-align:center;color:#2d3748;font-size:.76rem;margin-top:1.5rem'>
    ⛈️ <strong>StormWatch SP</strong>
    · Forecast: <a href='https://open-meteo.com' target='_blank' style='color:#4a5568'>Open-Meteo API</a>
    · Enchentes: <a href='https://open-meteo.com/en/docs/flood-api' target='_blank' style='color:#4a5568'>Open-Meteo Flood API (GloFAS)</a>
    · Alertas: Twilio SMS + SendGrid E-mail
    </p>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  FUNÇÃO PRINCIPAL DE RENDERIZAÇÃO
# ════════════════════════════════════════════════════════════════════

def render_app():
    """Função principal que orquestra toda a renderização da interface"""

    # Configurações iniciais
    st_autorefresh(interval=86_400_000, key="datarefresh")
    apply_custom_css()
    initialize_session_state()

    # Sidebar
    forecast_period = render_sidebar()

    # Header
    render_header()

    # Busca de localidade
    render_location_search()
    render_location_results()

    # Análise da localidade selecionada
    loc = st.session_state.selected_loc

    if loc is None:
        st.info("👆 Pesquise e selecione uma cidade ou bairro do estado de São Paulo para iniciar.")
        return

    st.markdown("---")
    st.markdown(f'<div class="sec-title">🌍 Analisando: {loc["display_name"]}</div>',
                unsafe_allow_html=True)

    fd = int(forecast_period)

    # Busca dados
    with st.spinner("🌦️ Buscando dados meteorológicos..."):
        json_data  = fetch_weather_data(build_weather_url(loc["lat"], loc["lon"], fd))
        df_weather = process_weather_data(json_data)

    with st.spinner("🌊 Buscando dados de rios (Open-Meteo Flood API / GloFAS)..."):
        df_flood = fetch_flood_data(loc["lat"], loc["lon"], fd)

    if df_weather is None:
        st.error("❌ Não foi possível obter dados meteorológicos. Tente novamente.")
        return

    csv_filename, df_history = update_historical_data(df_weather, loc["display_name"])

    c_ok, c_ts = st.columns([3, 1])
    c_ok.success(
        f"✅ **{loc['name']}** — dados carregados"
        + ("  |  🌊 Dados de rios disponíveis" if df_flood is not None else "  |  🌊 Sem dados de rios neste ponto")
    )
    c_ts.caption(f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # KPIs
    render_kpis(df_weather, df_flood)

    # Abas
    tab_ia, tab_precip, tab_temp, tab_hum, tab_rios = st.tabs([
        "🤖 Previsão IA",
        "🌧️ Precipitação",
        "🌡️ Temperatura",
        "💧 Umidade & Vento",
        "🌊 Dados de Rios",
    ])

    with tab_ia:
        render_forecast_tab(df_weather, df_flood, loc)

    with tab_precip:
        render_precipitation_tab(df_history)

    with tab_temp:
        render_temperature_tab(df_history)

    with tab_hum:
        render_humidity_tab(df_history)

    with tab_rios:
        render_river_tab(df_flood)

    # Rodapé
    render_footer(df_history, csv_filename)