import os
import sqlite3
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA E VISUAL
# -----------------------------------------------------------------------------
st.set_page_config(page_title="PokéDex Aztlas", page_icon="🐾", layout="wide")

# Injetamos o CSS para dar o toque de interface de jogo de Pokémon
st.markdown(
    """
    <style>
    @keyframes fundoAnimado {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stApp {
        background: linear-gradient(-45deg, #a0e0ff, #cceeff, #80d4ff, #e6f7ff);
        background-size: 400% 400%;
        animation: fundoAnimado 15s ease infinite;
    }

    .main .block-container {
        border: 2px solid rgba(255, 255, 255, 0.8);
        border-radius: 12px;
        padding: 2rem;
        background-color: rgba(255, 255, 255, 0.9);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 2. CONEXÃO COM O BANCO DE DADOS
# -----------------------------------------------------------------------------
def obter_caminho_banco():
  caminho_atual = os.path.dirname(__file__)
  return os.path.join(caminho_atual, "Aztlas_Dex.db")


def carregar_dados_pokemon():
  caminho_banco = obter_caminho_banco()

  if not os.path.exists(caminho_banco):
    st.warning(
        "Ficheiro do banco de dados não encontrado na pasta do projeto!"
    )
    return pd.DataFrame()

  with sqlite3.connect(caminho_banco) as conn:
    query = "SELECT * FROM Pokemon"
    df = pd.read_sql_query(query, conn)
    return df


# -----------------------------------------------------------------------------
# 3. ESTRUTURA PRINCIPAL DO SITE
# -----------------------------------------------------------------------------
st.title("🐾 PokéDex Regional - Aztlas")
st.markdown("Bem-vindo ao painel central do RPG!")

# Criamos as abas iniciais
abas = st.tabs(["📋 Pokédex", "✨ Habilidades", "🎒 Itens"])

with abas[0]:
  st.subheader("Lista de Pokémon Registados")

  # Carregamos os dados usando a função que criamos
  df_pokemon = carregar_dados_pokemon()

  if not df_pokemon.empty:
    # Mostramos os dados numa tabela interativa do Streamlit
    st.dataframe(df_pokemon, use_container_width=True)
  else:
    st.info("A carregar dados ou tabela vazia.")
