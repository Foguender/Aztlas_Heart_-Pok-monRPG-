import os
import random
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
# 2. FUNÇÕES AUXILIARES DE BADGES
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
# 3. CONEXÃO COM O BANCO DE DADOS
# -----------------------------------------------------------------------------
def obter_caminho_banco():
  caminho_atual = os.path.dirname(__file__)
  return os.path.join(caminho_atual, "Aztlas_Dex.db")


def carregar_dados_pokemon():
  caminho_banco = obter_caminho_banco()
  if not os.path.exists(caminho_banco):
    return pd.DataFrame()

  with sqlite3.connect(caminho_banco) as conn:
    # Carrega a tabela resumida para a lista inicial
    query = """SELECT ID, Nome, "Dex No.", "Tipo 1", "Tipo 2", SR FROM Pokemon ORDER BY ID"""
    return pd.read_sql_query(query, conn)


def buscar_detalhes_pokemon(pokemon_id):
  caminho_banco = obter_caminho_banco()
  with sqlite3.connect(caminho_banco) as conn:
    df = pd.read_sql_query(
        "SELECT * FROM Pokemon WHERE ID = ?", conn, params=(pokemon_id,)
    )
    return df.iloc[0].to_dict() if not df.empty else None


# -----------------------------------------------------------------------------
# 4. CONTROLE DE ESTADO DA SESSÃO
# -----------------------------------------------------------------------------
if "id_pokemon_selecionado" not in st.session_state:
  st.session_state.id_pokemon_selecionado = None


# -----------------------------------------------------------------------------
# 5. ESTRUTURA PRINCIPAL DO SITE
# -----------------------------------------------------------------------------
st.title("🐾 PokéDex Regional - Aztlas")

abas = st.tabs(
    ["📋 Pokédex Regional", "✨ Compêndio de Habilidades", "🎒 Compêndio de Itens"]
)

# ==============================================================================
# ABA 1: POKÉDEX REGIONAL (COM NAVEGAÇÃO POR CLIQUE NA LINHA)
# ==============================================================================
with abas[0]:
  df_pokemon = carregar_dados_pokemon()

  if df_pokemon.empty:
    st.warning("O banco de dados de Pokémon não foi encontrado ou está vazio.")
  else:
    # SE UM POKÉMON FOI SELECIONADO -> MOSTRA A FICHA DETALHADA
    if st.session_state.id_pokemon_selecionado is not None:
      if st.button("⬅ Voltar para a Lista"):
        st.session_state.id_pokemon_selecionado = None
        st.rerun()

      poke_geral = buscar_detalhes_pokemon(
          st.session_state.id_pokemon_selecionado
      )

      if poke_geral:
        nome_p = poke_geral.get("Nome", "Pokémon")
        dex_no = poke_geral.get("Dex No.", poke_geral.get("ID", ""))
        st.subheader(f"🛡️ Ficha: {nome_p} #{dex_no}")

        aba1, aba2 = st.tabs(["📋 Dados Gerais", "📊 Atributos de RPG"])

        with aba1:
          col1, col2 = st.columns([1, 2])
          with col1:
            st.metric("Número na Dex", f"#{dex_no}")
            t1 = criar_badge_tipo(poke_geral.get("Tipo 1"))
            t2 = criar_badge_tipo(poke_geral.get("Tipo 2"))
            st.markdown(f"**Tipos:** {t1} {t2}", unsafe_allow_html=True)
          with col2:
            st.markdown(f"**SR (Nível de Desafio):** {poke_geral.get('SR', '—')}")
            st.markdown(
                f"**Tamanho:** {poke_geral.get('Tamanho', 'Desconhecido')}"
            )
            st.markdown(
                f"**Habilidade 1:** `{poke_geral.get('Habilidade 1', 'Nenhuma')}`"
            )

        with aba2:
          st.write("**Dados brutos do Pokémon:**")
          st.json(poke_geral)

    # SE NENHUM POKÉMON FOI SELECIONADO -> MOSTRA A TABELA COMPLETA
    else:
      st.markdown(
          "Clique em qualquer linha da tabela para abrir a ficha completa do"
          " Pokémon:"
      )

      # Usa o evento de seleção de linha do Streamlit!
      evento_selecao = st.dataframe(
          df_pokemon.fillna("-"),
          use_container_width=True,
          hide_index=True,
          on_select="rerun",
          selection_mode="single-row",
      )

      # Captura o clique na tabela e guarda o ID no session_state
      if (
          evento_selecao
          and "selection" in evento_selecao
          and evento_selecao["selection"]["rows"]
      ):
        idx = evento_selecao["selection"]["rows"][0]
        st.session_state.id_pokemon_selecionado = df_pokemon.iloc[idx]["ID"]
        st.rerun()

# ==============================================================================
# ABAS SECUNDÁRIAS
# ==============================================================================
with abas[1]:
  st.subheader("✨ Compêndio de Habilidades")
  st.info("Espaço reservado para as habilidades do sistema.")

with abas[2]:
  st.subheader("🎒 Compêndio de Itens")
  st.info("Espaço reservado para os itens e equipamentos.")
