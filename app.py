import os
import sqlite3
import pandas as pd
import streamlit as st

# Configuração da página estilo PokéDex
st.set_page_config(page_title="PokéDex Aztlas", page_icon="🐾", layout="wide")


# --- CONEXÃO COM O BANCO DE DADOS ---
def conectar_banco():
    caminho_atual = os.path.dirname(__file__)
    caminho_banco = os.path.join(caminho_atual, "pokedex aztlas - Copia.db")
    return sqlite3.connect(caminho_banco)


# --- BUSCA DE DADOS ---
def carregar_dados_pokemon():
    conn = conectar_banco()
    # Carrega a tabela inteira do banco de dados diretamente para o Pandas
    query = "SELECT `ID`, `Dex No.`, `Nome`, `Tipo 1`, `Tipo 2`, `Habilidade 1` FROM pokemon"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def buscar_detalhes_pokemon(pokemon_id):
    conn = conectar_banco()
    cursor = conn.cursor()

    # Busca dados físicos da tabela pokemon
    cursor.execute('SELECT * FROM pokemon WHERE "ID" = ?', (pokemon_id,))
    poke_dados = cursor.fetchone()

    # Busca a descrição RPG correspondente
    cursor.execute(
        'SELECT "Espécie", "Descrição" FROM descricao_pokedexrpg WHERE "ID" = ?',
        (pokemon_id,),
    )
    desc_dados = cursor.fetchone()

    conn.close()
    return poke_dados, desc_dados


# --- CARREGAMENTO INICIAL ---
df_pokemon = carregar_dados_pokemon()

# --- BARRA LATERAL: FILTROS E BUSCA ---
st.sidebar.header("🔍 Filtros da Pokédex")

# 1. Filtro por Nome
filtro_nome = st.sidebar.text_input("Buscar por Nome:", "")

# 2. Filtro por Tipo (Pega todos os tipos únicos existentes no banco)
tipos_disponiveis = sorted(
    list(
        set(df_pokemon["Tipo 1"].dropna()) | set(df_pokemon["Tipo 2"].dropna())
    )
)
filtro_tipo = st.sidebar.selectbox(
    "Filtrar por Tipo:", ["Todos"] + tipos_disponiveis
)

# 3. Organizador (Ordenação de Colunas)
coluna_ordenar = st.sidebar.selectbox(
    "Ordenar por:", options=df_pokemon.columns.tolist(), index=2
)  # Padrão: Nome
ordem_crescente = st.sidebar.radio("Ordem:", ["Crescente", "Decrescente"])
ascendente = True if ordem_crescente == "Crescente" else False

# --- APLICAÇÃO DOS FILTROS NO PANDAS ---
df_filtrado = df_pokemon.copy()

# Aplicando busca por nome
if filtro_nome:
    df_filtrado = df_filtrado[
        df_filtrado["Nome"].str.contains(filtro_nome, case=False, na=False)
    ]

# Aplicando filtro por tipo
if filtro_tipo != "Todos":
    df_filtrado = df_filtrado[
        (df_filtrado["Tipo 1"] == filtro_tipo)
        | (df_filtrado["Tipo 2"] == filtro_tipo)
    ]

# Aplicando a ordenação em qualquer coluna escolhida
df_filtrado = df_filtrado.sort_values(by=coluna_ordenar, ascending=ascendente)

# --- SELEÇÃO PARA VER DETALHES ---
st.sidebar.markdown("---")
st.sidebar.subheader("📄 Ficha do Pokémon")

# Cria uma lista de opções para a caixa de seleção interna
opcoes_pokemon = {"Ver a Lista Completa": None}
for _, row in df_filtrado.iterrows():
    opcoes_pokemon[f"#{row['ID']} - {row['Nome']}"] = row["ID"]

pokemon_escolhido = st.sidebar.selectbox(
    "Selecione para abrir os detalhes:", options=list(opcoes_pokemon.keys())
)
id_selecionado = opcoes_pokemon[pokemon_escolhido]

# --- CORPO PRINCIPAL DO SITE ---

# PÁGINA DE DETALHES (Se um Pokémon foi selecionado no menu lateral)
if id_selecionado is not None:
    poke, desc = buscar_detalhes_pokemon(int(id_selecionado))

    if poke:
        st.title(f"{poke[2]} {poke[1] if poke[1] else ''}")

        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(
                "https://via.placeholder.com/250",
                caption=poke[2],
                use_container_width=True,
            )

        with col2:
            st.subheader("Informações da Pokédex")
            if desc:
                st.markdown(f"**Espécie:** {desc[0]}")
                st.markdown(f"*\"{desc[1]}\"*")

            st.write("---")
            st.markdown(
                f"**Tipo 1:** {poke[3]} | **Tipo 2:** {poke[4] if poke[4] else 'Nenhum'}"
            )
            st.markdown(f"**Altura:** {poke[5]} m | **Peso:** {poke[6]} kg")

            st.subheader("Habilidades")
            st.markdown(f"- **Principal:** {poke[7]}")
            if poke[8]:
                st.markdown(f"- **Secundária:** {poke[8]}")
            if poke[9]:
                st.markdown(f"- **Oculta (Habilidade E):** {poke[9]}")

# PÁGINA PRINCIPAL: LISTA ESTILO POKÉMON DB
else:
    st.title("PokéDex Completa")
    st.write(
        f"Exibindo **{len(df_filtrado)}** Pokémon com os filtros atuais. Use a barra lateral para ver detalhes de um Pokémon específico."
    )

    # Exibe a tabela interativa lindamente na tela.
    # O usuário também pode clicar no topo de qualquer coluna da tabela se quiser reordenar por lá!
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
