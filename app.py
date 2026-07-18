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


# --- REGRAS MATEMÁTICAS (CONVERSÃO POKE5E) ---
def calcular_atributo_dnd(base_stat):
    # Fórmula: ROUND(10 + (Base Stat - 70) / 15)
    score = round(10 + (base_stat - 70) / 15)
    # Aplica o limitador de 3 a 20 do Species Rating inicial
    return max(3, min(20, score))


def calcular_modificador(score):
    # Fórmula clássica de D&D 5e: (Atributo - 10) // 2
    mod = (score - 10) // 2
    return f"+{mod}" if mod >= 0 else f"{mod}"


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

    # 1. Dados Gerais (Tabela pokemon)
    cursor.execute('SELECT * FROM pokemon WHERE "ID" = ?', (pokemon_id,))
    gerais = cursor.fetchone()

    # 2. Descrição RPG (Tabela descricao_pokedexrpg)
    cursor.execute(
        'SELECT "Espécie", "Descrição" FROM descricao_pokedexrpg WHERE "ID" = ?',
        (pokemon_id,),
    )
    descricao = cursor.fetchone()

    # 3. Base Stats (Tabela Base Stats)
    cursor.execute('SELECT * FROM "Base Stats" WHERE "ID" = ?', (pokemon_id,))
    stats = cursor.fetchone()

    # 4. Breeding & Training (Tabela Training_Breeding)
    cursor.execute(
        'SELECT * FROM "Training_Breeding" WHERE "ID" = ?', (pokemon_id,)
    )
    breeding = cursor.fetchone()

    # 5. Golpes / Moves (Tabela pokemon_moves)
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

# MODO 1: EXIBIR A FICHA DETALHADA COM ABAS E CÁLCULOS
if st.session_state.id_pokemon_selecionado is not None:
    if st.button("⬅ Voltar para a Lista"):
        st.session_state.id_pokemon_selecionado = None
        st.rerun()

    poke_geral, poke_desc, poke_stats, poke_breed, df_moves = (
        buscar_detalhes_completos(int(st.session_state.id_pokemon_selecionado))
    )

    if poke_geral:
        st.title(f"{poke_geral[2]} {poke_geral[1] if poke_geral[1] else ''}")

        # Criação das 4 abas estruturadas
        aba1, aba2, aba3, aba4 = st.tabs(
            [
                "📋 Dados Gerais",
                "📊 Base Stats & RPG",
                "🥚 Breeding & Training",
                "⚔ Golpes (Moves)",
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

        # ABA 2: BASE STATS & ATRIBUTOS D&D (Poke5e)
        with aba2:
            if poke_stats:
                hp, atk, de, spatk, spdef, spe = (
                    poke_stats[2],
                    poke_stats[3],
                    poke_stats[4],
                    poke_stats[5],
                    poke_stats[6],
                    poke_stats[7],
                )
                bst = sum([hp, atk, de, spatk, spdef, spe])

                st.subheader("Estatísticas Base de Pokémon")

                stats_dados = {
                    "Status": [
                        "HP",
                        "Ataque",
                        "Defesa",
                        "Sp. Atk",
                        "Sp. Def",
                        "Velocidade",
                        "Total (BST)",
                    ],
                    "Valor": [hp, atk, de, spatk, spdef, spe, bst],
                }
                df_stats = pd.DataFrame(stats_dados)
                st.dataframe(df_stats, hide_index=True, use_container_width=True)

                st.write("---")
                st.subheader("🎲 Atributos Convertidos para RPG (Poke5e)")

                # --- SISTEMA DE AJUSTE MANUAL POR NOME (OVERRIDE) ---
                # Cadastramos as fichas oficiais do Poke5e direto pelo nome exato do Pokémon
                fichas_customizadas = {
                    "Pitya": {
                        "STR": 12,
                        "DEX": 15,
                        "CON": 13,
                        "INT": 6,
                        "WIS": 10,
                        "CHA": 10,
                        "HP_RPG": 17,
                        "AC": 12,
                    }
                    # Você pode adicionar outros Pokémon oficiais aqui embaixo seguindo o mesmo padrão!
                }

                # Puxa o nome atual do Pokémon (removendo espaços extras para garantir o encaixe)
                nome_atual = str(poke_geral[2]).strip()

                if nome_atual in fichas_customizadas:
                    # Se o nome estiver na lista, puxa a sua ficha perfeitinha do Poke5e
                    c = fichas_customizadas[nome_atual]
                    str_score, dex_score, con_score = (
                        c["STR"],
                        c["DEX"],
                        c["CON"],
                    )
                    int_score, wis_score, cha_score = (
                        c["INT"],
                        c["WIS"],
                        c["CHA"],
                    )
                    hp_rpg = c["HP_RPG"]
                    ac_total = c["AC"]
                else:
                    # Se não estiver cadastrado na mão, o sistema roda o cálculo aproximado
                    con_score = calcular_atributo_dnd(hp)
                    str_score = calcular_atributo_dnd(atk)
                    dex_score = calcular_atributo_dnd(de)
                    int_score = calcular_atributo_dnd(spatk)
                    wis_score = calcular_atributo_dnd(spdef)
                    cha_score = calcular_atributo_dnd(spe)

                    hp_rpg = 10 + (con_score - 10) // 2
                    mod_dex_num = (dex_score - 10) // 2
                    mod_wis_num = (wis_score - 10) // 2
                    bonus_esp = max(0, mod_wis_num) if mod_wis_num > 0 else 0
                    ac_total = 10 + mod_dex_num + bonus_esp

                # Calcula os modificadores visuais (+2, -1, etc.)
                mod_str = calcular_modificador(str_score)
                mod_dex = calcular_modificador(dex_score)
                mod_con = calcular_modificador(con_score)
                mod_int = calcular_modificador(int_score)
                mod_wis = calcular_modificador(wis_score)
                mod_cha = calcular_modificador(cha_score)

                # --- EXIBIÇÃO DOS STATUS DE COMBATE ---
                col_hp, col_ac = st.columns(2)
                with col_hp:
                    st.metric(
                        label="❤️ Pontos de Vida (HP Máximo)", value=hp_rpg
                    )
                with col_ac:
                    st.metric(
                        label="🛡️ Classe de Armadura (AC Natural)",
                        value=ac_total,
                    )

                st.write("")

                # Grid com os 6 atributos principais estilo ficha D&D
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                with c1:
                    st.metric(
                        label="STR (Força)",
                        value=str_score,
                        delta=mod_str,
                        delta_color="off",
                    )
                with c2:
                    st.metric(
                        label="DEX (Destreza)",
                        value=dex_score,
                        delta=mod_dex,
                        delta_color="off",
                    )
                with c3:
                    st.metric(
                        label="CON (Const.)",
                        value=con_score,
                        delta=mod_con,
                        delta_color="off",
                    )
                with c4:
                    st.metric(
                        label="INT (Intelig.)",
                        value=int_score,
                        delta=mod_int,
                        delta_color="off",
                    )
                with c5:
                    st.metric(
                        label="WIS (Sabed.)",
                        value=wis_score,
                        delta=mod_wis,
                        delta_color="off",
                    )
                with c6:
                    st.metric(
                        label="CHA (Carisma)",
                        value=cha_score,
                        delta=mod_cha,
                        delta_color="off",
                    )
            else:
                st.info(
                    "Dados de Base Stats não encontrados para este Pokémon."
                )

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

        # ABA 4: GOLPES (MOVES)
        with aba4:
            st.subheader("Lista de Golpes Aprendidos")
            if not df_moves.empty:
                st.write(
                    "Estes são os movimentos que este Pokémon pode aprender:"
                )
                st.dataframe(df_moves, hide_index=True, use_container_width=True)
            else:
                st.info(
                    "Nenhum golpe cadastrado ou encontrado para este Pokémon no momento."
                )

# MODO 2: EXIBIR A TABELA PRINCIPAL (MÉTODO DA CAIXA DE SELEÇÃO)
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
            indice_linha = lines_selecionadas[0]
            id_pokemon = df_filtrado.iloc[indice_linha]["ID"]
            st.session_state.id_pokemon_selecionado = id_pokemon
            st.rerun()
