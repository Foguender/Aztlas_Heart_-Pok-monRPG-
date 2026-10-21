import os
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(page_title="PokéDex Aztlas", page_icon="🐾", layout="wide")

# -----------------------------------------------------------------------------
# ESTILIZAÇÃO CSS - AZUL MAIS FORTE E ANIMADO
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
        /* Mudamos para tons de azul muito mais fortes e ricos */
        background: linear-gradient(-45deg, #003366, #005c8a, #0077b6, #023e8a);
        background-size: 400% 400%;
        /* Diminuímos para 10s para a mudança de cor ficar mais rápida e visível */
        animation: fundoAnimado 10s ease infinite;
    }

    /* Caixa central com fundo claro para garantir que a leitura fique perfeita */
    .main .block-container {
        border: 2px solid #90e0ef;
        border-radius: 12px;
        padding: 2rem;
        background-color: rgba(255, 255, 255, 0.92);
    }

    /* Textos com um azul bem escuro (quase preto) para dar contraste máximo */
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
