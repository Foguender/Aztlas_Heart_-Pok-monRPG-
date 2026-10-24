import os
import random
import sqlite3
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA & ESTILO (TEMA AZUL CERÚLEO)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="PokéDex Aztlas", page_icon="🐾", layout="wide")

st.markdown(
    """
    <style>
    @keyframes fundoAnimado {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stApp {
        background: linear-gradient(-45deg, #0077b6, #00b4d8, #48cae4, #90e0ef);
        background-size: 400% 400%;
        animation: fundoAnimado 12s ease infinite;
    }

    .main .block-container {
        border: 2px solid #ffffff;
        border-radius: 12px;
        padding: 2rem;
        background-color: rgba(255, 255, 255, 0.95);
    }

    /* Textos do corpo principal da página */
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6, .main p, .main span, .main label {
        color: #03045e !important;
    }

    /* --- ESTILOS DA BARRA LATERAL (SIDEBAR) --- */
    [data-testid="stSidebar"] {
        background-color: rgba(0, 50, 90, 0.85) !important;
    }

    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] a {
        color: #ffffff !important;
    }

    [data-testid="stSidebar"] input {
        color: #03045e !important;
        background-color: #f0f8ff !important;
    }

    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
        color: #03045e !important;
        background-color: #f0f8ff !important;
    }
    
    [data-testid="stSidebar"] [data-baseweb="select"] span {
        color: #03045e !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# FUNÇÕES DE ESTILO (BADGES)
# -----------------------------------------------------------------------------
def criar_badge_tipo(tipo):
  if not tipo or pd.isna(tipo) or str(tipo).strip() in ["-", "", "None"]:
    return ""

  cores_tipos = {
      "Normal": "#AAAA99",
      "Fogo": "#FF4422",
      "Água": "#3399FF",
      "Grama": "#6CC644",
      "Elétrico": "#F7D02C",
      "Eletrico": "#FfCC33",
      "Gelo": "#96D9D6",
      "Lutador": "#C22E28",
      "Venenoso": "#AA5599",
      "Veneno": "#A33EA0",
      "Terra": "#DDBB55",
      "Voador": "#8899ff",
      "Psíquico": "#FF5599",
      "Psiquico": "#F95587",
      "Inseto": "#AABB22",
      "Pedra": "#B6A136",
      "Fantasma": "#735797",
      "Dragão": "#6F35FC",
      "Sombrio": "#775544",
      "Aço": "#6CC644",
      "Fada": "#D685AD",
  }

  cor = cores_tipos.get(str(tipo).capitalize(), "#777777")
  return f"""<span style="
background-color: {cor};
color: white;
padding: 3px 8px;
border-radius: 4px;
font-weight: bold;
font-size: 11px;
text-transform: uppercase;
display: inline-block;
min-width: 65px;
text-align: center;">
{tipo}
</span>"""


# -----------------------------------------------------------------------------
# 1. BANCO DE DADOS & QUERIES
# -----------------------------------------------------------------------------
def obter_caminho_banco():
  caminho_atual = os.path.dirname(__file__)
  return os.path.join(caminho_atual, "Aztlas_Dex.db")


def carregar_dados_pokemon():
  caminho_banco = obter_caminho_banco()
  if not os.path.exists(caminho_banco):
    return pd.DataFrame()

  with sqlite3.connect(caminho_banco) as conn:
    query = """SELECT * FROM Pokemon"""
    df = pd.read_sql_query(query, conn)
    return df


def carregar_tabela_segura(conn, query, params=()):
  try:
    return pd.read_sql_query(query, conn, params=params)
  except Exception:
    return pd.DataFrame()


def buscar_detalhes_completos(pokemon_id):
  caminho_banco = obter_caminho_banco()
  with sqlite3.connect(caminho_banco) as conn:
    df_geral = carregar_tabela_segura(
        conn, 'SELECT * FROM Pokemon WHERE "ID" = ?', (pokemon_id,)
    )
    gerais = df_geral.iloc[0].to_dict() if not df_geral.empty else {}

    try:
      cursor = conn.cursor()
      cursor.execute(
          'SELECT "Espécie", "Descrição" FROM descricao_pokedexrpg WHERE "ID"'
          " = ?",
          (pokemon_id,),
      )
      descricao = cursor.fetchone()
    except Exception:
      descricao = ("Sem espécie", "Sem descrição disponível.")

    pokemon_nome = gerais.get("Nome", "")
    learnset_df = carregar_tabela_segura(
        conn,
        'SELECT * FROM "Learnset" WHERE "Pokemon_Nome" = ?',
        (pokemon_nome,),
    )
    if learnset_df.empty:
      learnset_df = carregar_tabela_segura(
          conn,
          'SELECT * FROM "Learnset_pokemon" WHERE "pokemon_id" = ? OR "ID" = ?',
          (pokemon_id, pokemon_id),
      )

    tm_df = carregar_tabela_segura(
        conn,
        'SELECT * FROM "Tm_pokémon" WHERE "pokemon_id" = ? OR "ID" = ?',
        (pokemon_id, pokemon_id),
    )
    egg_df = carregar_tabela_segura(
        conn,
        'SELECT * FROM "Egg_Moves" WHERE "pokemon_id" = ? OR "ID" = ?',
        (pokemon_id, pokemon_id),
    )
    teacher_df = carregar_tabela_segura(
        conn,
        'SELECT * FROM "Teacher_Moves" WHERE "pokemon_id" = ? OR "ID" = ?',
        (pokemon_id, pokemon_id),
    )

    query_evo = """
        SELECT 
        p1.Nome AS [Forma Inicial], 
        e.Nivel_Neccesario AS [Nível], 
        p2.Nome AS [Evolução]
        FROM Evolucoes e
        LEFT JOIN Pokemon p1 ON e.Pokemon_Origem = p1.ID
        LEFT JOIN Pokemon p2 ON e.Pokemon_Destino = p2.ID
        WHERE e.Pokemon_Origem = ? OR e.Pokemon_Destino = ?
        """
    evo_df = carregar_tabela_segura(conn, query_evo, (pokemon_id, pokemon_id))
    if evo_df.empty:
      query_evo_alt = """
            SELECT 
            p1.Nome AS [Forma Inicial], 
            e.forma_de_2evoluir AS [Método / Requisito 1], 
            p2.Nome AS [2ª Evolução]
            FROM Evolution_chart e
            LEFT JOIN Pokemon p1 ON e.pokemon_id_1 = p1.ID
            LEFT JOIN Pokemon p2 ON e.pokemon_id_2 = p2.ID
            WHERE e.pokemon_id_1 = ? OR e.pokemon_id_2 = ?
            """
      evo_df = carregar_tabela_segura(
          conn, query_evo_alt, (pokemon_id, pokemon_id)
      )

    loc_df = pd.DataFrame()
    for nome_tabela in ["Spawn_Pokemon", "Locations_Pok mon", "Locations_Pokémon"]:
      try:
        query_loc = f"""
                SELECT Local_Nome AS [Local], Metodo_Aparecimento AS [Método], 
                Tx_Chance AS [Chance], Nivel_Minimo AS [Nível Mín], 
                Nivel_Maximo AS [Nível Máx], Periodo_Dia AS [Horário]
                FROM "{nome_tabela}"
                WHERE Pokemon_Nome = ? OR pokemon_id = ?
                """
        loc_df = carregar_tabela_segura(
            conn, query_loc, (pokemon_nome, pokemon_id)
        )
        if not loc_df.empty:
          break
      except Exception:
        continue

    golpes_dict = {
        "learnset": learnset_df,
        "tm": tm_df,
        "egg": egg_df,
        "teacher": teacher_df,
    }

    return gerais, descricao, golpes_dict, evo_df, loc_df


def carregar_dados_habilidades():
  caminho_banco = obter_caminho_banco()
  if not os.path.exists(caminho_banco):
    return pd.DataFrame()

  with sqlite3.connect(caminho_banco) as conn:
    for nome_tabela in ["Habilidades", "Abilities", "habilidades"]:
      df = carregar_tabela_segura(conn, f'SELECT * FROM "{nome_tabela}"')
      if not df.empty:
        df.columns = [
            c.replace("DescriÃ§ao", "Descrição")
            .replace("Descricao", "Descrição")
            .replace("DescriÃ§Ã£o", "Descrição")
            for c in df.columns
        ]
        return df
    return pd.DataFrame()


def carregar_dados_itens():
  caminho_banco = obter_caminho_banco()
  if not os.path.exists(caminho_banco):
    return pd.DataFrame()

  with sqlite3.connect(caminho_banco) as conn:
    df_itens = carregar_tabela_segura(conn, 'SELECT * FROM "Itens"')
    if "PreÃ§o" in df_itens.columns:
      df_itens.rename(columns={"PreÃ§o": "Preço"}, inplace=True)
    if "Preço" in df_itens.columns:
      df_itens["Preço"] = pd.to_numeric(df_itens["Preço"], errors="coerce")
    return df_itens


# -----------------------------------------------------------------------------
# 2. ESTADOS DE SESSÃO
# -----------------------------------------------------------------------------
if "modo_mestre" not in st.session_state:
  st.session_state.modo_mestre = False

if "modificadores_preco" not in st.session_state:
  st.session_state.modificadores_preco = {}

if "id_pokemon_selecionado" not in st.session_state:
  st.session_state.id_pokemon_selecionado = None

if "historico_rolagens" not in st.session_state:
  st.session_state.historico_rolagens = []


def gerar_flutuacao_automatica(categorias):
  novos_modificadores = {}
  for cat in categorias:
    variacao = round(random.uniform(0.70, 1.50), 2)
    novos_modificadores[cat] = 1.10 if variacao == 1.0 else variacao
  return novos_modificadores


# -----------------------------------------------------------------------------
# 3. BARRA LATERAL (LOGIN DO MESTRE & ROLAGEM PÚBLICA DE DADOS)
# -----------------------------------------------------------------------------
st.sidebar.title("Pocket & Monsters RPG")
st.sidebar.markdown("---")
st.sidebar.subheader("Painel de Acesso")

senha = st.sidebar.text_input("Senha do Mestre:", type="password")
st.session_state.modo_mestre = senha == "Dusk_0256"

if st.session_state.modo_mestre:
  st.sidebar.success("⚔️ Modo Mestre Ativo!")
elif senha != "":
  st.sidebar.error("Senha incorreta.")

st.sidebar.markdown("---")
st.sidebar.subheader("🎲 Rolagem Pública de Dados")
jogador_nome = st.sidebar.text_input("Seu Nome / Personagem:", "")
faces_dado = st.sidebar.selectbox("Escolher Dado:", [20, 6, 10, 12, 100])

if st.sidebar.button("Rolar Dado Publicamente"):
  if not jogador_nome:
    st.sidebar.warning("Insira o seu nome primeiro!")
  else:
    resultado = random.randint(1, faces_dado)
    st.session_state.historico_rolagens.insert(
        0, {"jogador": jogador_nome, "dado": f"D{faces_dado}", "resultado": resultado}
    )
    st.sidebar.success(
        f"🎲 {jogador_nome} rolou um D{faces_dado} e tirou: **{resultado}**!"
    )

st.sidebar.markdown("---")

# -----------------------------------------------------------------------------
# 4. ESTRUTURA DE ABAS PRINCIPAIS
# -----------------------------------------------------------------------------
abas_disponiveis = [
    "🐾 Pokédex Regional",
    "✨ Compêndio de Habilidades",
    "🎒 Compêndio de Itens",
]

if st.session_state.modo_mestre:
  abas_disponiveis.append("🧙‍♂️ Escudo do Mestre")

abas = st.tabs(abas_disponiveis)


# ==============================================================================
# ABA 1: POKÉDEX REGIONAL
# ==============================================================================
with abas[0]:
  df_pokemon = carregar_dados_pokemon()

  if df_pokemon.empty:
    st.warning(
        "O banco de dados 'Aztlas_Dex.db' não foi encontrado ou está"
        " vazio."
    )
  else:
    st.sidebar.header("🔍 Filtros da Pokédex")
    filtro_nome = st.sidebar.text_input("Buscar Pokémon por Nome:", "")

    col_t1 = (
        df_pokemon["Tipo 1"].dropna().unique()
        if "Tipo 1" in df_pokemon.columns
        else []
    )
    col_t2 = (
        df_pokemon["Tipo 2"].dropna().unique()
        if "Tipo 2" in df_pokemon.columns
        else []
    )
    tipos_disponiveis = sorted(list(set(col_t1) | set(col_t2)))
    
    # Linha corrigida com todos os parênteses fechados corretamente:
    filtro_tipo = st.sidebar.selectbox(
        "Filtrar por Tipo:", ["Todos"] + tipos_disponiveis
    )

    df_filtrado = df_pokemon.copy()

    if filtro_nome and "Nome" in df_filtrado.columns:
      df_filtrado = df_filtrado[
          df_filtrado["Nome"].str.contains(filtro_nome, case=False, na=False)
      ]

    if filtro_tipo != "Todos":
      cond1 = (
          df_filtrado["Tipo 1"] == filtro_tipo
          if "Tipo 1" in df_filtrado.columns
          else False
      )
      cond2 = (
          df_filtrado["Tipo 2"] == filtro_tipo
          if "Tipo 2" in df_filtrado.columns
          else False
      )
      df_filtrado = df_filtrado[cond1 | cond2]
