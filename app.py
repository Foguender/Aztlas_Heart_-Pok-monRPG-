import os
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="PokéDex Aztlas", page_icon="🐾", layout="wide")

# -----------------------------------------------------------------------------
# ESTILIZAÇÃO CSS - TEMA AZUL CERÚLEO (ESTILO POKÉDEX CLÁSSICA)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @keyframes fundoAnimado {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stApp {
        /* Gradiente inspirado em tons de azul cerúleo e celeste brilhante */
        background: linear-gradient(-45deg, #0077b6, #00b4d8, #48cae4, #90e0ef);
        background-size: 400% 400%;
        animation: fundoAnimado 12s ease infinite;
    }

    /* Caixa central com fundo levemente translúcido para destacar o conteúdo */
    .main .block-container {
        border: 2px solid #ffffff;
        border-radius: 12px;
        padding: 2rem;
        background-color: rgba(255, 255, 255, 0.95);
    }

    /* Letras com um tom escuro elegante para contrastar perfeitamente */
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #03045e !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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

st.title("🐾 PokéDex Regional - Aztlas")
st.markdown("Bem-vindo ao painel central do RPG!")

abas = st.tabs(["📋 Pokédex", "✨ Habilidades", "🎒 Itens"])

with abas[0]:
  st.subheader("Lista de Pokémon Registados")

  df_pokemon = carregar_dados_pokemon()

  if not df_pokemon.empty:
    # Mostramos os dados numa tabela interativa do Streamlit
    st.dataframe(df_pokemon, use_container_width=True)
  else:
    st.info("A carregar dados ou tabela vazia.")
      def carregar_resumo_pokemon():
  # Abre a conexão com o banco de dados Aztlas_Dex.db
  with sqlite3.connect("Aztlas_Dex.db") as conn:
    # Seleciona apenas as colunas que você quer mostrar na lista resumida
    # Nota: Colunas com espaços no nome (como "Dex No.") usam aspas duplas em SQL
    query = """
            SELECT Nome, "Dex No.", "Tipo 1", "Tipo 2", SR 
            FROM Pokemon 
            ORDER BY ID
        """
    df = pd.read_sql_query(query, conn)
    return df


# --- Exibindo na aba de Pokédex ---
st.subheader("📋 Compêndio de Pokémon - Visão Rápida")

# Carrega os dados resumidos
df_resumo = carregar_resumo_pokemon()

if not df_resumo.empty:
  # st.dataframe desenha a tabela interativa na tela com as colunas escolhidas
  st.dataframe(
      df_resumo,
      use_container_width=True,
      hide_index=True,  # Oculta aquela coluna lateral de números de índice do Pandas
  )
else:
  st.info("Nenhum Pokémon encontrado no banco de dados.")
