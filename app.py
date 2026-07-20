import os
import sqlite3
import pandas as pd
import streamlit as st

# Configuração da página estilo PokéDex
st.set_page_config(page_title="PokéDex & Itens Aztlas", page_icon="🐾", layout="wide")

# --- CONTROLADORA DE ACESSO (SENHA DO MESTRE) ---
if "modo_mestre" not in st.session_state:
    st.session_state.modo_mestre = False

st.sidebar.title("🔮 Aztlas-Heart")
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 Painel de Acesso")

# Campo de senha mascarado na barra lateral
senha = st.sidebar.text_input("Senha do Mestre:", type="password")

if senha == "Dusk_0256":  # Altere sua senha aqui se desejar
    st.session_state.modo_mestre = True
    st.sidebar.success("⚔️ Modo Mestre Ativo!")
else:
    st.session_state.modo_mestre = False
    if senha != "":
        st.sidebar.error("Senha incorreta.")

st.sidebar.markdown("---")


# --- CONEXÃO COM O BANCO DE DADOS ---
def conectar_banco():
    caminho_atual = os.path.dirname(__file__)
    caminho_banco = os.path.join(caminho_atual, "pokedex aztlas - Copia.db")
    return sqlite3.connect(caminho_banco)


# --- BUSCA DE DADOS (POKÉMON) ---
def carregar_dados_pokemon():
    conn = conectar_banco()
    query = "SELECT `ID`, `Dex No.`, `Nome`, `Tipo 1`, `Tipo 2`, `Habilidade 1` FROM pokemon"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def buscar_detalhes_completos(pokemon_id):
    conn = conectar_banco()
    cursor = conn.cursor()

    # 1. Dados Gerais
    cursor.execute('SELECT * FROM pokemon WHERE "ID" = ?', (pokemon_id,))
    gerais = cursor.fetchone()

    # 2. Descrição RPG
    cursor.execute(
        'SELECT "Espécie", "Descrição" FROM descricao_pokedexrpg WHERE "ID" = ?',
        (pokemon_id,),
    )
    descricao = cursor.fetchone()

    # 3. Base Stats
    cursor.execute('SELECT * FROM "Base Stats" WHERE "ID" = ?', (pokemon_id,))
    stats = cursor.fetchone()

    # 4. Breeding & Training
    cursor.execute(
        'SELECT * FROM "Training_Breeding" WHERE "ID" = ?', (pokemon_id,)
    )
    breeding = cursor.fetchone()

    # 5. Golpes / Moves
    try:
        query_moves = 'SELECT "Nível", "Ataque", "Tipo", "Classe", "Poder", "Acurácia" FROM "pokemon_moves" WHERE "pokemon_id" = ? ORDER BY "Nível" ASC'
        moves_df = pd.read_sql_query(query_moves, conn, params=(pokemon_id,))
    except Exception:
        moves_df = pd.DataFrame()

    conn.close()
    return gerais, descricao, stats, breeding, moves_df


# --- BUSCA DE DADOS (ITENS) ---
def carregar_dados_itens():
    conn = conectar_banco()
    try:
        query = 'SELECT `ID`, `Tipo`, `Nome`, `Efeito`, `Descrição`, `Preço` FROM "Itens"'
        df_itens = pd.read_sql_query(query, conn)
    except Exception:
        df_itens = pd.DataFrame(columns=["ID", "Tipo", "Nome", "Efeito", "Descrição", "Preço"])
    conn.close()
    return df_itens


# --- INICIALIZAÇÃO DO ESTADO DE SESSÃO ---
if "id_pokemon_selecionado" not in st.session_state:
    st.session_state.id_pokemon_selecionado = None

# Organização por Abas Globais na aplicação
aba_pokedex, aba_itens = st.tabs(["🐾 Pokédex Regional", "🎒 Compêndio de Itens"])


# ==============================================================================
# ABA 1: POKÉDEX REGIONAL
# ==============================================================================
with aba_pokedex:
    df_pokemon = carregar_dados_pokemon()

    # --- BARRA LATERAL (FILTROS POKÉMON) ---
    st.sidebar.header("🔍 Filtros da Pokédex")

    filtro_nome = st.sidebar.text_input("Buscar Pokémon por Nome:", "")

    tipos_disponiveis = sorted(
        list(
            set(df_pokemon["Tipo 1"].dropna()) | set(df_pokemon["Tipo 2"].dropna())
        )
    )
    filtro_tipo = st.sidebar.selectbox(
        "Filtrar por Tipo:", ["Todos"] + tipos_disponiveis
    )

    coluna_ordenar = st.sidebar.selectbox(
        "Ordenar Pokémon por:", options=df_pokemon.columns.tolist(), index=2
    )
    ordem_crescente = st.sidebar.radio("Ordem Pokémon:", ["Crescente", "Decrescente"])
    ascendente = True if ordem_crescente == "Crescente" else False

    # --- APLICAÇÃO DOS FILTROS ---
    df_filtrado = df_pokemon.copy()

    if filtro_nome:
        df_filtrado = df_filtrado[
            df_filtrado["Nome"].str.contains(filtro_nome, case=False, na=False)
        ]

    if filtro_tipo != "Todos":
        df_filtrado = df_filtrado[
            (df_filtrado["Tipo 1"] == filtro_tipo)
            | (df_filtrado["Tipo 2"] == filtro_tipo)
        ]

    df_filtrado = df_filtrado.sort_values(by=coluna_ordenar, ascending=ascendente)

    # --- CORPO POKÉDEX ---
    if st.session_state.id_pokemon_selecionado is not None:
        if st.button("⬅ Voltar para a Lista"):
            st.session_state.id_pokemon_selecionado = None
            st.rerun()

        poke_geral, poke_desc, poke_stats, poke_breed, poke_moves = buscar_detalhes_completos(
            int(st.session_state.id_pokemon_selecionado)
        )

        if poke_geral:
            st.title(f"{poke_geral[2]} {poke_geral[1] if poke_geral[1] else ''}")

            aba1, aba2, aba3, aba4 = st.tabs(
                [
                    "📋 Dados Gerais",
                    "📊 Base Stats",
                    "🥚 Breeding & Training",
                    "⚔️ Golpes / Moves",
                ]
            )

            with aba1:
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(
                        "https://via.placeholder.com/250",
                        caption=poke_geral[2],
                        use_container_width=True,
                    )
                with col2:
                    st.subheader("Informações Biológicas")
                    if poke_desc:
                        st.markdown(f"**Espécie:** {poke_desc[0]}")
                        st.markdown(f"*\"{poke_desc[1]}\"*")

                    st.write("---")
                    st.markdown(
                        f"**Tipo 1:** {poke_geral[3]} | **Tipo 2:** {poke_geral[4] if poke_geral[4] else 'Nenhum'}"
                    )
                    st.markdown(
                        f"**Altura:** {poke_geral[5]} m | **Peso:** {poke_geral[6]} kg"
                    )

                    st.subheader("Habilidades")
                    st.markdown(f"- **Principal:** {poke_geral[7]}")
                    if poke_geral[8]:
                        st.markdown(f"- **Secundária:** {poke_geral[8]}")
                    if poke_geral[9]:
                        st.markdown(f"- **Oculta (Habilidade E):** {poke_geral[9]}")

            with aba2:
                st.subheader("Estatísticas Base")
                if poke_stats:
                    stats_dados = {
                        "Status": ["HP", "Ataque", "Defesa", "Sp. Atk", "Sp. Def", "Velocidade"],
                        "Valor": [poke_stats[2], poke_stats[3], poke_stats[4], poke_stats[5], poke_stats[6], poke_stats[7]],
                    }
                    df_stats = pd.DataFrame(stats_dados)
                    st.dataframe(df_stats, hide_index=True, use_container_width=True)
                else:
                    st.info("Dados de Base Stats não encontrados para este Pokémon.")

            with aba3:
                st.subheader("Dados de Cruzamento e Treinamento")
                if poke_breed:
                    st.markdown(f"**Rendimento de EV:** {poke_breed[2]}")
                    st.markdown(f"**Amizade Base:** {poke_breed[3]}")
                    st.markdown(
                        f"**Grupo de Ovos 1:** {poke_breed[4]} | **Grupo de Ovos 2:** {poke_breed[5] if poke_breed[5] else 'Nenhum'}"
                    )
                    st.markdown(f"**Taxa de Gênero:** {poke_breed[6]}")
                else:
                    st.info("Dados de Breeding/Training não encontrados para este Pokémon.")

            with aba4:
                st.subheader("Lista de Golpes Aprendidos")
                if not poke_moves.empty:
                    st.dataframe(poke_moves, hide_index=True, use_container_width=True)
                else:
                    st.info("Nenhum golpe encontrado ou tabela de golpes não configurada.")

    else:
        st.title("PokéDex Completa")
        st.write("Selecione a caixinha ao lado esquerdo de qualquer Pokémon para abrir sua ficha detalhada.")

        df_tabela = df_filtrado.fillna("-")

        evento_selecao = st.dataframe(
            df_tabela,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )

        if (
            evento_selecao
            and "selection" in evento_selecao
            and "rows" in evento_selecao["selection"]
        ):
            linhas_selecionadas = evento_selecao["selection"]["rows"]
            if len(linhas_selecionadas) > 0:
                indice_linha = linhas_selecionadas[0]
                id_pokemon = df_filtrado.iloc[indice_linha]["ID"]
                st.session_state.id_pokemon_selecionado = id_pokemon
                st.rerun()


# ==============================================================================
# ABA 2: COMPÊNDIO DE ITENS (POKÉ5E STYLE)
# ==============================================================================
with aba_itens:
    st.title("🎒 Compêndio de Itens & Equipamentos")
    st.markdown("Consulte os consumíveis, esferas de captura, bagas e itens segurados da região de Aztlas.")

    df_itens = carregar_dados_itens()

    if df_itens.empty:
        st.warning("Nenhum item encontrado na tabela 'Itens' da base de dados.")
    else:
        # Filtros específicos para Itens na barra lateral
        st.sidebar.markdown("---")
        st.sidebar.header("🎒 Filtros do Inventário")
        
        filtro_item_nome = st.sidebar.text_input("Buscar Item por Nome:", "")
        
        tipos_itens = ["Todos"] + sorted(list(df_itens["Tipo"].dropna().unique()))
        filtro_item_tipo = st.sidebar.selectbox("Filtrar por Categoria/Tipo:", tipos_itens)

        # Aplicação dos filtros de itens
        df_itens_filtrados = df_itens.copy()

        if filtro_item_nome:
            df_itens_filtrados = df_itens_filtrados[
                df_itens_filtrados["Nome"].str.contains(filtro_item_nome, case=False, na=False)
            ]

        if filtro_item_tipo != "Todos":
            df_itens_filtrados = df_itens_filtrados[
                df_itens_filtrados["Tipo"] == filtro_item_tipo
            ]

        # Exibição estilo Cards / Poké5e
        st.markdown(f"**Total de Itens Encontrados:** `{len(df_itens_filtrados)}`")
        
        # Modo de visualização: Tabela Completa ou Fichas Expandíveis
        visualizacao = st.radio("Modo de Visualização:", ["📋 Fichas Detalhadas", "📊 Tabela Geral"], horizontal=True)

        if visualizacao == "📋 Fichas Detalhadas":
            for _, item in df_itens_filtrados.iterrows():
                preco_fmt = f"₽ {item['Preço']:,.2f}" if pd.notnull(item['Preço']) else "Inestimável / Especial"
                
                with st.expander(f"📦 **{item['Nome']}** — *{item['Tipo']}* | 💰 {preco_fmt}"):
                    col_e1, col_e2 = st.columns([1, 2])
                    
                    with col_e1:
                        st.markdown(f"**Categoria:** `{item['Tipo']}`")
                        st.markdown(f"**Preço Médio:** {preco_fmt}")
                        if pd.notnull(item['Efeito']) and str(item['Efeito']).strip() != "":
                            st.info(f"⚡ **Efeito:** {item['Efeito']}")
                    
                    with col_e2:
                        st.markdown("**Descrição Rápida / Lore:**")
                        st.write(item['Descrição'] if item['Descrição'] else "Sem descrição cadastrada.")
        else:
            df_exibicao = df_itens_filtrados.fillna("-")
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
