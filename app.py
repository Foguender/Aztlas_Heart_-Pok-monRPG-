import streamlit as st
import pandas as pd
import sqlite3
import os
from streamlit_image_coordinates import streamlit_image_coordinates

# Configuração inicial da página (Deve ser o primeiro comando Streamlit)
st.set_page_config(
    layout="wide", 
    page_title="Aztlas-Heart // Tactical Visor", 
    page_icon="🔮"
)

# ------------------------------------------------------------------
# 1. INICIALIZAÇÃO DE ESTADOS (Session State)
# ------------------------------------------------------------------
if "modo_mestre" not in st.session_state:
    st.session_state.modo_mestre = False

# Banco de dados fictício/estrutural para a Pokédex e Itens
DB_NAME = "pokedex.db"

# ------------------------------------------------------------------
# 2. CONTROLE DE ACESSO NA BARRA LATERAL
# ------------------------------------------------------------------
st.sidebar.title("🔮 Aztlas-Heart")
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 Painel de Acesso")

# Campo de senha mascarado
senha = st.sidebar.text_input("Senha do Mestre:", type="password")

if senha == "Dusk_0256":  # Você pode alterar sua senha aqui
    st.session_state.modo_mestre = True
    st.sidebar.success("⚔️ Modo Mestre Ativo!")
else:
    st.session_state.modo_mestre = False
    if senha != "":
        st.sidebar.error("Senha incorreta.")

st.sidebar.markdown("---")
st.sidebar.info("Modo Jogador ativo por padrão. Recursos confidenciais estão ocultos.")

# ------------------------------------------------------------------
# 3. ESTRUTURAÇÃO DINÂMICA DAS ABAS
# ------------------------------------------------------------------
abas_disponiveis = ["🐾 Pokédex", "🎒 Itens & Equipamentos", "🗺️ Tactical Map"]

# Se o Mestre estiver logado, a aba secreta é adicionada
if st.session_state.modo_mestre:
    abas_disponiveis.append("🧙‍♂️ Escudo do Mestre")

# Renderiza as abas na interface
abas = st.tabs(abas_disponiveis)

# ------------------------------------------------------------------
# ABA 1: POKÉDEX REGIONAL
# ------------------------------------------------------------------
with abas[0]:
    st.title("🐾 Pokédex Regional de Aztlas")
    st.markdown("Consulte as criaturas catalogadas e suas fraquezas conhecidas.")
    
    # [INSIRA AQUI O SEU CÓDIGO DA POKÉDEX]
    # Exemplo visual estruturado:
    st.info("Espaço reservado para a listagem e busca do seu banco de dados de Pokémon.")
    
# ------------------------------------------------------------------
# ABA 2: ITENS & EQUIPAMENTOS
# ------------------------------------------------------------------
with abas[1]:
    st.title("🎒 Inventário do Grupo")
    st.markdown("Gerenciamento de itens, consumíveis e artefatos lendários.")
    
    # [INSIRA AQUI O SEU CÓDIGO DE ITENS]
    # Exemplo visual estruturado:
    st.info("Espaço reservado para a sua tabela ou sistema de busca de Itens da mochila.")

# ------------------------------------------------------------------
# ABA 3: TACTICAL MAP (VISOR DE MAPAS & INTERAÇÃO)
# ------------------------------------------------------------------
with abas[2]:
    st.title("🗺️ Aztlas Tactical Visor")
    
    # Mensagem secreta no mapa para o Mestre
    if st.session_state.modo_mestre:
        st.markdown("""
        <div style="background-color: #742a2a; color: #ffffff; padding: 12px; border-radius: 6px; border-left: 5px solid #feb2b2; margin-bottom: 15px;">
            <strong>👁️ VISÃO DE MESTRE:</strong> Há uma armadilha ativa e um evento climático secreto planejado para o quadrante SE.
        </div>
        """, unsafe_allow_html=True)

    # Divisão de layout: Mapa na Esquerda, Informações na Direita
    col_mapa, col_info = st.columns([2, 1])
    
    with col_mapa:
        st.subheader("Visualizador de Lentes")
        lente = st.selectbox("Selecione o nível de Zoom (Lente):", ["Full Map", "Half Map", "Quarter Map"])
        
        # Define o arquivo de imagem com base na lente escolhida
        caminho_mapa = f"mapas/{lente.lower().replace(' ', '_')}.png"
        
        # Fallback caso a imagem ainda não exista localmente/no GitHub
        if os.path.exists(caminho_mapa):
            # Captura o clique nas coordenadas da imagem
            coordenadas = streamlit_image_coordinates(caminho_mapa, key=f"mapa_{lente}")
        else:
            st.warning(f"Insira o arquivo de imagem em: `{caminho_mapa}` para ativar o mapa interativo.")
            coordenadas = None
            
        # Ferramenta de Calibração (Dev Mode) automática para o Mestre
        if st.session_state.modo_mestre and coordenadas:
            st.markdown("---")
            st.markdown("### 🛠️ Dev Mode: Calibrador de Bounding Boxes")
            st.write(f"Último clique registrado: **X:** `{coordenadas['x']}`, **Y:** `{coordenadas['y']}`")
            st.code(f"# Use estas coordenadas para montar suas caixas de colisão:\n[X_min, X_max, Y_min, Y_max]")

    with col_info:
        st.subheader("🛰️ Scanner de Região")
        
        if coordenadas:
            x = coordenadas["x"]
            y = coordenadas["y"]
            
            # --------------------------------------------------------------
            # LOGICA DE BOUNDING BOXES (Exemplo Prático)
            # --------------------------------------------------------------
            # Se o clique estiver dentro do intervalo X e Y configurado:
            if (100 <= x <= 250) and (150 <= y <= 300):
                st.markdown("### 🏔️ Cidade Inicial: Neo-Aztlas")
                st.write("Uma metrópole tecnológica cercada por muralhas antigas.")
                st.metric(label="População", value="12.500")
                st.metric(label="Alinhamento", value="Neutro")
                
                if st.session_state.modo_mestre:
                    st.error("⚠️ NOTA DO MESTRE: A guilda dos ladrões controla os subterrâneos daqui.")
            
            elif (400 <= x <= 600) and (50 <= y <= 200):
                st.markdown("### 🌲 Floresta dos Murmúrios")
                st.write("Uma densa mata onde bússolas falham e sons estranhos ecoam.")
                st.warning("Efeito Ativo: Visibilidade Reduzida (-2 em testes de Percepção).")
            
            else:
                st.markdown("### 🏜️ Terras Desconhecidas")
                st.write(f"Coordenadas atuais mapeadas pelo Visor: X:{x}, Y:{y}.")
                st.info("Nenhum ponto de interesse descoberto ou configurado neste quadrante ainda.")
        else:
            st.info("Clique em qualquer ponto do mapa à esquerda para escanear a região correspondente.")

# ------------------------------------------------------------------
# ABA 4: ESCUDO DO MESTRE (EXCLUSIVA E CONDICIONAL)
# ------------------------------------------------------------------
if st.session_state.modo_mestre:
    with abas[3]:
        st.title("🧙‍♂️ Escudo do Mestre (DM Screen)")
        st.markdown("Acesso rápido a ferramentas de controle de jogo sem compartilhar com os players.")
        
        # Sub-abas para organizar o escudo
        sub_combate, sub_lore, sub_regras = st.tabs([
            "⚔️ Controle de Combate", 
            "📜 Enredo & Segredos (Markdown)", 
            "📖 Consulta Rápida de Regras"
        ])
        
        # Sub-aba 1: Painel de Combate Ativo
        with sub_combate:
            st.subheader("⚡ Monitor de Vida dos Inimigos")
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.markdown("#### 👾 Monstro A")
                hp_a = st.number_input("HP Inimigo A", min_value=0, value=60, key="dm_hp_a")
                st.progress(min(hp_a / 60, 1.0) if hp_a > 0 else 0.0)
                st.selectbox("Status", ["Normal", "Paralisado", "Envenenado"], key="st_a")
                
            with c2:
                st.markdown("#### 👾 Monstro B")
                hp_b = st.number_input("HP Inimigo B", min_value=0, value=60, key="dm_hp_b")
                st.progress(min(hp_b / 60, 1.0) if hp_b > 0 else 0.0)
                st.selectbox("Status", ["Normal", "Paralisado", "Envenenado"], key="st_b")
                
            with c3:
                st.markdown("#### 👑 Boss da Sessão")
                hp_boss = st.number_input("HP Boss", min_value=0, value=250, key="dm_hp_boss")
                st.progress(min(hp_boss / 250, 1.0) if hp_boss > 0 else 0.0)
                st.selectbox("Status", ["Normal", "Queimado", "Confuso"], key="st_boss")

        # Sub-aba 2: Leitor do Arquivo de Lore Externo
        with sub_lore:
            st.subheader("📖 Notas Estruturadas da Campanha")
            
            nome_arquivo_notas = "secret_notes.md"
            
            if os.path.exists(nome_arquivo_notas):
                with open(nome_arquivo_notas, "r", encoding="utf-8") as arquivo:
                    conteudo_secreto = arquivo.read()
                st.markdown(conteudo_secreto)
            else:
                st.warning(f"O arquivo `{nome_arquivo_notas}` não foi encontrado na pasta raiz.")
                st.info("Crie um arquivo chamado `secret_notes.md` para escrever o enredo livremente usando Markdown.")

        # Sub-aba 3: Tabelas de consulta rápida
        with sub_regras:
            st.subheader("📊 Tabelas Auxiliares")
            
            with st.expander("🍂 Regras de Condições Rápidas"):
                st.markdown("""
                * **Envenenado:** Perde vida a cada rodada de combate.
                * **Paralisado:** Chance de perder o turno de ação.
                * **Dormindo:** Incapaz de agir até sofrer dano ou acordar.
                """)
                
            with st.expander("💰 Tabela de Preços de Suprimentos"):
                dados_precos = {
                    "Item de Suporte": ["Basic Ball", "Mega Ball", "Potion", "Super Potion"],
                    "Custo (₽)": [200, 600, 300, 700],
                    "Efeito Esperado": ["Captura normal", "Captura +50%", "Cura 20 HP", "Cura 60 HP"]
                }
                st.dataframe(pd.DataFrame(dados_precos), use_container_width=True, hide_index=True)
