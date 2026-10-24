import os
import random
import sqlite3
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA & ESTILO (TEMA AZUL CERÚLEO + ANIMAÇÃO DE CLIQUE)
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

    /* --- ONDA DE CLIQUE DA POKÉDEX --- */
    .onda-pokedex {
        position: fixed;
        border: 2px solid rgba(255, 255, 255, 0.9);
        border-radius: 50%;
        pointer-events: none;
        transform: translate(-50%, -50%);
        animation: expandirOnda 0.6s ease-out forwards;
        z-index: 999999;
        box-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
    }

    @keyframes expandirOnda {
        0% { width: 0px; height: 0px; opacity: 1; }
        100% { width: 150px; height: 150px; opacity: 0; border-width: 1px; }
    }
    </style>

    <script>
    document.addEventListener('click', function(e) {
        const onda = document.createElement('div');
        onda.className = 'onda-pokedex';
        onda.style.left = e.clientX + 'px';
        onda.style.top = e.clientY + 'px';
        document.body.appendChild(onda);
        setTimeout(() => { onda.remove(); }, 600);
    });
    </script>
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
    # 1. Dados gerais, stats e breeding (Tudo vem direto da tabela Pokemon!)
    df_geral = carregar_tabela_segura(
        conn, 'SELECT * FROM Pokemon WHERE "ID" = ?', (pokemon_id,)
    )
    gerais = df_geral.iloc[0].to_dict() if not df_geral.empty else {}

    # 2. Descrição (se houver tabela de descrições)
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

    # 3. Golpes
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

    # 4. Evoluções
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

    # 5. Localização
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


def gerar_flutuacao_automatica(categorias):
  novos_modificadores = {}
  for cat in categorias:
    variacao = round(random.uniform(0.70, 1.50), 2)
    novos_modificadores[cat] = 1.10 if variacao == 1.0 else variacao
  return novos_modificadores


# -----------------------------------------------------------------------------
# 3. BARRA LATERAL (LOGIN DO MESTRE)
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

    if st.session_state.id_pokemon_selecionado is not None:
      if st.button("⬅ Voltar para a Lista"):
        st.session_state.id_pokemon_selecionado = None
        st.rerun()

      poke_geral, poke_desc, golpes, poke_evo, poke_loc = (
          buscar_detalhes_completos(
              int(st.session_state.id_pokemon_selecionado)
          )
      )

      if poke_geral:
        nome_p = poke_geral.get("Nome", "Pokémon")
        dex_no = poke_geral.get("Dex No.", poke_geral.get("ID", ""))
        st.title(f"{nome_p} #{dex_no}")

        aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
            "📋 Dados Gerais",
            "📊 Atributos & Stats RPG",
            "🧬 Evoluções",
            "🗺️ Localização & Spawn",
            "🥚 Breeding & Training",
            "⚔️ Golpes / Moves",
        ])

        with aba1:
          col1, col2 = st.columns([1, 2])
          with col1:
            url_sprite = f"https://raw.githubusercontent.com/Foguender/Aztlas_Heart_-Pok-monRPG-/main/sprites/{poke_geral.get('ID')}.png"
            st.image(url_sprite, caption=nome_p, width=200)
          with col2:
            st.subheader("Informações Biológicas")
            if poke_desc and poke_desc[0]:
              st.markdown(f"**Espécie:** {poke_desc[0]}")
              st.markdown(f"*\"{poke_desc[1]}\"*")
            st.write("---")
            t1 = criar_badge_tipo(poke_geral.get("Tipo 1"))
            t2 = criar_badge_tipo(poke_geral.get("Tipo 2"))
            st.markdown(f"**Tipos:** {t1} {t2}", unsafe_allow_html=True)
            st.markdown(
                f"📏 **Tamanho:** {poke_geral.get('Tamanho', '—')} | 🎯"
                f" **SR:** {poke_geral.get('SR', '—')}"
            )
            st.write("---")
            st.subheader("✨ Habilidades")
            hab1 = poke_geral.get("Habilidade 1", "Nenhuma")
            hab2 = poke_geral.get("Habilidade 2", None)
            hab_e = poke_geral.get("Habilidade E", None)
            st.markdown(f"• **Habilidade 1:** `{hab1}`")
            if hab2:
              st.markdown(f"• **Habilidade 2:** `{hab2}`")
            if hab_e:
              st.markdown(f"• **Habilidade Oculta:** `{hab_e}`")

        with aba2:
          st.subheader("Atributos de RPG (Sistema D20)")
          col_s1, col_s2, col_s3 = st.columns(3)
          with col_s1:
            st.metric("HP", poke_geral.get("HP", "—"))
            st.metric("FOR", poke_geral.get("FOR", "—"))
            st.metric("DES", poke_geral.get("DES", "—"))
          with col_s2:
            st.metric("CON", poke_geral.get("CON", "—"))
            st.metric("INT", poke_geral.get("INT", "—"))
            st.metric("SAB", poke_geral.get("SAB", "—"))
          with col_s3:
            st.metric("CAR", poke_geral.get("CAR", "—"))
            st.metric("CA", poke_geral.get("CA", "—"))
            st.metric("Hit Dice", poke_geral.get("Hit Dice", "—"))

        with aba3:
          st.subheader("Linhagem de Evolução")
          if not poke_evo.empty:
            st.dataframe(poke_evo, width=800, hide_index=True)
          else:
            st.info("Este Pokémon não possui evoluções registadas.")

        with aba4:
          st.subheader("Locais de Aparição em Aztlas")
          if not poke_loc.empty:
            st.dataframe(poke_loc, width=800, hide_index=True)
          else:
            st.info("Sem locais de aparição cadastrados.")

        with aba5:
          st.subheader("Dados de Cruzamento e Treinamento")
          st.markdown(
              "**Grupo de Ovos 1:**"
              f" {poke_geral.get('Grupo de Ovos 1', '—')}"
          )
          st.markdown(
              "**Grupo de Ovos 2:**"
              f" {poke_geral.get('Grupo de Ovos 2', '—')}"
          )
          st.markdown(
              "**Taxa de Género M:**"
              f" {poke_geral.get('Tx. Genero M', '—')}%"
          )
          st.markdown(
              "**Taxa de Género F:**"
              f" {poke_geral.get('Tx. Genero F', '—')}%"
          )

        with aba6:
          st.subheader("⚔️ Movimentos e Golpes Aprendidos")
          tab_learn, tab_tm, tab_egg, tab_teacher = st.tabs(
              ["📜 Por Nível", "CDs / TMs & HMs", "🥚 Egg Moves", "👨‍🏫 Teacher Moves"]
          )

          def renderizar_tabela_pokemondb(df_golpes, coluna_nivel=None):
            if df_golpes.empty:
              st.info("Nenhum movimento registrado nesta categoria.")
              return
            df = df_golpes.copy()
            df_exibicao = pd.DataFrame()
            if coluna_nivel and coluna_nivel in df.columns:
              df_exibicao["Nível"] = df[coluna_nivel].apply(
                  lambda x: f"Lvl {x}" if pd.notnull(x) else "1"
              )
            if "Golpe_Nome" in df.columns:
              df_exibicao["Golpe"] = df["Golpe_Nome"].apply(
                  lambda x: f"<b>{x}</b>"
              )
            elif "Nome" in df.columns:
              df_exibicao["Golpe"] = df["Nome"].apply(
                  lambda x: f"<b>{x}</b>"
              )
            elif "Move" in df.columns:
              df_exibicao["Golpe"] = df["Move"].apply(
                  lambda x: f"<b>{x}</b>"
              )
            if "Tipo" in df.columns:
              df_exibicao["Tipo"] = df["Tipo"].apply(criar_badge_tipo)
            if "Categoria" in df.columns:
              df_exibicao["Classe"] = df["Categoria"].apply(
                  lambda x: (
                      '🔴 <span style="color:#e05244; font-weight:bold;">Físico</span>'
                      if "fís" in str(x).lower() or "fis" in str(x).lower()
                      else (
                          '🔵 <span style="color:#4a90e2;'
                          ' font-weight:bold;">Especial</span>'
                          if "esp" in str(x).lower()
                          else '⚪ <span style="color:#8e8e93;'
                          ' font-weight:bold;">Status</span>'
                      )
                  )
              )
            if "Poder" in df.columns:
              df_exibicao["Poder"] = df["Poder"].apply(
                  lambda x: (
                      str(x) if pd.notnull(x) and str(x) != "0" else "—"
                  )
              )
            if "Precisao" in df.columns:
              df_exibicao["Precisão"] = df["Precisao"].apply(
                  lambda x: f"{x}%" if pd.notnull(x) else "—"
              )
            elif "Accuracy" in df.columns:
              df_exibicao["Precisão"] = df["Accuracy"].apply(
                  lambda x: f"{x}%" if pd.notnull(x) else "—"
              )
            if "PP" in df.columns:
              df_exibicao["PP"] = df["PP"]
            if "Efeito" in df.columns:
              df_exibicao["Efeito / Descrição"] = df["Efeito"]
            st.write(
                df_exibicao.to_html(escape=False, index=False),
                unsafe_allow_html=True,
            )

          with tab_learn:
            renderizar_tabela_pokemondb(golpes["learnset"], coluna_nivel="Level")
          with tab_tm:
            renderizar_tabela_pokemondb(golpes["tm"])
          with tab_egg:
            renderizar_tabela_pokemondb(golpes["egg"])
          with tab_teacher:
            renderizar_tabela_pokemondb(golpes["teacher"])

    else:
      st.title("PokéDex Completa")
      evento_selecao = st.dataframe(
          df_filtrado.fillna("-"),
          width=1000,
          hide_index=True,
          on_select="rerun",
          selection_mode="single-row",
      )
      if (
          evento_selecao
          and "selection" in evento_selecao
          and evento_selecao["selection"]["rows"]
      ):
        idx = evento_selecao["selection"]["rows"][0]
        st.session_state.id_pokemon_selecionado = df_filtrado.iloc[idx]["ID"]
        st.rerun()


# ==============================================================================
# ABA 2: COMPÊNDIO DE HABILIDADES
# ==============================================================================
with abas[1]:
  st.title("✨ Compêndio de Habilidades (Abilities)")
  st.markdown("Consulte os efeitos passivos e mecânicas das habilidades.")
  df_hab = carregar_dados_habilidades()
  if df_hab.empty:
    st.warning("Nenhuma tabela de habilidades encontrada.")
  else:
    filtro_hab = st.text_input("🔍 Buscar Habilidade:", "")
    df_hab_filtradas = df_hab.copy()
    if filtro_hab:
      condicoes = pd.Series([False] * len(df_hab_filtradas))
      for col in df_hab_filtradas.columns:
        condicoes = condicoes | (
            df_hab_filtradas[col]
            .astype(str)
            .str.contains(filtro_hab, case=False, na=False)
        )
      df_hab_filtradas = df_hab_filtradas[condicoes]

    vis_hab = st.radio(
        "Modo de Visualização:",
        ["📋 Fichas Detalhadas", "📊 Tabela Geral"],
        horizontal=True,
    )
    if vis_hab == "📋 Fichas Detalhadas":
      for _, hab in df_hab_filtradas.iterrows():
        nome_h = hab.get("Nome", hab.get("ID", "Habilidade"))
        efeito_h = hab.get("Efeito", "")
        desc_h = hab.get("Descrição", "")
        with st.expander(f"✨ **{nome_h}**"):
          if (
              pd.notnull(efeito_h)
              and str(efeito_h).strip() not in ["", "-", "None"]
          ):
            st.info(f"⚡ **Efeito:** {efeito_h}")
          if (
              pd.notnull(desc_h)
              and str(desc_h).strip() not in ["", "-", "None"]
          ):
            st.markdown(f"**Descrição:**\n{desc_h}")
    else:
      st.dataframe(df_hab_filtradas.fillna("-"), width=1000, hide_index=True)


# ==============================================================================
# ABA 3: COMPÊNDIO DE ITENS
# ==============================================================================
with abas[2]:
  st.title("🎒 Compêndio de Itens & Equipamentos")
  df_itens = carregar_dados_itens()
  if df_itens.empty:
    st.warning("Nenhum item encontrado.")
  else:
    st.sidebar.markdown("---")
    st.sidebar.header("🎒 Filtros do Inventário")
    filtro_item_nome = st.sidebar.text_input("Buscar Item:", "")
    tipos_itens = (
        ["Todos"] + sorted(list(df_itens["Tipo"].dropna().unique()))
        if "Tipo" in df_itens.columns
        else ["Todos"]
    )
    filtro_item_tipo = st.sidebar.selectbox("Filtrar por Tipo:", tipos_itens)

    df_itens_filtrados = df_itens.copy()
    if filtro_item_nome and "Nome" in df_itens_filtrados.columns:
      df_itens_filtrados = df_itens_filtrados[
          df_itens_filtrados["Nome"].str.contains(
              filtro_item_nome, case=False, na=False
          )
      ]
    if filtro_item_tipo != "Todos" and "Tipo" in df_itens_filtrados.columns:
      df_itens_filtrados = df_itens_filtrados[
          df_itens_filtrados["Tipo"] == filtro_item_tipo
      ]


    def processar_exibicao_preco(row):
      preco_raw = row.get("Preço", None)
      try:
        if pd.isnull(preco_raw) or preco_raw is None:
          return "Inestimável", ""
        preco_original = float(preco_raw)
      except (ValueError, TypeError):
        return "Inestimável", ""
      if preco_original == 0:
        return "Grátis", ""
      if not st.session_state.modo_mestre:
        return f"₽ {preco_original:,.2f}", ""
      tipo_item = row.get("Tipo", "")
      mod = st.session_state.modificadores_preco.get(tipo_item, 1.0)
      preco_final = preco_original * mod
      pct = int(abs(mod - 1.0) * 100)
      status = (
          f"📈 +{pct}% (Alta)"
          if mod > 1.0
          else (f"📉 -{pct}% (Desconto)" if mod < 1.0 else "⚖️ Base")
      )
      return f"₽ {preco_final:,.2f}", status


    visualizacao = st.radio(
        "Visualização:",
        ["📋 Fichas Detalhadas", "📊 Tabela Geral"],
        horizontal=True,
    )
    if visualizacao == "📋 Fichas Detalhadas":
      for _, item in df_itens_filtrados.iterrows():
        preco_txt, status_preco = processar_exibicao_preco(item)
        titulo_expander = (
            f"📦 **{item.get('Nome', 'Item')}** — *{item.get('Tipo', '')}* |"
            f" 💰 **{preco_txt}**"
        )
        if st.session_state.modo_mestre and status_preco:
          titulo_expander += f" ({status_preco})"
        with st.expander(titulo_expander):
          col_e1, col_e2 = st.columns([1, 2])
          with col_e1:
            st.markdown(f"**Categoria:** `{item.get('Tipo', '—')}`")
            st.markdown(f"**Preço:** {preco_txt}")
            efeito = item.get("Efeito", None)
            if pd.notnull(efeito) and str(efeito).strip() != "":
              st.info(f"⚡ **Efeito:** {efeito}")
          with col_e2:
            st.markdown("**Descrição / Lore:**")
            st.write(item.get("Descricao", "Sem descrição."))
    else:
      df_exibicao = df_itens_filtrados.copy()
      df_exibicao["Preço"] = df_exibicao.apply(
          lambda r: processar_exibicao_preco(r)[0], axis=1
      )
      if st.session_state.modo_mestre:
        df_exibicao["Status Mercado"] = df_exibicao.apply(
            lambda r: processar_exibicao_preco(r)[1], axis=1
        )
      st.dataframe(df_exibicao.fillna("-"), width=1000, hide_index=True)


# ==============================================================================
# ABA 4: ESCUDO DO MESTRE
# ==============================================================================
if st.session_state.modo_mestre:
  with abas[3]:
    st.title("🧙‍♂️ Escudo do Mestre")
    sub_mercado, sub_roleplay, sub_regras = st.tabs(
        ["🎲 Mercado", "🎭 Roleplay & Improv", "📜 Regras Rápidas"]
    )
    df_itens = carregar_dados_itens()
    categorias_existentes = (
        sorted(list(df_itens["Tipo"].dropna().unique()))
        if not df_itens.empty and "Tipo" in df_itens.columns
        else []
    )

    with sub_mercado:
      col_btn1, col_btn2 = st.columns(2)
      with col_btn1:
        if st.button("🎲 Girar Mercado", type="primary"):
          st.session_state.modificadores_preco = gerar_flutuacao_automatica(
              categorias_existentes
          )
          st.success("Mercado atualizado!")
          st.rerun()
      with col_btn2:
        if st.button("🔄 Resetar Preços"):
          st.session_state.modificadores_preco = {
              cat: 1.0 for cat in categorias_existentes
          }
          st.info("Preços restaurados.")
          st.rerun()
      for cat in categorias_existentes:
        mod = st.session_state.modificadores_preco.get(cat, 1.0)
        pct = int((mod - 1.0) * 100)
        st.write(f"• **{cat}**: Modificador de {mod}x ({pct}%)")

    with sub_roleplay:
      st.markdown("### 🎲 Eventos Aleatórios")
      if st.button("🔮 Sortear Evento"):
        st.info("Um clima repentino alterou as condições da rota!")

    with sub_regras:
      st.markdown("### 📜 Regras do Sistema")
      caminho_regras = os.path.join(
          os.path.dirname(__file__), "regras_mestre.md"
      )
      if os.path.exists(caminho_regras):
        with open(caminho_regras, "r", encoding="utf-8") as f:
          st.markdown(f.read())
      else:
        st.info("Arquivo `regras_mestre.md` não encontrado.")
