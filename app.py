import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
import os

# Configuração da página
st.set_page_config(page_title="Aztlas Heart - Visor Tático", layout="wide")

# 1. CONTROLE DE ACESSO NA BARRA LATERAL (Escudo do Mestre)
if "modo_mestre" not in st.session_state:
    st.session_state.modo_mestre = False

st.sidebar.title("🔑 RPG Access Control")

# Caixa para digitar a senha
senha = st.sidebar.text_input("Enter DM Password:", type="password")

# Validação da senha
if senha == "aztlas2026":
    st.session_state.modo_mestre = True
    st.sidebar.success("⚔️ Master Mode Active!")
else:
    st.session_state.modo_mestre = False

# 2. DEFINIÇÃO DAS ABAS (Aba do Mestre aparece condicionalmente)
abas_lista = ["Pokédex", "Itens", "World Map"]
if st.session_state.modo_mestre:
    abas_lista.append("🧙‍♂️ DM Panel")

abas = st.tabs(abas_lista)

# --- ABA 1: POKÉDEX ---
with abas[0]:
    st.title("📱 Pokédex Regional")
    st.write("Consulte os dados dos Pokémon da região de Aztlas aqui.")

# --- ABA 2: ITENS ---
with abas[1]:
    st.title("🎒 Inventário e Itens")
    st.write("Lista de itens, berries e equipamentos disponíveis.")

# --- ABA 3: TACTICAL MAP (Onde estava o erro de sintaxe) ---
with abas[2]:
    st.title("🗺️ Aztlas Tactical Visor")
    
    # Mensagem exclusiva da Visão de Mestre
    if st.session_state.modo_mestre:
        st.markdown("""
        <div style="background-color: #742a2a; color: #ffffff; padding: 12px; border-radius: 6px; border-left: 5px solid #feb2b2; margin-bottom: 15px;">
            <strong>👁️ VISÃO DE MESTRE:</strong> Dev Mode e notas confidenciais liberados.
        </div>
        """, unsafe_allow_html=True)

    # Divisão de Layout: Mapa na Esquerda, Scanner na Direita
    col_mapa, col_info = st.columns([2, 1])
    
    with col_mapa:
        st.subheader("Visualizador de Lentes")
        
        # Seleção do nível de zoom
        lente = st.selectbox("Selecione o nível de Lente (Zoom):", ["Full Map", "Half Map", "Quarter Map"])
        
        nome_arquivo_mapa = ""
        
        # Lógica de caminhos apontando para as subpastas estruturadas
        if lente == "Full Map":
            nome_arquivo_mapa = "Full/full_map.png"
            
        elif lente == "Half Map":
            metade = st.radio("Selecione a Metade:", ["Metade 1", "Metade 2"], horizontal=True)
            if metade == "Metade 1":
                nome_arquivo_mapa = "Half/half_map_1.png"
            else:
                nome_arquivo_mapa = "Half/half_map_2.png"
                
        elif lente == "Quarter Map":
            quadrante = st.selectbox("Selecione o Quadrante:", ["Noroeste (NW)", "Nordeste (NE)", "Sudoeste (SW)", "Sudeste (SE)"])
            if quadrante == "Noroeste (NW)":
                nome_arquivo_mapa = "Quarter/quarter_nw.png"
            elif quadrante == "Nordeste (NE)":
                nome_arquivo_mapa = "Quarter/quarter_ne.png"
            elif quadrante == "Sudoeste (SW)":
                nome_arquivo_mapa = "Quarter/quarter_sw.png"
            elif quadrante == "Sudeste (SE)":
                nome_arquivo_mapa = "Quarter/quarter_se.png"
        
        # Monta o caminho final na pasta mapas
        caminho_final = f"mapas/{nome_arquivo_mapa}"
        
        # Exibe o mapa clicável se o arquivo existir
        if os.path.exists(caminho_final):
            coordenadas = streamlit_image_coordinates(caminho_final, key=f"click_{nome_arquivo_mapa}")
        else:
            st.warning(f"⚠️ Arquivo não encontrado: `{caminho_final}`")
            st.info("Verifique se o arquivo está na subpasta correta no seu GitHub com letras correspondentes.")
            coordenadas = None
            
        # Calibrador visível apenas para o Mestre
        if st.session_state.modo_mestre and coordenadas:
            st.markdown("---")
            st.markdown("### 🛠️ Dev Mode: Calibrador")
            st.write(f"Caminho ativo: `{caminho_final}`")
            st.write(f"Clique em: **X:** `{coordenadas['x']}`, **Y:** `{coordenadas['y']}`")
            st.code(f"# Use para mapear este ponto:\n[X_min, X_max, Y_min, Y_max]")

    with col_info:
        st.subheader("🛰️ Scanner de Região")
        
        if coordenadas:
            x = coordenadas["x"]
            y = coordenadas["y"]
            
            # Exemplo de verificação de colisão/localização por mapa
            if "quarter_nw.png" in caminho_final and (50 <= x <= 150) and (50 <= y <= 150):
                st.markdown("### 🏕️ Acampamento Rebelde")
                st.write("Um ponto escondido nas montanhas do noroeste.")
            else:
                st.info(f"Coordenadas registradas em `{nome_arquivo_mapa}`: X={x}, Y={y}.")
        else:
            st.info("Clique no mapa para escanear a área.")

# --- ABA 4: PAINEL DO MESTRE (Apenas para quem sabe a senha) ---
if st.session_state.modo_mestre:
    with abas[-1]:
        st.title("🧙‍♂️ Escudo do Mestre")
        
        sub_combate, sub_lore, sub_regras = st.tabs(["⚔️ Combate", "📜 Lore Secreta", "📚 Regras da Mesa"])
        
        with sub_combate:
            st.subheader("Controle de Iniciativa e HP")
            st.write("Gerencie os status ocultos da batalha aqui.")
            
        with sub_lore:
            st.subheader("Notas Secretas da Campanha")
            st.write("Plots, reviravoltas e segredos que os jogadores ainda não sabem.")
            
        with sub_regras:
            st.subheader("Guia de Consulta Rápida")
            st.write("Tabelas de danos, condições e mecânicas da sua mesa.")
