import os
import random  # <--- Adicionado para a flutuação automática
import sqlite3
import pandas as pd
import streamlit as st

# Configuração da página
st.set_page_config(page_title="PokéDex & Itens Aztlas", page_icon="🐾", layout="wide")

# -----------------------------------------------------------------------------
# 1. ESTADOS DE SESSÃO & MERCADO AUTOMÁTICO
# -----------------------------------------------------------------------------
if "modo_mestre" not in st.session_state:
    st.session_state.modo_mestre = False

if "modificadores_preco" not in st.session_state:
    st.session_state.modificadores_preco = {}


# Função para gerar a flutuação automática dos preços por categoria
def gerar_flutuacao_automatica(categorias):
    novos_modificadores = {}
    for cat in categorias:
        # Gera uma variação entre 0.7 (-30%) e 1.5 (+50%)
        # Arredondado para intervalos de 5% (ex: 0.85, 1.10, 1.25)
        variacao = round(random.uniform(0.70, 1.50), 2)
        novos_modificadores[cat] = variacao
    return novos_modificadores


# -----------------------------------------------------------------------------
# 2. PAINEL DE ACESSO (BARRA LATERAL)
# -----------------------------------------------------------------------------
st.sidebar.title("🔮 Aztlas-Heart")
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 Painel de Acesso")

senha = st.sidebar.text_input("Senha do Mestre:", type="password")

if senha == "Dusk_0256":
    st.session_state.modo_mestre = True
    st.sidebar.success("⚔️ Modo Mestre Ativo!")
else:
    st.session_state.modo_mestre = False
    if senha != "":
        st.sidebar.error("Senha incorreta.")

st.sidebar.markdown("---")


# -----------------------------------------------------------------------------
# 3. BANCO DE DADOS & QUERIES
# -----------------------------------------------------------------------------
def conectar_banco():
    caminho_atual = os.path.dirname(__file__)
    caminho_banco = os.path.join(caminho_atual, "pokedex aztlas - Copia.db")
    return sqlite3.connect(caminho_banco)


def carregar_dados_pokemon():
    conn = conectar_banco()
    query = "SELECT `ID`, `Dex No.`, `Nome`, `Tipo 1`, `Tipo 2`, `Habilidade 1` FROM pokemon"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def buscar_detalhes_completos(pokemon_id):
    conn = conectar_banco()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM pokemon WHERE "ID" = ?', (pokemon_id,))
    gerais = cursor.fetchone()

    cursor.execute(
        'SELECT "Espécie", "Descrição" FROM descricao_pokedexrpg WHERE "ID" = ?',
        (pokemon_id,),
    )
    descricao = cursor.fetchone()

    cursor.execute('SELECT * FROM "Base Stats" WHERE "ID" = ?', (pokemon_id,))
    stats = cursor.fetchone()

    cursor.execute('SELECT * FROM "Training_Breeding" WHERE "ID" = ?', (pokemon_id,))
    breeding = cursor.fetchone()

    try:
        query_moves = 'SELECT "Nível", "Ataque", "Tipo", "Classe", "Poder", "Acurácia" FROM "pokemon_moves" WHERE "pokemon_id" = ? ORDER BY "Nível" ASC'
        moves_df = pd.read_sql_query(query_moves, conn, params=(pokemon_id,))
    except Exception:
        moves_df = pd.DataFrame()

    conn.close()
    return gerais, descricao, stats, breeding, moves_df


def carregar_dados_itens():
    conn = conectar_banco()
    try:
        query = (
            'SELECT `ID`, `Tipo`, `Nome`, `Efeito`, `Descrição`, `Preço` FROM "Itens"'
        )
        df_itens = pd.read_sql_query(query, conn)
    except Exception:
        df_itens = pd.DataFrame(
            columns=["ID", "Tipo", "Nome", "Efeito", "Descrição", "Preço"]
        )
    conn.close()
    return df_itens


if "id_pokemon_selecionado" not in st.session_state:
    st.session_state.id_pokemon_selecionado = None


# -----------------------------------------------------------------------------
# 4. ESTRUTURA DE ABAS
# -----------------------------------------------------------------------------
abas_disponiveis = ["🐾 Pokédex Regional", "🎒 Compêndio de Itens"]
if st.session_state.modo_mestre:
    abas_disponiveis.append("🧙‍♂️ Escudo do Mestre")

abas = st.tabs(abas_disponiveis)


# ==============================================================================
# ABA 1: POKÉDEX REGIONAL
# ==============================================================================
with abas[0]:
    df_pokemon = carregar_dados_pokemon()

    st.sidebar.header("🔍 Filtros da Pokédex")
    filtro_nome = st.sidebar.text_input("Buscar Pokémon por Nome:", "")

    tipos_disponiveis = sorted(
        list(
            set(df_pokemon["Tipo 1"].dropna()) | set(df_pokemon["Tipo 2"].dropna())
        )
    )
    filtro_tipo = st.sidebar.selectbox(
        "Filtrar por Tipo:", ["Todos"] + tipos_disponiveis
    )

    coluna_ordenar = st.sidebar.selectbox(
        "Ordenar Pokémon por:", options=df_pokemon.columns.tolist(), index=2
    )
    ordem_crescente = st.sidebar.radio("Ordem Pokémon:", ["Crescente", "Decrescente"])
    ascendente = True if ordem_crescente == "Crescente" else False

    df_filtrado = df_pokemon.copy()

    if filtro_nome:
        df_filtrado = df_filtrado[
            df_filtrado["Nome"].str.contains(filtro_nome, case=False, na=False)
        ]

    if filtro_tipo != "Todos":
        df_filtrado = df_filtrado[
            (df_filtrado["Tipo 1"] == filtro_tipo)
            | (df_filtrado["Tipo 2"] == filtro_tipo)
        ]

    df_filtrado = df_filtrado.sort_values(by=coluna_ordenar, ascending=ascendente)

    if st.session_state.id_pokemon_selecionado is not None:
        if st.button("⬅ Voltar para a Lista"):
            st.session_state.id_pokemon_selecionado = None
            st.rerun()

        (
            poke_geral,
            poke_desc,
            poke_stats,
            poke_breed,
            poke_moves,
        ) = buscar_detalhes_completos(
            int(st.session_state.id_pokemon_selecionado)
        )

        if poke_geral:
            st.title(f"{poke_geral[2]} {poke_geral[1] if poke_geral[1] else ''}")

            aba1, aba2, aba3, aba4 = st.tabs(
                [
                    "📋 Dados Gerais",
                    "📊 Base Stats",
                    "🥚 Breeding & Training",
                    "⚔️ Golpes / Moves",
                ]
            )

            with aba1:
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(
                        "https://via.placeholder.com/250",
                        caption=poke_geral[2],
                        use_container_width=True,
                    )
                with col2:
                    st.subheader("Informações Biológicas")
                    if poke_desc:
                        st.markdown(f"**Espécie:** {poke_desc[0]}")
                        st.markdown(f"*\"{poke_desc[1]}\"*")

                    st.write("---")
                    st.markdown(
                        f"**Tipo 1:** {poke_geral[3]} | **Tipo 2:** {poke_geral[4] if poke_geral[4] else 'Nenhum'}"
                    )
                    st.markdown(
                        f"**Altura:** {poke_geral[5]} m | **Peso:** {poke_geral[6]} kg"
                    )

                    st.subheader("Habilidades")
                    st.markdown(f"- **Principal:** {poke_geral[7]}")
                    if poke_geral[8]:
                        st.markdown(f"- **Secundária:** {poke_geral[8]}")
                    if poke_geral[9]:
                        st.markdown(
                            f"- **Oculta (Habilidade E):** {poke_geral[9]}"
                        )

            with aba2:
                st.subheader("Estatísticas Base")
                if poke_stats:
                    stats_dados = {
                        "Status": [
                            "HP",
                            "Ataque",
                            "Defesa",
                            "Sp. Atk",
                            "Sp. Def",
                            "Velocidade",
                        ],
                        "Valor": [
                            poke_stats[2],
                            poke_stats[3],
                            poke_stats[4],
                            poke_stats[5],
                            poke_stats[6],
                            poke_stats[7],
                        ],
                    }
                    st.dataframe(
                        pd.DataFrame(stats_dados),
                        hide_index=True,
                        use_container_width=True,
                    )
                else:
                    st.info(
                        "Dados de Base Stats não encontrados para este Pokémon."
                    )

            with aba3:
                st.subheader("Dados de Cruzamento e Treinamento")
                if poke_breed:
                    st.markdown(f"**Rendimento de EV:** {poke_breed[2]}")
                    st.markdown(f"**Amizade Base:** {poke_breed[3]}")
                    st.markdown(
                        f"**Grupo de Ovos 1:** {poke_breed[4]} | **Grupo de Ovos 2:** {poke_breed[5] if poke_breed[5] else 'Nenhum'}"
                    )
                    st.markdown(f"**Taxa de Gênero:** {poke_breed[6]}")
                else:
                    st.info(
                        "Dados de Breeding/Training não encontrados para este Pokémon."
                    )

            with aba4:
                st.subheader("Lista de Golpes Aprendidos")
                if not poke_moves.empty:
                    st.dataframe(
                        poke_moves, hide_index=True, use_container_width=True
                    )
                else:
                    st.info(
                        "Nenhum golpe encontrado ou tabela de golpes não configurada."
                    )

    else:
        st.title("PokéDex Completa")
        st.write(
            "Selecione a caixinha ao lado esquerdo de qualquer Pokémon para abrir sua ficha detalhada."
        )

        df_tabela = df_filtrado.fillna("-")
        evento_selecao = st.dataframe(
            df_tabela,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
        )

        if (
            evento_selecao
            and "selection" in evento_selecao
            and "rows" in evento_selecao["selection"]
        ):
            linhas_selecionadas = evento_selecao["selection"]["rows"]
            if len(linhas_selecionadas) > 0:
                indice_linha = linhas_selecionadas[0]
                st.session_state.id_pokemon_selecionado = df_filtrado.iloc[
                    indice_linha
                ]["ID"]
                st.rerun()


# ==============================================================================
# ABA 2: COMPÊNDIO DE ITENS (COM CÁLCULO FLUTUANTE AUTOMÁTICO)
# ==============================================================================
with abas[1]:
    st.title("🎒 Compêndio de Itens & Equipamentos")
    st.markdown(
        "Consulte os consumíveis, esferas de captura, bagas e itens da região de Aztlas."
    )

    df_itens = carregar_dados_itens()

    if df_itens.empty:
        st.warning("Nenhum item encontrado na tabela 'Itens' da base de dados.")
    else:
        st.sidebar.markdown("---")
        st.sidebar.header("🎒 Filtros do Inventário")

        filtro_item_nome = st.sidebar.text_input("Buscar Item por Nome:", "")
        tipos_itens = ["Todos"] + sorted(list(df_itens["Tipo"].dropna().unique()))
        filtro_item_tipo = st.sidebar.selectbox(
            "Filtrar por Categoria/Tipo:", tipos_itens
        )

        df_itens_filtrados = df_itens.copy()

        if filtro_item_nome:
            df_itens_filtrados = df_itens_filtrados[
                df_itens_filtrados["Nome"].str.contains(
                    filtro_item_nome, case=False, na=False
                )
            ]

        if filtro_item_tipo != "Todos":
            df_itens_filtrados = df_itens_filtrados[
                df_itens_filtrados["Tipo"] == filtro_item_tipo
            ]

        # CALCULADORA DE PREÇO AUTOMÁTICA
        def calcular_preco_ajustado(row):
            preco_original = row["Preço"]
            if pd.isnull(preco_original) or preco_original == 0:
                return "Inestimável", "⚖️ Estável"

            tipo_item = row["Tipo"]
            # Puxa a variação do dia ou mantém 1.0 se o mercado não tiver rodado
            mod = st.session_state.modificadores_preco.get(tipo_item, 1.0)

            if mod != 1.0:
                preco_final = preco_original * mod
                pct = int(abs(mod - 1.0) * 100)

                if mod > 1.0:
                    status = f"📈 +{pct}% (Alta de Mercado)"
                else:
                    status = f"📉 -{pct}% (Oferta / Desconto)"

                return f"₽ {preco_final:,.2f}", status

            return f"₽ {preco_original:,.2f}", "⚖️ Estável"

        visualizacao = st.radio(
            "Modo de Visualização:",
            ["📋 Fichas Detalhadas", "📊 Tabela Geral"],
            horizontal=True,
        )

        if visualizacao == "📋 Fichas Detalhadas":
            for _, item in df_itens_filtrados.iterrows():
                preco_txt, status_preco = calcular_preco_ajustado(item)

                with st.expander(
                    f"📦 **{item['Nome']}** — *{item['Tipo']}* | 💰 **{preco_txt}** ({status_preco})"
                ):
                    col_e1, col_e2 = st.columns([1, 2])

                    with col_e1:
                        st.markdown(f"**Categoria:** `{item['Tipo']}`")
                        st.markdown(f"**Preço Atual:** {preco_txt}")
                        st.markdown(f"**Tendência do Mercado:** {status_preco}")

                        if (
                            pd.notnull(item["Efeito"])
                            and str(item["Efeito"]).strip() != ""
                        ):
                            st.info(f"⚡ **Efeito:** {item['Efeito']}")

                    with col_e2:
                        st.markdown("**Descrição Rápida / Lore:**")
                        st.write(
                            item["Descrição"]
                            if item["Descrição"]
                            else "Sem descrição cadastrada."
                        )
        else:
            df_exibicao = df_itens_filtrados.copy()

            df_exibicao["Preço Atual"] = df_exibicao.apply(
                lambda r: calcular_preco_ajustado(r)[0], axis=1
            )
            df_exibicao["Status do Mercado"] = df_exibicao.apply(
                lambda r: calcular_preco_ajustado(r)[1], axis=1
            )

            df_exibicao = df_exibicao.fillna("-")
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)


# ==============================================================================
# ABA 3: ESCUDO DO MESTRE (CONTROLE AUTOMÁTICO DO MERCADO)
# ==============================================================================
if st.session_state.modo_mestre:
    with abas[2]:
        st.title("🧙‍♂️ Escudo do Mestre")
        st.markdown(
            "Gerencie a economia e as regras do jogo com um clique."
        )

        sub_mercado, sub_regras = st.tabs(
            ["🎲 Algoritmo de Mercado", "📜 Regras Rápida"]
        )

        with sub_mercado:
            st.subheader("⚡ Gerador Automático de Economia")
            st.write(
                "Clique no botão abaixo para simular a mudança de dia e flutuar todos os preços de Aztlas de forma aleatória."
            )

            df_itens = carregar_dados_itens()
            categorias = (
                sorted(list(df_itens["Tipo"].dropna().unique()))
                if not df_itens.empty
                else []
            )

            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                if st.button("🎲 Rolar Novo Dia (Girar Mercado)", type="primary"):
                    st.session_state.modificadores_preco = (
                        gerar_flutuacao_automatica(categorias)
                    )
                    st.success("🎉 Economia atualizada com sucesso para todas as categorias!")
                    st.rerun()

            with col_btn2:
                if st.button("🔄 Resetar Mercado (Preços Base)"):
                    st.session_state.modificadores_preco = {}
                    st.info("Preços restaurados ao valor original do banco de dados.")
                    st.rerun()

            st.write("---")
            st.subheader("📊 Flutuações Vigentes do Dia")

            if not st.session_state.modificadores_preco:
                st.caption("O mercado está estável. Nenhuma flutuação ativa no momento.")
            else:
                for cat in categorias:
                    mod = st.session_state.modificadores_preco.get(cat, 1.0)
                    pct = int((mod - 1.0) * 100)

                    if pct > 0:
                        st.write(f"• **{cat}**: 📈 **+{pct}%** de inflação")
                    elif pct < 0:
                        st.write(f"• **{cat}**: 📉 **{pct}%** de desconto")
                    else:
                        st.write(f"• **{cat}**: ⚖️ Preço Base Sem Alteração")

        with sub_regras:
            st.info("Espaço reservado para anotações do Mestre.")
