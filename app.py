import sqlite3
import streamlit as st

# Configuração da página estilo PokéDex
st.set_page_config(page_title="PokéDex Aztlas", page_icon="🐾", layout="wide")


def conectar_banco():
    # Substitua pelo nome exato do seu arquivo .db se for diferente
    return sqlite3.connect("pokedex aztlas - Copia.db")


# --- FUNÇÕES DE BUSCA ---
def buscar_todos_pokemon():
    conn = conectar_banco()
    cursor = conn.cursor()
    # Mudamos as aspas duplas para crases para evitar conflitos de sintaxe no servidor
    cursor.execute(
        "SELECT `ID`, `Dex No.`, `Nome`, `Tipo 1`, `Tipo 2`, `Habilidade 1` FROM pokemon"
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


def buscar_detalhes_pokemon(pokemon_id):
    conn = conectar_banco()
    cursor = conn.cursor()

    # Busca dados físicos e de habilidades
    cursor.execute(
        'SELECT * FROM pokemon WHERE "ID" = ?', (pokemon_id,)
    )
    poke_dados = cursor.fetchone()

    # Busca a descrição RPG correspondente
    cursor.execute(
        'SELECT "Espécie", "Descrição" FROM descricao_pokedexrpg WHERE "ID" = ?',
        (pokemon_id,),
    )
    desc_dados = cursor.fetchone()

    conn.close()
    return poke_dados, desc_dados


# --- SISTEMA DE NAVEGAÇÃO ---
# Inicializa o estado da sessão para controlar qual página exibir
if "pokemon_selecionado" not in st.session_state:
    st.session_state.pokemon_selecionado = None

# Botão para voltar à lista principal
if st.session_state.pokemon_selecionado is not None:
    if st.button("⬅ Voltar para a Lista"):
        st.session_state.pokemon_selecionado = None
        st.rerun()

# --- PÁGINA 1: DETALHES DO POKÉMON ---
if st.session_state.pokemon_selecionado:
    poke_id = st.session_state.pokemon_selecionado
    poke, desc = buscar_detalhes_pokemon(poke_id)

    if poke:
        st.title(f"{poke[2]} {poke[1] if poke[1] else ''}")

        col1, col2 = st.columns([1, 2])

        with col1:
            # Placeholder para imagem (caso queira adicionar no futuro)
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

# --- PÁGINA 2: LISTA ESTILO POKÉMON DB (SEM BASE STATS) ---
else:
    st.title("PokéDex Completa")
    st.write(
        "Clique no botão **Ver Detalhes** de qualquer Pokémon para abrir sua ficha."
    )

    lista_pokemon = buscar_todos_pokemon()

    # Cabeçalho da Tabela customizada
    header_cols = st.columns([1, 1, 2, 1, 1, 2, 1])
    header_cols[0].markdown("**ID**")
    header_cols[1].markdown("**Dex No.**")
    header_cols[2].markdown("**Nome**")
    header_cols[3].markdown("**Tipo 1**")
    header_cols[4].markdown("**Tipo 2**")
    header_cols[5].markdown("**Habilidade Principal**")
    header_cols[6].markdown("**Ação**")

    st.write("---")

    # Linhas da tabela
    for poke in lista_pokemon:
        p_id, dex_no, nome, tipo1, tipo2, hab1 = poke
        cols = st.columns([1, 1, 2, 1, 1, 2, 1])

        cols[0].write(str(p_id))
        cols[1].write(str(dex_no) if dex_no else "-")
        cols[2].write(f"**{nome}**")
        cols[3].write(tipo1)
        cols[4].write(tipo2 if tipo2 else "-")
        cols[5].write(hab1)

        # Botão interativo para abrir a página do Pokémon específico
        if cols[6].button("Ver Detalhes", key=f"btn_{p_id}"):
            st.session_state.pokemon_selecionado = p_id
            st.rerun()
