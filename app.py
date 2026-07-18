import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
import os
import sqlite3
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Aztlas Heart - Visor Tático", layout="wide")

# --- FUNÇÃO AUXILIAR: CARREGAMENTO DA POKÉDEX DO SCRIPT SQLite ---
def carregar_dados_pokedex():
    # Caminho ajustado para o banco de dados que está no seu repositório
    caminho_db = "pokedex aztlas - Copia.db"
    
    if not os.path.exists(caminho_db):
        return None, f"Arquivo `{caminho_db}` não encontrado na raiz do projeto."
        
    try:
        conn = sqlite3.connect(caminho_db)
        
        # 1. Carrega dados fundamentais (Nome, Tipo, Tamanho, Habilidades)
        df_poke = pd.read_sql_query("SELECT * FROM pokemon", conn)
        
        # 2. Carrega as descrições customizadas do seu RPG (Espécie e Biologia)
        df_desc = pd.read_sql_query("SELECT Nome, Espécie, Descrição FROM descricao_pokedexrpg", conn)
        
        # 3. Carrega os Atributos de Combate (Base Stats)
        df_stats = pd.read_sql_query("SELECT * FROM 'Base Stats'", conn)
        
        conn.close()
        
        # Garante a limpeza de strings para um merge limpo e sem falhas ocultas
        for df in [df_poke, df_desc, df_stats]:
            if "Nome" in df.columns:
                df["Nome"] = df["Nome"].astype(str).str.strip()
                
        # Junta todas as tabelas usando o "Nome" como chave de ligação universal
        df_completo = pd.merge(df_poke, df_desc, on="Nome", how="left")
        df_completo = pd.merge(df_completo, df_stats, on="Nome", how="left")
        
        return df_completo, None
    except Exception as e:
        return None, str(e)


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

# --- ABA 1: POKÉDEX REGIONAL (DINÂMICA VIA SQLITE) ---
# --- ABA 1: POKÉDEX REGIONAL (FORMATO LISTA COMPLETA) ---
with abas[0]:
    st.title("📱 Pokédex Regional de Aztlas")
    
    # Processa o banco de dados real enviado
    df_pokedex, erro_db = carregar_dados_pokedex()
    
    if erro_db:
        st.error(f"❌ Falha ao acionar a Pokédex: {erro_db}")
        st.info("Verifique se o arquivo do banco está commitado com o nome exato na raiz do seu GitHub.")
    elif df_pokedex is not None and not df_pokedex.empty:
        # Limpeza inicial de nulos
        df_pokedex = df_pokedex.dropna(subset=["Nome"])
        df_pokedex = df_pokedex[df_pokedex["Nome"] != ""]
        
        # Converte o campo 'Dex No.' para numérico para garantir a ordenação matemática correta (1, 2, 10 em vez de 1, 10, 2)
        df_pokedex["Dex No. Numérico"] = pd.to_numeric(df_pokedex["Dex No."], errors='coerce').fillna(999)
        
        # --- Formatação da linha de exibição ---
        def formatar_linha_selecao(linha):
            num = int(linha["Dex No. Numérico"])
            num_str = f"{num:03d}" if num != 999 else "???"
            nome = linha.get("Nome", "Desconhecido")
            t1 = linha.get("Tipo 1", "???")
            t2 = linha.get("Tipo 2", "")
            
            tipos = f"{t1}" + (f" / {t2}" if t2 and pd.notna(t2) else "")
            return f"[Nº {num_str}] {nome} ({tipos})"

        # Cria a coluna de exibição e ordena estritamente pelo ID numérico
        df_pokedex["Exibicao"] = df_pokedex.apply(formatar_linha_selecao, axis=1)
        df_pokedex = df_pokedex.sort_values(by="Dex No. Numérico", ascending=True)
        lista_exibicao = df_pokedex["Exibicao"].unique().tolist()
        
        opcao_selecionada = st.selectbox("Escanear assinatura de energia:", ["-- Selecione um Pokémon --"] + lista_exibicao)
        
        if opcao_selecionada != "-- Selecione um Pokémon --":
            # Resgata a linha correta cruzando com a coluna de Exibição
            poke_dados = df_pokedex[df_pokedex["Exibicao"] == opcao_selecionada].iloc[0]
            pokemon_selecionado = poke_dados["Nome"]
            
            # Cabeçalho da Dex
            num_dex = str(poke_dados.get("Dex No.", "???")).split('.')[0]
            st.markdown(f"## {pokemon_selecionado} `Nº {num_dex}`")
            
            # Tipagem formatada em badges
            t1 = poke_dados.get("Tipo 1", "???")
            t2 = poke_dados.get("Tipo 2", None)
            tipos_str = f"`{t1}`" + (f" / `{t2}`" if t2 and pd.notna(t2) else "")
            
            st.markdown(f"**Tipo:** {tipos_str} | **Espécie:** *{poke_dados.get('Espécie', 'Não catalogada')}*")
            
            # Métricas Físicas e Habilidades
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Altura", f"{poke_dados.get('Altura', '??')} m")
            with c2:
                st.metric("Peso", f"{poke_dados.get('Peso', '??')} kg")
            with c3:
                h1 = poke_dados.get("Habilidade 1", "Nenhuma")
                he = poke_dados.get("Habilidade E", None)
                st.markdown(f"**Habilidade:** {h1}")
                if he and pd.notna(he):
                    st.markdown(f"**Oculta:** {he}")
                    
            st.markdown("---")
            
            # Biologia / Lore Secreta da tabela do RPG
            st.subheader("📜 Registro Biológico")
            desc_bio = poke_dados.get("Descrição", "Nenhum dado biológico inserido para este espécime.")
            st.info(desc_bio)
            
            # Status Base de Combate extraídos do SQL
            if "HP" in poke_dados.columns:
                st.subheader("📊 Atributos de Combate (Base Stats)")
                col_stats = st.columns(6)
                stats_lista = ["HP", "Atk", "Def", "Sp. Atk", "Sp. Def", "Spe"]
                
                for idx, stat_nome in enumerate(stats_lista):
                    with col_stats[idx]:
                        val = poke_dados.get(stat_nome, 0)
                        st.metric(label=stat_nome, value=int(val) if pd.notna(val) else 0)
    else:
        st.warning("A Pokédex carregou corretamente, mas não encontrou nenhuma entrada válida.")

# --- ABA 2: ITENS (Mercado Dinâmico com Flutuação de Preço) ---
# --- ABA 2: ITENS (Mercado Dinâmico com Flutuação de Preço) ---
with abas[1]:
    st.title("🎒 Inventário e Mercado")
    
    banco_itens = {
        "Pokébola": {"preco_base": 200, "descricao": "Dispositivo básico de captura."},
        "Superbola": {"preco_base": 600, "descricao": "Dispositivo com maior taxa de captura."},
        "Ultra-bola": {"preco_base": 1200, "descricao": "Dispositivo de alta performance para capturas difíceis."},
        "Poção": {"preco_base": 300, "descricao": "Restaura 20 de HP de um Pokémon."},
        "Super Poção": {"preco_base": 700, "descricao": "Restaura 50 de HP de um Pokémon."},
        "Reviver": {"preco_base": 1500, "descricao": "Revive um Pokémon desmaiado com metade do HP."},
    }
    
    st.write("Bem-vindo ao catálogo de suprimentos de Aztlas.")
    
    # VISÃO EXCLUSIVA DO MESTRE NO VISOR DE ITENS
    if st.session_state.modo_mestre:
        st.markdown("---")
        st.markdown("### 🛒 Visor do Mestre: Precificação em Tempo Real")
        st.caption("Esta seção calcula custos variáveis automaticamente sem expor tabelas aos players.")
        
        agora = datetime.now()
        hora_atual = agora.hour
        dia_semana = agora.weekday()
        
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
        
        item_pesquisado = st.selectbox("Pesquisar Item no Acervo do Mestre:", ["-- Selecione um Item --"] + list(banco_itens.keys()))
        
        if item_pesquisado != "-- Selecione um Item --":
            dados = banco_itens[item_pesquisado]
            
            # Garante que o preço nunca seja menor que 1
            preco_calculado = max(1, int(dados["preco_base"] * multiplicador))
            
            st.markdown(f"#### 📦 {item_pesquisado}")
            st.write(f"*{dados['descricao']}*")
            
            c1, c2 = st.columns(2)
            c1.metric(label="Preço Comercial Flutuante", value=f"{preco_calculado}₽")
            
            diferenca = preco_calculado - dados['preco_base']
            c2.metric(label="Preço Base (Fixo)", value=f"{dados['preco_base']}₽", delta=f"{diferenca}₽")
    else:
        st.write("Consulte o Mestre da mesa para saber a disponibilidade e os valores atuais das lojas locais.")

# --- ABA 3: TACTICAL MAP ---
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
        
        if lente == "Full Map":
            nome_subpasta = "Full"
            arquivo_selecionado = "full_map.png"
        elif lente == "Half Map":
            nome_subpasta = "Half"
            opcao_half = st.radio("Selecione o arquivo da metade correspondente:", ["Arquivo 1", "Arquivo 2"], horizontal=True)
            arquivo_selecionado = "half_map_1.png" if opcao_half == "Arquivo 1" else "half_map_2.png"
        elif lente == "Quarter Map":
            nome_subpasta = "Quarter"
            opcao_quarter = st.selectbox("Selecione o arquivo do quadrante correspondente:", ["Quadrante 1", "Quadrante 2", "Quadrante 3", "Quadrante 4"])
            mapeamento_quarter = {
                "Quadrante 1": "quarter_nw.png",
                "Quadrante 2": "quarter_ne.png",
                "Quadrante 3": "quarter_sw.png",
                "Quadrante 4": "quarter_se.png"
            }
            arquivo_selecionado = mapeamento_quarter[opcao_quarter]
        
        caminho_final = f"mapas/{nome_subpasta}/{arquivo_selecionado}"
        
        if os.path.exists(caminho_final):
            coordenadas = streamlit_image_coordinates(caminho_final, key=f"click_{lente}_{arquivo_selecionado}")
        else:
            st.error(f"❌ Arquivo não encontrado em: `{caminho_final}`")
            st.info("Caso tenha mudado os nomes internos das imagens, use o campo abaixo para carregar manualmente:")
            arquivo_manual = st.text_input("Digite o nome exato do arquivo com a extensão:", value=arquivo_selecionado)
            caminho_final = f"mapas/{nome_subpasta}/{arquivo_manual}"
            
            if os.path.exists(caminho_final):
                coordenadas = streamlit_image_coordinates(caminho_final, key="click_manual")
            else:
                coordenadas = None
            
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
