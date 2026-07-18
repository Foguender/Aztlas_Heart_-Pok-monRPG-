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
            <strong>👁️ VISÃO DE MESTRE:</strong> Os segredos e ferramentas de calibração estão visíveis para você.
        </div>
        """, unsafe_allow_html=True)

    # Divisão de layout: Mapa na Esquerda, Informações na Direita
    col_mapa, col_info = st.columns([2, 1])
    
    with col_mapa:
        st.subheader("Visualizador de Lentes")
        
        # 1. Seleção do nível geral de zoom
        lente = st.selectbox("Selecione o nível de Lente (Zoom):", ["Full Map", "Half Map", "Quarter Map"])
        
        # Variável para guardar o nome exato do arquivo final
        nome_arquivo_mapa = ""
        
        # 2. Lógica adaptada para as subdivisões reais das imagens
        if lente == "Full Map":
            nome_arquivo_mapa = "MApa Aztlas (1).png"
            
        elif lente == "Half Map":
            # 2 Imagens: Leste ou Oeste, Norte ou Sul (ajuste as opções conforme você nomeou os arquivos)
            metade = st.radio("Selecione a Metade:", ["Metade 1 (Oeste)", "Metade 2 (Leste)"], horizontal=True)
            if metade == "Metade 1 (Oeste)":
                nome_arquivo_mapa = "MApa Aztlas (2) - Half Left.png"
            else:
                nome_arquivo_mapa = "MApa Aztlas (2) - Half Right.png"
                
        elif lente == "Quarter Map":
            # 4 Imagens: Os 4 quadrantes clássicos
            quadrante = st.selectbox("Selecione o Quadrante:", ["Noroeste (NW)", "Nordeste (NE)", "Sudoeste (SW)", "Sudoeste (SE)"])
            # Transforma a seleção no nome do seu arquivo (ex: quarter_nw.png)
            sufixo = quadrante.split("(")[1].replace(")", "").lower().strip()
            nome_arquivo_mapa = f"quarter_{sufixo}.png"
        
        # Monta o caminho final para o Streamlit buscar na pasta
        caminho_final = f"mapas/{nome_arquivo_mapa}"
        
        # 3. Renderização e captura do clique
        if os.path.exists(caminho_final):
            # O key muda dinamicamente baseado no arquivo para não dar conflito no Streamlit
            coordenadas = streamlit_image_coordinates(caminho_final, key=f"click_{nome_arquivo_mapa}")
        else:
            st.warning(f"⚠️ Arquivo não encontrado no GitHub: `{caminho_final}`")
            st.info("Verifique se o nome do arquivo na sua pasta 'mapas' está exatamente igual ao listado acima.")
            coordenadas = None
            
        # Ferramenta de Calibração (Dev Mode) automática para o Mestre
        if st.session_state.modo_mestre and coordenadas:
            st.markdown("---")
            st.markdown("### 🛠️ Dev Mode: Calibrador")
            st.write(f"Mapa ativo: `{nome_arquivo_mapa}`")
            st.write(f"Clique registrado: **X:** `{coordenadas['x']}`, **Y:** `{coordenadas['y']}`")
            st.code(f"# Bounding Box para este clique específico:\n[X_min, X_max, Y_min, Y_max]")

    with col_info:
        st.subheader("🛰️ Scanner de Região")
        
        if coordenadas:
            x = coordenadas["x"]
            y = coordenadas["y"]
            
            # Aqui entra a sua checagem de Bounding Boxes. 
            # Como agora temos mapas diferentes, você pode filtrar pelo mapa ativo:
            st.write(f"Buscando pontos no mapa `{nome_arquivo_mapa}`...")
            
            # EXEMPLO: Se o clique foi no Quadrante Noroeste (quarter_nw.png)
            if nome_arquivo_mapa == "quarter_nw.png" and (50 <= x <= 150) and (50 <= y <= 150):
                st.markdown("### 🏕️ Acampamento Rebelde")
                st.write("Um ponto escondido usado por treinadores renegados.")
            else:
                st.info(f"Coordenadas registradas neste clique: X={x}, Y={y}. Nenhum segredo mapeado aqui ainda.")
        else:
            st.info("Clique em qualquer ponto do mapa ativo para escanear a área.")

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
