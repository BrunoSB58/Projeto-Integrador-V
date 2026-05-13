"""
monitor_alertas_postgresql.py — StormWatch SP
Versão adaptada para backend com PostgreSQL

DIFERENÇAS DA VERSÃO ORIGINAL:
  • Funciona com load_subscriptions() que retorna DataFrame (não lista)
  • Usa latitude/longitude da tabela subscriptions
  • Compatível com send_email_alert(email, subject, html_message)
  • Compatível com send_sms_alert(phone, message)
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd

from backend import (
    build_weather_url,
    fetch_weather_data,
    process_weather_data,
    fetch_flood_data,
    forecast_storm,
    forecast_flood,
    load_subscriptions,
    send_sms_alert,
    send_email_alert,
    search_location,
)

# ════════════════════════════════════════════════════════════════════
#  CONFIGURAÇÃO
# ════════════════════════════════════════════════════════════════════

INTERVALO_VERIFICACAO = 3600  # 1 hora
HORARIOS_VERIFICACAO = ["06:00", "12:00", "18:00", "21:00"]
NIVEIS_ALERTA = ["alto", "critico"]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitor_alertas.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════
#  VERIFICAÇÃO E ENVIO DE ALERTAS
# ════════════════════════════════════════════════════════════════════

def verificar_e_enviar_alertas() -> Dict[str, Any]:
    """
    Função principal que:
    1. Carrega todos os cadastros do PostgreSQL
    2. Verifica previsões para cada localidade
    3. Envia alertas quando necessário
    """
    logger.info("=" * 70)
    logger.info("INICIANDO VERIFICAÇÃO DE ALERTAS")
    logger.info("=" * 70)
    
    estatisticas = {
        "total_cadastros": 0,
        "alertas_enviados": 0,
        "erros": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # 1. Carregar cadastros (retorna DataFrame)
        df_subs = load_subscriptions()
        estatisticas["total_cadastros"] = len(df_subs)
        
        if df_subs.empty:
            logger.warning("Nenhum cadastro encontrado.")
            return estatisticas
        
        logger.info(f"📋 {len(df_subs)} cadastro(s) encontrado(s)")
        
        # 2. Verificar se há coordenadas no banco
        tem_coordenadas = 'latitude' in df_subs.columns and 'longitude' in df_subs.columns
        
        if not tem_coordenadas:
            logger.warning("⚠️ ATENÇÃO: Colunas latitude/longitude não encontradas!")
            logger.warning("   Execute: ALTER TABLE subscriptions ADD COLUMN latitude DECIMAL(10,6), ADD COLUMN longitude DECIMAL(10,6);")
            logger.warning("   Tentando buscar coordenadas via API (mais lento)...")
        
        # 3. Converter DataFrame para lista de dicts
        subs = df_subs.to_dict('records')
        
        # 4. Agrupar por localidade
        cadastros_por_loc = {}
        
        for sub in subs:
            localidade = sub["localidade"]
            
            # Obter coordenadas
            if tem_coordenadas and pd.notna(sub.get("latitude")) and pd.notna(sub.get("longitude")):
                lat = float(sub["latitude"])
                lon = float(sub["longitude"])
            else:
                # Buscar via API (fallback)
                logger.info(f"   🔍 Buscando coordenadas para {localidade}...")
                locs = search_location(localidade)
                if not locs:
                    logger.warning(f"   ⚠️ Coordenadas não encontradas para {localidade}")
                    continue
                lat = locs[0]["lat"]
                lon = locs[0]["lon"]
            
            loc_key = (lat, lon)
            
            if loc_key not in cadastros_por_loc:
                cadastros_por_loc[loc_key] = {
                    "localidade": localidade,
                    "lat": lat,
                    "lon": lon,
                    "cadastros": []
                }
            
            cadastros_por_loc[loc_key]["cadastros"].append(sub)
        
        logger.info(f"📍 {len(cadastros_por_loc)} localidade(s) única(s)")
        
        # 5. Processar cada localidade
        for loc_info in cadastros_por_loc.values():
            try:
                processar_localidade(loc_info, estatisticas)
            except Exception as e:
                logger.error(f"❌ Erro ao processar {loc_info['localidade']}: {e}")
                estatisticas["erros"] += 1
        
        # 6. Resumo
        logger.info("=" * 70)
        logger.info("RESUMO DA EXECUÇÃO:")
        logger.info(f"  • Cadastros verificados: {estatisticas['total_cadastros']}")
        logger.info(f"  • Alertas enviados: {estatisticas['alertas_enviados']}")
        logger.info(f"  • Erros: {estatisticas['erros']}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        estatisticas["erros"] += 1
    
    return estatisticas


def processar_localidade(loc_info: Dict[str, Any], stats: Dict[str, Any]) -> None:
    """
    Processa uma localidade específica:
    1. Busca dados meteorológicos
    2. Executa previsões
    3. Envia alertas
    """
    localidade = loc_info["localidade"]
    lat = loc_info["lat"]
    lon = loc_info["lon"]
    cadastros = loc_info["cadastros"]
    
    logger.info(f"\n🌍 Verificando: {localidade}")
    logger.info(f"   Coordenadas: ({lat:.4f}, {lon:.4f})")
    logger.info(f"   {len(cadastros)} cadastro(s) nesta localidade")
    
    # 1. Buscar dados meteorológicos
    url_weather = build_weather_url(lat, lon, forecast_days=7)
    raw_weather = fetch_weather_data(url_weather)
    
    if not raw_weather:
        logger.warning(f"   ⚠️ Falha ao buscar dados meteorológicos")
        return
    
    df_weather = process_weather_data(raw_weather)
    
    if df_weather is None or df_weather.empty:
        logger.warning(f"   ⚠️ Dados meteorológicos vazios")
        return
    
    # 2. Buscar dados de vazão
    df_flood = fetch_flood_data(lat, lon, forecast_days=7)
    
    # 3. Executar previsões
    prev_tempestade = forecast_storm(df_weather)
    prev_enchente = forecast_flood(df_weather, df_flood)
    
    logger.info(f"   🌩️ Tempestade: {prev_tempestade['nivel'].upper()}")
    logger.info(f"   🌊 Enchente: {prev_enchente['nivel'].upper()}")
    
    # 4. Verificar se deve alertar
    deve_alertar_tempestade = prev_tempestade["nivel"] in NIVEIS_ALERTA
    deve_alertar_enchente = prev_enchente["nivel"] in NIVEIS_ALERTA
    
    if not (deve_alertar_tempestade or deve_alertar_enchente):
        logger.info(f"   ✅ Sem riscos críticos - nenhum alerta necessário")
        return
    
    # 5. Enviar alertas
    for cad in cadastros:
        try:
            enviar_alerta_para_cadastro(cad, prev_tempestade, prev_enchente)
            stats["alertas_enviados"] += 1
        except Exception as e:
            logger.error(f"   ❌ Erro ao enviar para {cad.get('nome', 'N/A')}: {e}")
            stats["erros"] += 1


def enviar_alerta_para_cadastro(
    cadastro: Dict[str, Any],
    prev_tempestade: Dict[str, Any],
    prev_enchente: Dict[str, Any]
) -> None:
    """
    Envia alerta para um cadastro específico
    """
    tipo = cadastro.get("tipo_alerta", "").lower()
    nome = cadastro.get("nome", "Usuário")
    email = cadastro.get("email", "")
    telefone = cadastro.get("telefone", "")
    localidade = cadastro.get("localidade", "")
    
    # Verificar qual tipo de alerta enviar
    alertas_para_enviar = []
    
    if tipo in ["tempestade", "ambos"]:
        if prev_tempestade["nivel"] in NIVEIS_ALERTA:
            alertas_para_enviar.append(("tempestade", prev_tempestade))
    
    if tipo in ["enchente", "ambos"]:
        if prev_enchente["nivel"] in NIVEIS_ALERTA:
            alertas_para_enviar.append(("enchente", prev_enchente))
    
    if not alertas_para_enviar:
        return
    
    # Montar mensagem
    mensagem_texto = f"⚠️ ALERTA StormWatch SP\n\n"
    mensagem_texto += f"📍 {localidade}\n"
    mensagem_texto += f"👤 {nome}\n\n"
    
    mensagem_html = f"<h2>⚠️ ALERTA StormWatch SP</h2>"
    mensagem_html += f"<p><strong>📍 {localidade}</strong></p>"
    mensagem_html += f"<p>👤 {nome}</p>"
    
    for tipo_alerta, previsao in alertas_para_enviar:
        mensagem_texto += f"{previsao['mensagem']}\n\n"
        mensagem_html += f"<p>{previsao['mensagem']}</p>"
    
    timestamp_str = datetime.now().strftime('%d/%m/%Y às %H:%M')
    mensagem_texto += f"🕐 Verificado em: {timestamp_str}\n"
    mensagem_texto += f"\n⚡ Este é um alerta automático do StormWatch SP"
    
    mensagem_html += f"<p><small>🕐 Verificado em: {timestamp_str}</small></p>"
    mensagem_html += f"<p><small>⚡ Este é um alerta automático do StormWatch SP</small></p>"
    
    # Enviar por email
    if email:
        try:
            nivel_max = max(
                [p["nivel"] for _, p in alertas_para_enviar],
                key=lambda x: ["baixo", "moderado", "alto", "critico"].index(x)
            )
            assunto = f"🚨 ALERTA: {nivel_max.upper()} - {localidade}"
            
            resultado = send_email_alert(email, assunto, mensagem_html)
            
            if resultado.get("success"):
                logger.info(f"   📧 Email enviado para {email}")
            else:
                logger.error(f"   ❌ Falha no email: {resultado.get('error', 'Erro desconhecido')}")
                
        except Exception as e:
            logger.error(f"   ❌ Erro ao enviar email: {e}")
    
    # Enviar por SMS
    if telefone:
        try:
            # Limitar mensagem SMS (máx 160 caracteres)
            mensagem_sms = mensagem_texto[:160]
            
            resultado = send_sms_alert(telefone, mensagem_sms)
            
            if resultado.get("success"):
                logger.info(f"   📱 SMS enviado para {telefone}")
            else:
                logger.error(f"   ❌ Falha no SMS: {resultado.get('error', 'Erro desconhecido')}")
                
        except Exception as e:
            logger.error(f"   ❌ Erro ao enviar SMS: {e}")


# ════════════════════════════════════════════════════════════════════
#  SCHEDULERS
# ════════════════════════════════════════════════════════════════════

def executar_continuamente():
    """
    Executa verificações em intervalo regular
    """
    logger.info("🚀 Monitor iniciado em modo CONTÍNUO")
    logger.info(f"⏱️  Intervalo: {INTERVALO_VERIFICACAO}s ({INTERVALO_VERIFICACAO/3600:.1f}h)")
    
    while True:
        try:
            verificar_e_enviar_alertas()
        except Exception as e:
            logger.error(f"❌ Erro no loop: {e}")
        
        logger.info(f"\n⏳ Aguardando {INTERVALO_VERIFICACAO}s...")
        time.sleep(INTERVALO_VERIFICACAO)


def executar_em_horarios():
    """
    Executa apenas em horários específicos
    """
    logger.info("🚀 Monitor iniciado em modo HORÁRIOS ESPECÍFICOS")
    logger.info(f"⏱️  Horários: {', '.join(HORARIOS_VERIFICACAO)}")
    
    while True:
        hora_atual = datetime.now().strftime("%H:%M")
        
        if hora_atual in HORARIOS_VERIFICACAO:
            logger.info(f"⏰ Horário de verificação: {hora_atual}")
            try:
                verificar_e_enviar_alertas()
            except Exception as e:
                logger.error(f"❌ Erro: {e}")
            time.sleep(61)
        else:
            time.sleep(60)


# ════════════════════════════════════════════════════════════════════
#  ENTRADA PRINCIPAL
# ════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor StormWatch SP")
    parser.add_argument("--once", action="store_true", help="Executa uma vez")
    parser.add_argument("--horarios", action="store_true", help="Usa horários específicos")
    
    args = parser.parse_args()
    
    try:
        if args.once:
            logger.info("🧪 Modo TESTE (uma vez)")
            verificar_e_enviar_alertas()
            logger.info("✅ Teste concluído")
        elif args.horarios:
            executar_em_horarios()
        else:
            executar_continuamente()
    except KeyboardInterrupt:
        logger.info("\n⏹️  Monitor interrompido")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        sys.exit(1)
