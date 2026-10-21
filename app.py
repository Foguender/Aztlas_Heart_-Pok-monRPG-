import os
import sqlite3
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA E VISUAL (TEMA AZUL CERÚLEO)
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
        /* Gradiente animado em tons de azul cerúleo e celeste */
        background: linear-gradient(-45deg, #0077b6, #00b4d8, #48cae4, #90e0ef);
        background-size: 400% 400%;
        animation: fundoAnimado 12s ease infinite;
    }

    /* Caixa central com fundo branco e cantos arredondados */
    .main .block-container {
        border: 2px solid #ffffff;
        border-radius: 12px;
        padding: 2rem;
        background-color: rgba(255, 255, 255, 0.95);
    }

    /* Textos com um tom escuro elegante para garantir leitura perfeita */
    h1, h2, h3, h4, h5, h6, p, span, label, div {
        color: #03045e !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 2. FUNÇÕES DE CONEXÃO COM O BANCO DE DADOS
# -----------------------------------------------------------------------------
def obter_caminho_banco():
  caminho_atual = os.path.dirname(__file__)
  return os.path.join(caminho_atual, "Aztlas_Dex.db")


def carregar_resumo_pokemon():
  caminho_banco = obter_caminho_banco()

  if not os.path.exists(caminho_banco):
    st.warning("Ficheiro 'Aztlas_Dex.db' não foi encontrado na pasta do projeto!")
    return pd.DataFrame()

  # Abre a conexão com o SQLite e seleciona apenas os dados essenciais para a lista
  with sqlite3.connect(caminho_banco) as conn:
    query = """
            SELECT Nome, "Dex No.", "Tipo 1", "Tipo 2", SR 
            FROM Pokemon 
            ORDER BY ID
        """
    df = pd.read_sql_query(query, conn)
    return df


# -----------------------------------------------------------------------------
# 3. ESTRUTURA PRINCIPAL DO SITE (ABAS)
# -----------------------------------------------------------------------------
st.title("🐾 PokéDex Regional - Aztlas")
st.markdown(
    "Bem-vindo ao painel central do RPG! Aqui tens a lista rápida dos Pokémon"
    " registados."
)

# Criamos as abas do sistema
abas = st.tabs(["📋 Pokédex", "✨ Habilidades", "🎒 Itens"])

with abas[0]:
  st.subheader("Compêndio de Pokémon - Visão Rápida")

  # Carregamos os dados resumidos do banco
  df_resumo = carregar_resumo_pokemon()

  if not df_resumo.empty:
    # Mostramos a tabela limpa e sem o índice lateral
    st.dataframe(df_resumo, use_container_width=True, hide_index=True)
  else:
    st.info("A carregar dados ou tabela vazia.")

with abas[1]:
  st.subheader("Habilidades Passivas")
  st.info(
      "Em breve: Lista de habilidades e efeitos especiais vindos do banco de"
      " dados."
  )

with abas[2]:
  st.subheader("Itens e Equipamentos")
  st.info("Em breve: Gestão de itens, consumíveis e preços.")
