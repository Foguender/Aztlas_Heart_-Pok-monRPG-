import os
import sqlite3
import datetime
import pandas as pd
import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates

# Configuração Básica da Página
st.set_page_config(page_title="Aztlas-Heart - Visor Tático", page_icon="❤️", layout="wide")

# --- 1. CONTROLE DE ACESSO (SESSÃO E SIDEBAR) ---
if "dm_mode" not in st.session_state:
    st.session_state.dm_mode = False

st.sidebar.title("🔐 Aztlas Control")
master_password = st.sidebar.text_input("Senha do Mestre:", type="password")

if master_password == "Dusk_0256":
    st.session_state.dm_mode = True
    st.sidebar.success("🧙‍♂️ Modo Mestre Ativado!")
else:
    st.session_state.dm_mode = False
    if master_password:
        st.sidebar.error("Senha incorreta.")

# --- 2. ESTRUTURA DE ABAS ---
tabs_list = ["Pokédex", "Itens", "World Map"]
if st.session_state.dm_mode:
    tabs_list.append("🧙‍♂️ DM Panel")

tab_pokedex, tab_itens, tab_map, *tab_dm = st.tabs(tabs_list)

# --- 3. CONEXÃO COM O BANCO DE DADOS (POKÉDEX) ---
DB_NAME = "pokedex aztlas - Copia.db"

@st.cache_data
def carregar_dados_pokedex():
    if not os.path.exists(DB_NAME):
        return None
    try:
        conn = sqlite3.connect(DB_NAME)
        df_pokemon = pd.read_sql_query("SELECT * FROM pokemon", conn)
        df_stats = pd.read_sql_query("SELECT * FROM [Base Stats]", conn)
        df_desc = pd.read_sql_query("SELECT * FROM descricao_pokedexrpg", conn)
        conn.close()
        
        # Unificando as tabelas com base na chave 'Nome'
        df_merged = pd.merge(df_pokemon, df_stats, on="Nome", how="inner")
        df_final = pd.merge(df_merged, df_desc, on="Nome", how="inner")
        
        # Garantindo a ordenação estrita pelo ID numérico
        df_final['Dex No.'] = pd.to_numeric(df_final['Dex No.'], errors='coerce').fillna(999).astype(int)
        df_final = df_final.sort_values(by='Dex No.').reset_index(drop=True)
        return df_final
    except Exception as e:
        st.error(f"Erro ao ler banco de dados: {e}")
        return None

df_pokedex = carregar_dados_pokedex()

# --- ABA 1: POKÉDEX ---
with tab_pokedex:
    st.header("📊 Visor de Dados Pokédex")
    if df_pokedex is not None:
        # Formatação do Selectbox: "[Nº 001] Nome (Tipo 1 / Tipo 2)"
        options = []
        for idx, row in df_pokedex.iterrows():
            tipo2 = f" / {row['Tipo 2']}" if 'Tipo 2' in row and pd.notna(row['Tipo 2']) and row['Tipo 2'] != "" else ""
            label = f"[Nº {int(row['Dex No.']):03d}] {row['Nome']} ({row['Tipo 1']}{tipo2})"
            options.append((label, idx))
        
        selected_label, selected_idx = st.selectbox(
            "Selecionar Pokémon:", 
            options, 
            format_func=lambda x: x[0]
        )
        
        poke_data = df_pokedex.iloc[selected_idx]
        
        # Exibição dos Dados Layoutados
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("📋 Dados Físicos & Biologia")
            st.markdown(f"**Espécie:** {poke_data.get('Especie', 'Desconhecida')}")
            st.markdown(f"**Altura:** {poke_data.get('Altura', '--')} m | **Peso:** {poke_data.get('Peso', '--')} kg")
            st.info(f"**Descrição:**\n\n{poke_data.get('Descricao', 'Sem biologia registrada.')}")
            
        with col2:
            st.subheader("⚔️ Atributos de Combate Base")
            # Mapeamento padrão dos 6 atributos de Pokémon
            stats_list = ['HP', 'Attack', 'Defense', 'Sp. Atk', 'Sp. Def', 'Speed']
            
            for stat in stats_list:
                val = poke_data.get(stat, 0)
                st.markdown(f"**{stat}:** {val}")
                st.progress(min(int(val) / 255, 1.0))
    else:
        st.warning(f"Banco de dados '{DB_NAME}' não encontrado ou vazio. Verifique o arquivo no diretório raiz.")

# --- ABA 2: ITENS (MERCADO COM PREÇOS FLUTUANTES) ---
with tab_itens:
    st.header("🎒 Mercado do Moço dos Itens")
    
    # Dicionário Base de Itens
    itens_db = {
        "Poké Ball": 200,
        "Great Ball": 600,
        "Ultra Ball": 1200,
        "Potion": 300,
        "Super Potion": 700,
        "Hyper Potion": 1500,
        "Revive": 2000,
        "Antidote": 100
    }
    
    # Cálculo do modificador de tempo real
    agora = datetime.datetime.now()
    hora = agora.hour
    dia_semana = agora.weekday() # 5 = Sábado, 6 = Domingo
    
    modificador = 1.0
    motivo = "Preço Padrão de Mercado"
    
    if 0 <= hora < 6:
        modificador += 0.35
        motivo = "Madrugada Alucinante (+35%)"
    elif 12 <= hora < 14:
        modificador -= 0.10
        motivo = "Horário de Almoço (-10%)"
        
    if dia_semana >= 5:
        modificador += 0.15
        motivo += " + Inflação de Fim de Semana (+15%)"

    if st.session_state.dm_mode:
        st.caption(f"**[Mestre] Alerta do Servidor:** {motivo} | Multiplicador Atual: x{modificador:.2f}")
        
        # Tabela avançada para o Mestre
        dados_tabela = []
        for item, preco_base in itens_db.items():
            preco_final = max(1, int(preco_base * modificador))
            dados_tabela.append({"Item": item, "Preço Base": f"${preco_base}", "Preço Calculado": f"${preco_final}"})
        st.table(pd.DataFrame(dados_tabela))
    else:
        # Visão comum simplificada para Jogadores
        st.markdown("### Itens Disponíveis para Compra")
        for item, preco_base in itens_db.items():
            preco_final = max(1, int(preco_base * modificador))
            st.write(f"🔹 **{item}**: ${preco_final}")

# --- ABA 3: WORLD MAP (COM COORDENADAS) ---
with tab_map:
    st.header("🗺️ Navegação Cartográfica de Aztlas")
    
    # Escolha do Zoom / Nível de Divisão
    map_zoom = st.selectbox("Nível de Zoom do Mapa:", ["Full", "Half", "Quarter"])
    
    # Sistema de busca de caminhos baseados em subpastas estruturadas
    caminho_mapa = f"mapas/{map_zoom}/mapa.png"
    
    # Contingência manual caso o arquivo de imagem não seja encontrado
    if not os.path.exists(caminho_mapa):
        st.error(f"Arquivo não localizado em: `{caminho_mapa}`")
        st.info("⚠️ Ativando plano de contingência manual. Faça o upload do mapa correspondente abaixo:")
        uploaded_file = st.file_uploader(f"Envie o mapa para [{map_zoom}]", type=["png", "jpg", "jpeg"])
        if uploaded_file:
            with open("mapa_contingencia.png", "wb") as f:
                f.write(uploaded_file.getbuffer())
            caminho_mapa = "mapa_contingencia.png"
            
    if os.path.exists(caminho_mapa):
        st.subheader("Clique no mapa para rastrear as coordenadas da sua equipe:")
        
        # Renderização interativa da imagem e captura dos cliques
        coords = streamlit_image_coordinates(caminho_mapa, key=f"map_{map_zoom}")
        
        if coords:
            st.success(f"📍 Posição Detectada -> X: {coords['x']} | Y: {coords['y']}")
            
            # Dev Mode para calibração rápida exclusivo do mestre
            if st.session_state.dm_mode:
                st.write("---")
                st.subheader("🔧 Painel de Calibração (Dev Mode)")
                st.code(f"# Copie este valor para registrar pontos de interesse:\n\"ponto_interesse\": ({coords['x']}, {coords['y']})", language="python")

# --- ABA BONUS: PAINEL EXCLUSIVO DO DM ---
if st.session_state.dm_mode:
    with tab_dm[0]:
        st.header("🧙‍♂️ Painel de Operações Ocultas")
        st.subheader("Escudo do Mestre & Comandos Rápidos")
        st.warning("Esta aba é invisível para usuários comuns sem a chave correspondente.")
        
        # Exemplo de utilitários rápidos para o mestre
        st.text_input("Notas rápidas da sessão:")
        st.slider("Dificuldade do Próximo Encontro (Nível de Perigo):", 1, 10, 5)
