import sqlite3
import pandas as pd
import streamlit as st

# Configuração da página
st.set_page_config(page_title="Pokédex Poke5e", layout="wide")


# --- FUNÇÕES DE AJUDA ---
def conectar_banco():
    return sqlite3.connect("pokedex.db")


def calcular_modificador(valor):
    """Calcula o modificador de D&D 5e padrão (ex: 15 -> +2, 6 -> -2)"""
    if valor is None:
        return "0"
    mod = (valor - 10) // 2
    return f"+{mod}" if mod >= 0 else f"{mod}"


# --- INICIALIZAÇÃO DO ESTADO ---
if "id_pokemon_selecionado" not in st.session_state:
    st.session_state.id_pokemon_selecionado = 1  # Começa no ID 1 por padrão

# --- SIDERBAR / NAVEGAÇÃO ---
st.sidebar.title("🔍 Navegação Pokédex")

conn = conectar_banco()

# Busca a lista de Pokémon para a navegação lateral
df_sidebar = pd.read_sql_query("SELECT id, name FROM pokemon", conn)
lista_pokemon = [f"{row['id']} - {row['name']}" for _, row in df_sidebar.iterrows()]

pokemon_escolhido = st.sidebar.selectbox("Selecione um Pokémon:", lista_pokemon)
id_atual = int(pokemon_escolhido.split(" - ")[0])
st.session_state.id_pokemon_selecionado = id_atual

# --- BUSCA DE DADOS DO POKÉMON SELECIONADO ---
cursor = conn.cursor()

# 1. Dados Gerais
cursor.execute("SELECT * FROM pokemon WHERE id = ?", (id_atual,))
poke_geral = cursor.fetchone()

# 2. Base Stats Originais
cursor.execute("SELECT * FROM base_stats WHERE pokemon_id = ?", (id_atual,))
poke_stats = cursor.fetchone()

# 3. Atributos do RPG (Tabela Nova)
# Se você ainda não criou a tabela, esse bloco retornará None temporariamente
try:
    cursor.execute(
        "SELECT str, dex, con, intel, wis, cha, ac, hp_rpg FROM rpg_attributes WHERE pokemon_id = ?",
        (id_atual,),
    )
    rpg_stats = cursor.fetchone()
except sqlite3.OperationalError:
    rpg_stats = None

conn.close()

# --- INTERFACE PRINCIPAL ---
if poke_geral:
    st.title(f"🦖 {poke_geral[2]} (Nº {poke_geral[0]})")

    # Criando as 4 abras solicitadas
    aba1, aba2, aba3, aba4 = st.tabs(
        [
            "📋 Dados Gerais",
            "🎲 Status & Atributos RPG",
            "🥚 Criação & Treino",
            "⚔️ Movimentos",
        ]
    )

    # --- ABA 1: DADOS GERAIS ---
    with aba1:
        st.subheader("Informações Biológicas")
        # Exiba aqui seus dados de tipo, descrição, etc.
        st.write(f"Espécie: {poke_geral[2]}")

    # --- ABA 2: BASE STATS & ATRIBUTOS D&D (DIRETO DO BANCO) ---
    with aba2:
        col_stats_brutos, col_stats_rpg = st.columns([1, 2])

        with col_stats_brutos:
            st.subheader("📊 Atributos Originais (Jogo)")
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
                st.dataframe(
                    pd.DataFrame(stats_dados),
                    hide_index=True,
                    use_container_width=True,
                )

        with col_stats_rpg:
            st.subheader("🛡️ Ficha Técnica Poke5e (D&D)")

            if rpg_stats:
                # Se encontrou os dados salvos na tabela do banco de dados
                str_score, dex_score, con_score = (
                    rpg_stats[0],
                    rpg_stats[1],
                    rpg_stats[2],
                )
                int_score, wis_score, cha_score = (
                    rpg_stats[3],
                    rpg_stats[4],
                    rpg_stats[5],
                )
                ac_total = rpg_stats[6]
                hp_rpg = rpg_stats[7]
            else:
                # Valores provisórios caso a tabela no banco ainda esteja vazia
                st.warning(
                    "⚠️ Atributos de RPG não encontrados no banco de dados para este Pokémon."
                )
                str_score, dex_score, con_score = 10, 10, 10
                int_score, wis_score, cha_score = 10, 10, 10
                ac_total = 10
                hp_rpg = 10

            # Exibição dos cards de combate superiores
            c_hp, c_ac = st.columns(2)
            with c_hp:
                st.metric(label="❤️ Pontos de Vida (HP)", value=hp_rpg)
            with c_ac:
                st.metric(label="🛡️ Classe de Armadura (AC)", value=ac_total)

            st.write("")

            # Grid com as 6 habilidades de D&D 5e
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            with c1:
                st.metric(
                    label="STR",
                    value=str_score,
                    delta=calcular_modificador(str_score),
                    delta_color="off",
                )
            with c2:
                st.metric(
                    label="DEX",
                    value=dex_score,
                    delta=calcular_modificador(dex_score),
                    delta_color="off",
                )
            with c3:
                st.metric(
                    label="CON",
                    value=con_score,
                    delta=calcular_modificador(con_score),
                    delta_color="off",
                )
            with c4:
                st.metric(
                    label="INT",
                    value=int_score,
                    delta=calcular_modificador(int_score),
                    delta_color="off",
                )
            with c5:
                st.metric(
                    label="WIS",
                    value=wis_score,
                    delta=calcular_modificador(wis_score),
                    delta_color="off",
                )
            with c6:
                st.metric(
                    label="CHA",
                    value=cha_score,
                    delta=calcular_modificador(cha_score),
                    delta_color="off",
                )

    # --- ABA 3: CRIAÇÃO & TREINO ---
    with aba3:
        st.subheader("Dados de Cruzamento e Treinamento")

    # --- ABA 4: MOVIMENTOS ---
    with aba4:
        st.subheader("Lista de Ataques Disponíveis")

else:
    st.error("Pokémon não encontrado.")
