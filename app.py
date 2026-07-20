import os
import random
import sqlite3
import pandas as pd
import streamlit as st

# Configuração da página
st.set_page_config(page_title="PokéDex & Itens Aztlas", page_icon="🐾", layout="wide")


# -----------------------------------------------------------------------------
# 1. BANCO DE DADOS & QUERIES
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
        query = 'SELECT `ID`, `Tipo`, `Nome`, `Efeito`, `Descrição`, `Preço` FROM "Itens"'
        df_itens = pd.read_sql_query(query, conn)
        # Converte a coluna Preço para formato numérico com segurança
        df_itens["Preço"] = pd.to_numeric(df_itens["Preço"], errors="coerce")
    except Exception:
        df_itens = pd.DataFrame(
            columns=["ID", "Tipo", "Nome", "Efeito", "Descrição", "Preço"]
        )
    conn.close()
    return df_itens


# -----------------------------------------------------------------------------
# 2. ESTADOS DE SESSÃO & MERCADO AUTOMÁTICO
# -----------------------------------------------------------------------------
if "modo_mestre" not in st.session_state:
    st.session_state.modo_mestre = False

if "modificadores_preco" not in st.session_state:
    st.session_state.modificadores_preco = {}


def gerar_flutuacao_automatica(categorias):
    novos_modificadores = {}
    for cat in categorias:
        variacao = round(random.uniform(0.70, 1.50), 2)
        if variacao == 1.0:
            variacao = 1.10
        novos_modificadores[cat] = variacao
    return novos_modificadores


# -----------------------------------------------------------------------------
# 3. PAINEL DE ACESSO (BARRA LATERAL)
# -----------------------------------------------------------------------------
st.sidebar.title("🔮 Aztlas-Heart")
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 Painel de Acesso")

senha = st.sidebar.text_input("Senha do Mestre:", type="password")

if senha == "aztlas2026":
    st.session_state.modo_mestre = True
    st.sidebar.success("⚔️ Modo Mestre Ativo!")
else:
    st.session_state.modo_mestre = False
    if senha != "":
        st.sidebar.error("Senha incorreta.")

st.sidebar.markdown("---")

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
# ABA 2: COMPÊNDIO DE ITENS
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

        # CALCULADORA INTELIGENTE DE PREÇO (COM CONVERSÃO SEGURA)
        def processar_exibicao_preco(row):
            preco_raw = row["Preço"]

            # Validação e conversão segura para float
            try:
                if pd.isnull(preco_raw) or preco_raw is None:
                    return "Inestimável", ""
                preco_original = float(preco_raw)
            except (ValueError, TypeError):
                return "Inestimável", ""

            if preco_original == 0:
                return "Grátis / Inestimável", ""

            # --- VISÃO DO JOGADOR (PREÇO BASE LIMPO) ---
            if not st.session_state.modo_mestre:
                return f"₽ {preco_original:,.2f}", ""

            # --- VISÃO EXCLUSIVA DO MESTRE (COM FLUTUAÇÃO) ---
            tipo_item = row["Tipo"]
            mod = st.session_state.modificadores_preco.get(tipo_item, 1.0)
            preco_final = preco_original * mod
            pct = int(abs(mod - 1.0) * 100)

            if mod > 1.0:
                status = f"📈 +{pct}% (Alta)"
            elif mod < 1.0:
                status = f"📉 -{pct}% (Desconto)"
            else:
                status = "⚖️ Base"

            return f"₽ {preco_final:,.2f}", status

        visualizacao = st.radio(
            "Modo de Visualização:",
            ["📋 Fichas Detalhadas", "📊 Tabela Geral"],
            horizontal=True,
        )

        if visualizacao == "📋 Fichas Detalhadas":
            for _, item in df_itens_filtrados.iterrows():
                preco_txt, status_preco = processar_exibicao_preco(item)

                if st.session_state.modo_mestre and status_preco:
                    titulo_expander = f"📦 **{item['Nome']}** — *{item['Tipo']}* | 💰 **{preco_txt}** ({status_preco})"
                else:
                    titulo_expander = f"📦 **{item['Nome']}** — *{item['Tipo']}* | 💰 **{preco_txt}**"

                with st.expander(titulo_expander):
                    col_e1, col_e2 = st.columns([1, 2])

                    with col_e1:
                        st.markdown(f"**Categoria:** `{item['Tipo']}`")
                        st.markdown(f"**Preço:** {preco_txt}")

                        if st.session_state.modo_mestre and status_preco:
                            st.caption(f"Status da Flutuação: {status_preco}")

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

            df_exibicao["Preço"] = df_exibicao.apply(
                lambda r: processar_exibicao_preco(r)[0], axis=1
            )

            if st.session_state.modo_mestre:
                df_exibicao["Status Mercado (Mestre)"] = df_exibicao.apply(
                    lambda r: processar_exibicao_preco(r)[1], axis=1
                )

            df_exibicao = df_exibicao.fillna("-")
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)


# ==============================================================================
# ABA 3: ESCUDO DO MESTRE
# ==============================================================================
if st.session_state.modo_mestre:
    with abas[2]:
        st.title("🧙‍♂️ Escudo do Mestre")
        st.markdown(
            "Painel de gerenciamento do ecossistema e economia de Aztlas."
        )

        sub_mercado, sub_regras = st.tabs(
            ["🎲 Algoritmo de Mercado", "📜 Regras Rápidas"]
        )

        df_itens = carregar_dados_itens()
        categorias_existentes = (
            sorted(list(df_itens["Tipo"].dropna().unique()))
            if not df_itens.empty
            else []
        )

        with sub_mercado:
            st.subheader("⚡ Gerador de Economia Automática")

            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:
                if st.button("🎲 Girar Mercado (Simular Novo Dia)", type="primary"):
                    st.session_state.modificadores_preco = (
                        gerar_flutuacao_automatica(categorias_existentes)
                    )
                    st.success("🎉 Mercado atualizado! Novos percentuais gerados.")
                    st.rerun()

            with col_btn2:
                if st.button("🔄 Resetar Mercado (Voltar aos Preços Base)"):
                    st.session_state.modificadores_preco = {
                        cat: 1.0 for cat in categorias_existentes
                    }
                    st.info("Preços restaurados ao valor base do banco de dados.")
                    st.rerun()

            st.write("---")
            st.subheader("📊 Flutuações Vigentes no Momento")

            if not st.session_state.modificadores_preco:
                st.caption(
                    "Nenhuma flutuação gerada ainda hoje. Clique em 'Girar Mercado' para simular."
                )
            else:
                for cat in categorias_existentes:
                    mod = st.session_state.modificadores_preco.get(cat, 1.0)
                    pct = int((mod - 1.0) * 100)

                    if pct > 0:
                        st.write(f"• **{cat}**: 📈 **+{pct}%** (Inflação)")
                    elif pct < 0:
                        st.write(f"• **{cat}**: 📉 **{pct}%** (Desconto)")
                    else:
                        st.write(f"• **{cat}**: ⚖️ **0%** (Preço Base Original)")

        with sub_regras:
            st.info("Espaço reservado para anotações rápidas do Mestre.")
