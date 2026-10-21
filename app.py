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
    return pd.DataFrame()

  with sqlite3.connect(caminho_banco) as conn:
    query = """
            SELECT Nome, "Dex No.", "Tipo 1", "Tipo 2", SR 
            FROM Pokemon 
            ORDER BY ID
        """
    return pd.read_sql_query(query, conn)


def carregar_detalhes_pokemon(nome_pokemon):
  caminho_banco = obter_caminho_banco()
  if not os.path.exists(caminho_banco):
    return None

  with sqlite3.connect(caminho_banco) as conn:
    # Pega absolutamente TUDO (`*`) daquele Pokémon específico
    query = "SELECT * FROM Pokemon WHERE Nome = ?"
    df = pd.read_sql_query(query, conn, params=(nome_pokemon,))
    if not df.empty:
      return df.iloc[0]  # Retorna a primeira linha como um dicionário/série de dados
  return None


# -----------------------------------------------------------------------------
# 3. ESTRUTURA PRINCIPAL DO SITE (ABAS)
# -----------------------------------------------------------------------------
st.title("🐾 PokéDex Regional - Aztlas")
st.markdown("Painel central do RPG de mesa.")

abas = st.tabs(["📋 Pokédex", "✨ Habilidades", "🎒 Itens"])

with abas[0]:
  st.subheader("Compêndio de Pokémon - Visão Rápida")

  df_resumo = carregar_resumo_pokemon()

  if not df_resumo.empty:
    # Mostramos a tabela resumida
    st.dataframe(df_resumo, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🔍 Ficha Completa do Pokémon")

    # Criamos uma caixa de seleção para escolher o Pokémon pelo nome
    lista_nomes = df_resumo["Nome"].tolist()
    pokemon_escolhido = st.selectbox(
        "Selecione um Pokémon para ver todos os detalhes:", lista_nomes
    )

    if pokemon_escolhido:
      # Buscamos todas as informações detalhadas dele no banco
      dados_pkmn = carregar_detalhes_pokemon(pokemon_escolhido)

      if dados_pkmn is not None:
        # Exibimos os dados de forma organizada (tipo ficha de RPG)
        st.markdown(f"### 🛡️ Ficha: {dados_pkmn['Nome']}")

        # Exemplo de organização em colunas para os atributos principais
        col1, col2, col3 = st.columns(3)
        with col1:
          st.write(f"**Número na Dex:** {dados_pkmn['Dex No.']}")
          st.write(f"**Tipo 1:** {dados_pkmn['Tipo 1']}")
        with col2:
          st.write(f"**Tipo 2:** {dados_pkmn.get('Tipo 2', 'Nenhum')}")
          st.write(f"**SR (Desafio):** {dados_pkmn['SR']}")
        with col3:
          st.write(f"**Tamanho:** {dados_pkmn.get('Tamanho', 'Desconhecido')}")

        # Se quiseres ver todas as colunas brutas que existem na linha caso queiras conferir:
        with st.expander("Ver dados brutos completos da tabela"):
          st.write(dados_pkmn)
      else:
        st.warning("Não foram encontrados detalhes para este Pokémon.")
  else:
    st.info(
        "A tabela de Pokémon está vazia ou o ficheiro de base de dados não foi"
        " encontrado."
    )

with abas[1]:
  st.subheader("Habilidades Passivas")
  st.info("Em breve: Lista de habilidades.")

with abas[2]:
  st.subheader("Itens e Equipamentos")
  st.info("Em breve: Gestão de itens.")
