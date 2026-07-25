import sqlite3
import pandas as pd
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Pokédex - Painel Tático", page_icon="🎮", layout="wide"
)

st.title("🎮 Painel da Pokédex & Mapa")


# --- CONEXÃO COM O BANCO DE DADOS ---
def get_connection():
  # Altere 'pokedex.db' para o nome exato do seu arquivo de banco de dados
  return sqlite3.connect("pokedex.db")


conn = get_connection()

# --- CARREGAMENTO DAS LISTAS PARA OS FILTROS ---
try:
  df_pokemons = pd.read_sql_query(
      "SELECT id, name FROM pokemon ORDER BY name", conn
  )
  lista_pokemons = df_pokemons["name"].tolist()
except Exception:
  lista_pokemons = []

try:
  df_locais = pd.read_sql_query(
      "SELECT id, Location FROM Locations ORDER BY Location", conn
  )
  lista_locais = df_locais["Location"].tolist()
except Exception:
  lista_locais = []

# --- CRIAÇÃO DAS ABAS DA APLICAÇÃO ---
aba_pokedex, aba_locais, aba_evolucoes = st.tabs(
    ["📱 Consultar Pokémon", "🗺️ Consultar Localizações", "🧬 Tabela de Evoluções"]
)

# ==========================================
# ABA 1: CONSULTAR POKÉMON E SEUS LOCAIS
# ==========================================
with aba_pokedex:
  st.header("Busca por Pokémon")

  if lista_pokemons:
    pokemon_selecionado = st.selectbox(
        "Selecione um Pokémon:", lista_pokemons, key="sb_poke"
    )

    if pokemon_selecionado:
      # Pega o ID do Pokémon selecionado
      poke_id = df_pokemons[df_pokemons["name"] == pokemon_selecionado][
          "id"
      ].values[0]

      st.subheader(f"📍 Onde encontrar: {pokemon_selecionado}")

      # Consulta fazendo JOIN entre Locations e Locations_Pokémon
      query_loc = f"""
                SELECT 
                    l.Location AS 'Local',
                    lp.spawn_method AS 'Método de Aparição',
                    lp.chance_rate AS 'Chance (%)',
                    lp.min_level AS 'Nível Mínimo',
                    lp.max_level AS 'Nível Máximo',
                    lp.time_of_day AS 'Horário'
                FROM Locations_Pokémon lp
                JOIN Locations l ON lp.location_id = l.id
                WHERE lp.pokemon_id = {poke_id}
            """

      df_resultado_loc = pd.read_sql_query(query_loc, conn)

      if not df_resultado_loc.empty:
        st.dataframe(df_resultado_loc, use_container_width=True)
      else:
        st.info("Este Pokémon não possui locais de encontro cadastrados.")
  else:
    st.error("Não foi possível carregar a lista de Pokémon do banco de dados.")

# ==========================================
# ABA 2: CONSULTAR POR LOCALIZAÇÃO
# ==========================================
with aba_locais:
  st.header("Busca por Localização")

  if lista_locais:
    local_selecionado = st.selectbox(
        "Selecione um Local/Rota:", lista_locais, key="sb_local"
    )

    if local_selecionado:
      local_id = df_locais[df_locais["Location"] == local_selecionado][
          "id"
      ].values[0]

      st.subheader(f"🌿 Encontros em: {local_selecionado}")

      # Consulta buscando os Pokémon que aparecem na rota selecionada
      query_encontros = f"""
                SELECT 
                    p.name AS 'Pokémon',
                    lp.spawn_method AS 'Método',
                    lp.chance_rate AS 'Chance (%)',
                    lp.min_level AS 'Nível Mín',
                    lp.max_level AS 'Nível Máx',
                    lp.time_of_day AS 'Turno'
                FROM Locations_Pokémon lp
                JOIN pokemon p ON lp.pokemon_id = p.id
                WHERE lp.location_id = {local_id}
            """

      df_resultado_encontros = pd.read_sql_query(query_encontros, conn)

      if not df_resultado_encontros.empty:
        st.dataframe(df_resultado_encontros, use_container_width=True)
      else:
        st.info("Nenhum Pokémon cadastrado para este local.")
  else:
    st.error("Não foi possível carregar a lista de locais.")

# ==========================================
# ABA 3: TABELA DE EVOLUÇÕES
# ==========================================
with aba_evolucoes:
  st.header("Árvores de Evolução")

  query_evo = """
        SELECT 
            `1evo` AS 'Estágio 1',
            `forma de 2evoluir` AS 'Requisito 2ª Evo',
            `2evo` AS 'Estágio 2',
            `forma de 3evoluir` AS 'Requisito 3ª Evo',
            `3evo` AS 'Estágio 3'
        FROM Evolution_chart
    """

  try:
    df_evolucoes = pd.read_sql_query(query_evo, conn)

    # Filtro opcional por nome dentro da tabela de evoluções
    busca_evo = st.text_input("Filtrar evolução por nome do Pokémon:")

    if busca_evo:
      df_evolucoes = df_evolucoes[
          df_evolucoes["Estágio 1"].str.contains(busca_evo, case=False, na=False)
          | df_evolucoes["Estágio 2"].str.contains(
              busca_evo, case=False, na=False
          )
          | df_evolucoes["Estágio 3"].str.contains(
              busca_evo, case=False, na=False
          )
      ]

    st.dataframe(df_evolucoes, use_container_width=True)

  except Exception as e:
    st.error(f"Erro ao carregar a tabela de evoluções: {e}")

# Fecha a conexão com o banco no final
conn.close()
