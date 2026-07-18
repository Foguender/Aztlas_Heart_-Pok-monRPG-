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


# --- CAPTURAR PARÂMETROS DA URL ---
# Usamos a URL do navegador para saber qual Pokémon exibir (ex: ?id=10)
parametros_url = st.query_params

# --- CARREGAMENTO INICIAL DOS DADOS ---
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

# MODO 1: EXIBIR A FICHA DO POKÉMON SE ACESSADO VIA LINK
if "id" in parametros_url:
    id_selecionado = parametros_url["id"]

    # Botão para voltar à lista principal
    if st.button("⬅ Voltar para a Lista"):
        st.query_params.clear()  # Limpa o id da URL para voltar à lista
        st.rerun()

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

# MODO 2: EXIBIR A LISTA PRINCIPAL COM LINKS NOS NOMES
else:
    st.title("PokéDex Completa")
    st.write(
        f"Exibindo **{len(df_filtrado)}** Pokémon. Clique no nome de qualquer um para abrir os detalhes."
    )

    # Criamos o cabeçalho da tabela em HTML/CSS para lembrar o estilo do Pokémon DB
    html_tabela = """
    <style>
        .pokedex-table {
            width: 100%;
            border-collapse: collapse;
            font-family: sans-serif;
        }
        .pokedex-table th {
            text-align: left;
            padding: 10px;
            background-color: #f2f2f2;
            border-bottom: 2px solid #ddd;
        }
        .pokedex-table td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        .pokedex-link {
            color: #0066cc;
            text-decoration: none;
            font-weight: bold;
        }
        .pokedex-link:hover {
            text-decoration: underline;
        }
    </style>
    <table class="pokedex-table">
        <tr>
            <th>Dex No.</th>
            <th>Nome</th>
            <th>Tipo 1</th>
            <th>Tipo 2</th>
            <th>Habilidade 1</th>
        </tr>
    """

    # Preenchemos as linhas da tabela dinamicamente com os dados filtrados do banco
    for _, row in df_filtrado.iterrows():
        dex_no = row["Dex No."] if row["Dex No."] else "-"
        nome = row["Nome"]
        tipo1 = row["Tipo 1"]
        tipo2 = row["Tipo 2"] if row["Tipo 2"] else "-"
        hab1 = row["Habilidade 1"]
        p_id = row["ID"]

        # O link aponta para a própria URL com o parâmetro ?id=X correspondente
        html_tabela += f"""
        <tr>
            <td>{dex_no}</td>
            <td><a class="pokedex-link" href="/?id={p_id}" target="_self">{nome}</a></td>
            <td>{tipo1}</td>
            <td>{tipo2}</td>
            <td>{hab1}</td>
        </tr>
        """

    html_tabela += "</table>"

    # Renderiza a tabela HTML de forma segura no Streamlit
    st.markdown(html_tabela, unsafe_allow_html=True)
