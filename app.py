import os
import sqlite3
import pandas as pd
import streamlit as st

# Configuração da página estilo PokéDex
st.set_page_config(page_title="PokéDex Aztlas", page_icon="🐾", layout="wide")

# --- CONTROLADORA DE ACESSO (SENHA DO MESTRE) ---
if "modo_mestre" not in st.session_state:
    st.session_state.modo_mestre = False

st.sidebar.title("🔮 Aztlas-Heart")
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 Painel de Acesso")

# Campo de senha mascarado na barra lateral
senha = st.sidebar.text_input("Senha do Mestre:", type="password")

if senha == "aztlas2026":  # Altere sua senha aqui se desejar
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


# --- BUSCA DE DADOS ---
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


# --- INICIALIZAÇÃO DO ESTADO DE SESSÃO ---
if "id_pokemon_selecionado" not in st.session_state:
    st.session_state.id_pokemon_selecionado = None

df_pokemon = carregar_dados_pokemon()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("🔍 Filtros da Pokédex")

filtro_nome = st.sidebar.text_input("Buscar por Nome:", "")

tipos_disponiveis = sorted(
    list(
        set(df_pokemon["Tipo 1"].dropna()) | set(df_pokemon["Tipo 2"].dropna())
    )
)
filtro_tipo = st.sidebar.selectbox(
    "Filtrar por Tipo:", ["Todos"] + tipos_disponiveis
)

coluna_ordenar = st.sidebar.selectbox(
    "Ordenar por:", options=df_pokemon.columns.tolist(), index=2
)
ordem_crescente = st.sidebar.radio("Ordem:", ["Crescente", "Decrescente"])
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


# --- CORPO PRINCIPAL DO SITE ---

# MODO 1: EXIBIR A FICHA DETALHADA COM ABAS
if st.session_state.id_pokemon_selecionado is not None:
    if st.button("⬅ Voltar para a Lista"):
        st.session_state.id_pokemon_selecionado = None
        st.rerun()

    # Recebe os 5 valores retornados pela função
    poke_geral, poke_desc, poke_stats, poke_breed, poke_moves = buscar_detalhes_completos(
        int(st.session_state.id_pokemon_selecionado)
    )

    if poke_geral:
        st.title(
            f"{poke_geral[2]} {poke_geral[1] if poke_geral[1] else ''}"
        )

        # Adicionada a aba de Golpes
        aba1, aba2, aba3, aba4 = st.tabs(
            [
                "📋 Dados Gerais",
                "📊 Base Stats",
                "🥚 Breeding & Training",
                "⚔️ Golpes / Moves",
            ]
        )

        # ABA 1: DADOS GERAIS
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
                    st.markdown(
                        f"- **Oculta (Habilidade E):** {poke_geral[9]}"
                    )

        # ABA 2: BASE STATS
        with aba2:
            st.subheader("Estatísticas Base")
            if poke_stats:
                stats_dados = {
                    "Status": [
                        "HP",
                        "Ataque",
                        "Defesa",
                        "Sp. Atk",
                        "Sp. Def",
                        "Velocidade",
                    ],
                    "Valor": [
                        poke_stats[2],
                        poke_stats[3],
                        poke_stats[4],
                        poke_stats[5],
                        poke_stats[6],
                        poke_stats[7],
                    ],
                }
                df_stats = pd.DataFrame(stats_dados)
                st.dataframe(df_stats, hide_index=True, use_container_width=True)
            else:
                st.info("Dados de Base Stats não encontrados para este Pokémon.")

        # ABA 3: BREEDING & TRAINING
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
                st.info(
                    "Dados de Breeding/Training não encontrados para este Pokémon."
                )

        # ABA 4: GOLPES / MOVES
        with aba4:
            st.subheader("Lista de Golpes Aprendidos")
            if not poke_moves.empty:
                st.dataframe(poke_moves, hide_index=True, use_container_width=True)
            else:
                st.info("Nenhum golpe encontrado ou tabela de golpes não configurada.")

# MODO 2: EXIBIR A TABELA PRINCIPAL (ESTILO POKÉMON DB)
else:
    st.title("PokéDex Completa")
    st.write(
        "Selecione a caixinha ao lado esquerdo de qualquer Pokémon para abrir sua ficha detalhada."
    )

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
