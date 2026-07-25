import sqlite3
import pandas as pd
import streamlit as st

# Conecta ao banco de dados SQLite
conn = sqlite3.connect("pokedex.db")


# Função para buscar e exibir a evolução de um Pokémon
def exibir_evolucao(nome_pokemon):
  query = f"SELECT * FROM Evolution_chart WHERE Pokemon = '{nome_pokemon}'"
  df_evolucao = pd.read_sql_query(query, conn)

  if not df_evolucao.empty:
    st.subheader("🧬 Tabela de Evolução")
    st.dataframe(df_evolucao)
  else:
    st.info("Nenhuma evolução encontrada para este Pokémon.")


# Função para buscar e exibir as localizações
def exibir_localizacao(nome_pokemon):
  query = f"SELECT * FROM Locations WHERE Pokemon = '{nome_pokemon}'"
  df_loc = pd.read_sql_query(query, conn)

  if not df_loc.empty:
    st.subheader("📍 Localização e Encontros")
    st.table(df_loc)
  else:
    st.info("Localização não encontrada.")
