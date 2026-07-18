import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
import os
import random
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Aztlas Heart - Visor Tático", layout="wide")

# 1. CONTROLE DE ACESSO NA BARRA LATERAL (Nova Senha Atualizada)
if "modo_mestre" not in st.session_state:
    st.session_state.modo_mestre = False

st.sidebar.title("🔑 RPG Access Control")

# Caixa para digitar a senha secreta
senha = st.sidebar.text_input("Enter DM Password:", type="password")

if senha == "Dusk_0256":
    st.session_state.modo_mestre = True
    st.sidebar.success("⚔️ Master Mode Active!")
else:
    st.session_state.modo_mestre = False

# 2. DEFINIÇÃO DAS ABAS
abas_lista = ["Pokédex", "Itens", "World Map"]
if st.session_state.modo_mestre:
    abas_lista.append("🧙‍♂️ DM Panel")

abas = st.tabs(abas_lista)

# --- ABA 1: POKÉDEX ---
with abas[0]:
    st.title("📱 Pokédex Regional")
    st.write("Consulte os dados dos Pokémon da região de Aztlas aqui.")

# --- ABA 2: ITENS (Mercado Dinâmico com Flutuação de Preço) ---
with abas[1]:
    st.title("🎒 Inventário e Mercado")
    
    # Banco de dados simulado de itens (substitua ou conecte com seu .db depois)
    banco_itens = {
        "Pokébola": {"preco_base": 200, "descricao": "Dispositivo básico de captura."},
        "Superbola": {"preco_base": 600, "descricao": "Dispositivo com maior taxa de captura."},
        "Ultra-bola": {"preco_base": 1200, "descricao": "Dispositivo de alta performance para capturas difíceis."},
        "Poção": {"preco_base": 300, "descricao": "Restaura 20 de HP de um Pokémon."},
        "Super Poção": {"preco_base": 700, "descricao": "Restaura 50 de HP de um Pokémon."},
        "Reviver": {"preco_base": 1500, "descricao": "Revive um Pokémon desmaiado com metade do HP."},
    }
    
    # Jogadores veem apenas a listagem comum ou descrição simples se você quiser
    st.write("Bem-vindo ao catálogo de suprimentos de Aztlas.")
    
    # VISÃO EXCLUSIVA DO MESTRE NO VISOR DE ITENS
    if st.session_state.modo_mestre:
        st.markdown("---")
        st.markdown("### 🛒 Visor do Mestre: Precificação em Tempo Real")
        st.caption("Esta seção calcula custos variáveis automaticamente sem expor tabelas aos players.")
        
        # Sistema de flutuação baseado na hora e dia real
        agora = datetime.now()
        hora_atual = agora.hour
        dia_semana = agora.weekday() # 0 = Segunda, 5 = Sábado, 6 = Domingo
        
        # Lógica de mercado: Itens ficam mais caros de madrugada (escassez) ou finais de semana
        multiplicador = 1.0
        motivo_flutua = "Preço regular de mercado."
        
        if 0 <= hora_atual <= 6:
            multiplicador = 1.35
            motivo_flutua = "⚠️ Inflação de Madrugada (+35% de custo pelo horário alternativo)"
        elif dia_semana >= 5:
            multiplicador = 1.15
            motivo_flutua = "📈 Alta Demanda de Fim de Semana (+15% no comércio regional)"
        elif 12 <= hora_atual <= 14:
            multiplicador = 0.90
            motivo_flutua = "📉 Promoção de Horário de Almoço (-10% de desconto)"

        st.info(f"📅 **Status do Mercado Atual:** {motivo_flutua} | Servidor: {hora_atual:02d}h")
        
        # Campo de pesquisa direta sem mostrar tabela
        item_pesquisado = st.selectbox("Pesquisar Item no Acervo do Mestre:", ["-- Selecione um Item --"] + list(banco_itens.keys()))
        
        if item_pesquisado != "-- Selecione um Item --":
            dados = banco_itens[item_pesquisado]
            preco_calculado = int(dados["preco_base"] * multiplicador)
            
            # Layout limpo exibindo os detalhes do item computado
            st.markdown(f"#### 📦 {item_pesquisado}")
            st.write(f"*{dados['descricao']}*")
            
            c1, c2 = st.columns(2)
            c1.metric(label="Preço Comercial Flutuante", value=f"{preco_calculado}₽")
            c2.metric(label="Preço Base (Fixo)", value=f"{dados['preco_base']}₽", delta=f"{preco_calculado - dados['preco_base']}₽")
    else:
        # Visão padrão do jogador: Apenas lista simples sem valores ocultos ou dinâmicos
        st.write("Consulte o Mestre da mesa para saber a disponibilidade e os valores atuais das lojas locais.")

# --- ABA 3: TACTICAL MAP (Correção dos seletores de subpastas) ---
with abas[2]:
    st.title("🗺️ Aztlas Tactical Visor")
    
    if st.session_state.modo_mestre:
        st.markdown("""
        <div style="background-color: #742a2a; color: #ffffff; padding: 12px; border-radius: 6px; border-left: 5px solid #feb2b2; margin-bottom: 15px;">
            <strong>👁️ VISÃO DE MESTRE:</strong> Lentes táticas e Dev Mode operacionais.
        </div>
        """, unsafe_allow_html=True)

    col_mapa, col_info = st.columns([2, 1])
    
    with col_mapa:
        st.subheader("Visualizador de Lentes")
        
        lente = st.selectbox("Selecione o nível de Lente (Zoom):", ["Full Map", "Half Map", "Quarter Map"])
        
        nome_subpasta = ""
        arquivo_selecionado = ""
        
        # Ajuste dinâmico de pastas conforme seu projeto
        if lente == "Full Map":
            nome_subpasta = "Full"
            arquivo_selecionado = "full_map.png"
            
        elif lente == "Half Map":
            nome_subpasta = "Half"
            # Radio para o usuário alternar livremente entre os 2 arquivos reais da pasta
            opcao_half = st.radio("Selecione o arquivo da metade correspondente:", ["Arquivo 1", "Arquivo 2"], horizontal=True)
            arquivo_selecionado = "half_map_1.png" if opcao_half == "Arquivo 1" else "half_map_2.png"
                
        elif lente == "Quarter Map":
            nome_subpasta = "Quarter"
            # Lista para alternar livremente entre as 4 partes reais da pasta
            opcao_quarter = st.selectbox("Selecione o arquivo do quadrante correspondente:", ["Quadrante 1", "Quadrante 2", "Quadrante 3", "Quadrante 4"])
            mapeamento_quarter = {
                "Quadrante 1": "quarter_nw.png",
                "Quadrante 2": "quarter_ne.png",
                "Quadrante 3": "quarter_sw.png",
                "Quadrante 4": "quarter_se.png"
            }
            arquivo_selecionado = mapeamento_quarter[opcao_quarter]
        
        # Montagem do caminho
        caminho_final = f"mapas/{nome_subpasta}/{arquivo_selecionado}"
        
        if os.path.exists(caminho_final):
            coordenadas = streamlit_image_coordinates(caminho_final, key=f"click_{lente}_{arquivo_selecionado}")
        else:
            # Caso os nomes internos ainda variem, exibe um campo de texto alternativo para não quebrar a sessão
            st.error(f"❌ Arquivo não encontrado em: `{caminho_final}`")
            st.info("Caso tenha mudado os nomes internos das imagens, use o campo abaixo para carregar manualmente:")
            arquivo_manual = st.text_input("Digite o nome exato do arquivo com a extensão (ex: mapa_novo.png):", value=arquivo_selecionado)
            caminho_final = f"mapas/{nome_subpasta}/{arquivo_manual}"
            
            if os.path.exists(caminho_final):
                coordenadas = streamlit_image_coordinates(caminho_final, key="click_manual")
            else:
                coordenadas = None
            
        # Calibrador Dev Mode
        if st.session_state.modo_mestre and coordenadas:
            st.markdown("---")
            st.markdown("### 🛠️ Dev Mode: Calibrador")
            st.write(f"Caminho ativo no servidor: `{caminho_final}`")
            st.write(f"Clique registrado em: **X:** `{coordenadas['x']}`, **Y:** `{coordenadas['y']}`")

    with col_info:
        st.subheader("🛰️ Scanner de Região")
        
        if coordenadas:
            x = coordenadas["x"]
            y = coordenadas["y"]
            st.info(f"Sinal escaneado no arquivo `{arquivo_selecionado}`. Coordenadas estáveis: X={x}, Y={y}.")
        else:
            st.info("Clique em um ponto do mapa ativo para calibrar ou ler o setor.")

# --- ABA 4: PAINEL DO MESTRE ---
if st.session_state.modo_mestre:
    with abas[-1]:
        st.title("🧙‍♂️ Escudo do Mestre")
        sub_combate, sub_lore, sub_regras = st.tabs(["⚔️ Combate", "📜 Lore Secreta", "📚 Regras da Mesa"])
        
        with sub_combate:
            st.write("Controle de Iniciativa e HP ativos.")
        with sub_lore:
            st.write("Acessando arquivos secretos de lore `.md`.")
        with sub_regras:
            st.write("Tabelas de consulta rápida de dados de Aztlas.")
