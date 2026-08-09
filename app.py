import os
import random
import sqlite3
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(page_title="PokéDex Aztlas", page_icon="🐾", layout="wide")


# -----------------------------------------------------------------------------
# ESTILIZAÇÃO COMPLEMENTAR (ESTILO POKÉMONDB)
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
        "Dragon": "#6F35FC",
        "Sombrio": "#775544",
        "Metal": "#B7B7CE",
        "Aço": "#B7B7CE",
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


def criar_badge_categoria(categoria):
    if not categoria or pd.isna(categoria):
        return "—"

    cat_str = str(categoria).lower()
    if "fís" in cat_str or "fis" in cat_str or "physical" in cat_str:
        return '🔴 <span style="color:#e05244; font-weight:bold;">Físico</span>'
    elif "esp" in cat_str or "special" in cat_str:
        return '🔵 <span style="color:#4a90e2; font-weight:bold;">Especial</span>'
    else:
        return '⚪ <span style="color:#8e8e93; font-weight:bold;">Status</span>'


# -----------------------------------------------------------------------------
# 1. BANCO DE DADOS & QUERIES
# -----------------------------------------------------------------------------
def obter_caminho_banco():
    caminho_atual = os.path.dirname(__file__)
    return os.path.join(caminho_atual, "pokedex aztlas - Copia.db")


def carregar_dados_pokemon():
    caminho_banco = obter_caminho_banco()
    if not os.path.exists(caminho_banco):
        return pd.DataFrame(
            columns=["ID", "Dex No.", "Nome", "Tipo 1", "Tipo 2", "Tamanho", "SR"]
        )

    with sqlite3.connect(caminho_banco) as conn:
        query = (
            "SELECT `ID`, `Dex No.`, `Nome`, `Tipo 1`, `Tipo 2`, `Tamanho`, `SR`"
            " FROM pokemon"
        )
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
        cursor = conn.cursor()

        # 1. Dados Gerais
        cursor.execute('SELECT * FROM pokemon WHERE "ID" = ?', (pokemon_id,))
        gerais = cursor.fetchone()

        # 2. Descrição
        try:
            cursor.execute(
                'SELECT "Espécie", "Descrição" FROM descricao_pokedexrpg WHERE "ID" = ?',
                (pokemon_id,),
            )
            descricao = cursor.fetchone()
        except Exception:
            try:
                cursor.execute(
                    'SELECT "EspÃ©cie", "DescriÃ§Ã£o" FROM descricao_pokedexrpg WHERE "ID" = ?',
                    (pokemon_id,),
                )
                descricao = cursor.fetchone()
            except Exception:
                descricao = ("Sem espécie", "Sem descrição disponível.")

        # 3. Base Stats
        cursor.execute(
            'SELECT * FROM "Base Stats" WHERE "id_pokemon" = ?', (pokemon_id,)
        )
        stats = cursor.fetchone()
        if not stats:
            cursor.execute(
                'SELECT * FROM "Base Stats" WHERE "ID" = ?', (pokemon_id,)
            )
            stats = cursor.fetchone()

        # 4. Breeding & Training
        cursor.execute(
            'SELECT * FROM "Tr_Br" WHERE "ID" = ?', (pokemon_id,)
        )
        breeding = cursor.fetchone()

        # 5. Consultas Específicas de Golpes (Learnset, TM, Egg, Teacher)
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

        # Fallback genérico para a tabela antiga caso as específicas estejam vazias
        if learnset_df.empty and tm_df.empty and egg_df.empty and teacher_df.empty:
            learnset_df = carregar_tabela_segura(
                conn,
                'SELECT * FROM "pokemon_moves" WHERE "pokemon_id" = ?',
                (pokemon_id,),
            )

        # 6. Evoluções
        query_evo = """
            SELECT 
                p1.Nome AS [Forma Inicial],
                e.forma_de_2evoluir AS [Método / Requisito 1],
                p2.Nome AS [2ª Evolução],
                e.forma_de_3evoluir AS [Método / Requisito 2],
                p3.Nome AS [3ª Evolução]
            FROM Evolution_chart e
            LEFT JOIN pokemon p1 ON e.pokemon_id_1 = p1.ID
            LEFT JOIN pokemon p2 ON e.pokemon_id_2 = p2.ID
            LEFT JOIN pokemon p3 ON e.pokemon_id_3 = p3.ID
            WHERE e.pokemon_id_1 = ? OR e.pokemon_id_2 = ? OR e.pokemon_id_3 = ?
        """
        evo_df = carregar_tabela_segura(
            conn, query_evo, (pokemon_id, pokemon_id, pokemon_id)
        )

        # 7. Localização
        loc_df = pd.DataFrame()
        for nome_tabela in [
            "Locations_Pok mon",
            "Locations_Pokémon",
            "location_pokemon",
        ]:
            query_loc = f"""
                SELECT l.Location AS [Local], lp.spawn_method AS [Método], 
                       lp.chance_rate AS [Chance], lp.min_level AS [Nível Mín], 
                       lp.max_level AS [Nível Máx], lp.time_of_day AS [Horário]
                FROM "{nome_tabela}" lp
                JOIN Locations l ON lp.location_id = l.ID
                WHERE lp.pokemon_id = ?
            """
            loc_df = carregar_tabela_segura(conn, query_loc, (pokemon_id,))
            if not loc_df.empty:
                break

    golpes_dict = {
        "learnset": learnset_df,
        "tm": tm_df,
        "egg": egg_df,
        "teacher": teacher_df,
    }

    return gerais, descricao, stats, breeding, golpes_dict, evo_df, loc_df


def carregar_dados_habilidades():
    caminho_banco = obter_caminho_banco()
    if not os.path.exists(caminho_banco):
        return pd.DataFrame()

    with sqlite3.connect(caminho_banco) as conn:
        for nome_tabela in ["Habilidades", "Abilities", "habilidades"]:
            df = carregar_tabela_segura(conn, f'SELECT * FROM "{nome_tabela}"')
            if not df.empty:
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
# 3. BARRA LATERAL
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
        st.warning("O banco de dados de Pokémon não foi encontrado ou está vazio.")
    else:
        st.sidebar.header("🔍 Filtros da Pokédex")
        filtro_nome = st.sidebar.text_input("Buscar Pokémon por Nome:", "")

        tipos_disponiveis = sorted(
            list(
                set(df_pokemon["Tipo 1"].dropna().unique())
                | set(df_pokemon["Tipo 2"].dropna().unique())
            )
        )
        filtro_tipo = st.sidebar.selectbox(
            "Filtrar por Tipo:", ["Todos"] + tipos_disponiveis
        )

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

        if st.session_state.id_pokemon_selecionado is not None:
            if st.button("⬅ Voltar para a Lista"):
                st.session_state.id_pokemon_selecionado = None
                st.rerun()

            (
                poke_geral,
                poke_desc,
                poke_stats,
                poke_breed,
                golpes,
                poke_evo,
                poke_loc,
            ) = buscar_detalhes_completos(
                int(st.session_state.id_pokemon_selecionado)
            )

            if poke_geral:
                st.title(f"{poke_geral[2]} #{poke_geral[1]}")

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
                        url_sprite = f"https://raw.githubusercontent.com/Foguender/Aztlas_Heart_-Pok-monRPG-/main/sprites/{poke_geral[0]}.png"
                        st.image(
                            url_sprite,
                            caption=poke_geral[2],
                            use_container_width=True,
                        )
                    with col2:
                        st.subheader("Informações Biológicas")
                        if poke_desc:
                            st.markdown(f"**Espécie:** {poke_desc[0]}")
                            st.markdown(f"*\"{poke_desc[1]}\"*")
                        st.write("---")
                        
                        t1 = criar_badge_tipo(poke_geral[3])
                        t2 = criar_badge_tipo(poke_geral[4]) if poke_geral[4] else ""
                        st.markdown(f"**Tipos:** {t1} {t2}", unsafe_allow_html=True)
                        st.markdown(
                            f"📏 **Tamanho:** {poke_geral[5]} | 🎯 **SR:**"
                            f" {poke_geral[6]}"
                        )

                with aba2:
                    st.subheader("Atributos de RPG (Sistema D20)")
                    if poke_stats:
                        col_s1, col_s2, col_s3 = st.columns(3)
                        with col_s1:
                            st.metric("HP", poke_stats[2])
                            st.metric("FOR", poke_stats[3])
                            st.metric("DES", poke_stats[4])
                        with col_s2:
                            st.metric("CON", poke_stats[5])
                            st.metric("INT", poke_stats[6])
                            st.metric("SAB", poke_stats[7])
                        with col_s3:
                            st.metric("CAR", poke_stats[8])
                            if len(poke_stats) > 12:
                                st.metric("CA", poke_stats[12])

                with aba3:
                    st.subheader("Linhagem de Evolução")
                    st.dataframe(
                        poke_evo if not poke_evo.empty else "Sem evoluções.",
                        use_container_width=True,
                        hide_index=True,
                    )

                with aba4:
                    st.subheader("Locais de Aparição em Aztlas")
                    st.dataframe(
                        poke_loc if not poke_loc.empty else "Sem locais salvos.",
                        use_container_width=True,
                        hide_index=True,
                    )

                with aba5:
                    st.subheader("Dados de Cruzamento e Treinamento")
                    if poke_breed:
                        st.markdown(f"**EV:** {poke_breed[2]}")
                        st.markdown(f"**Amizade Base:** {poke_breed[3]}")
                        st.markdown(
                            f"**Grupo de Ovos:** {poke_breed[4]} /"
                            f" {poke_breed[5]}"
                        )

                with aba6:
                    st.subheader("⚔️ Movimentos e Golpes Aprendidos")

                    tab_learn, tab_tm, tab_egg, tab_teacher = st.tabs([
                        "📜 Por Nível",
                        "💿 TMs & HMs",
                        "🥚 Egg Moves",
                        "👨‍🏫 Teacher Moves",
                    ])

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

                        if "Nome" in df.columns:
                            df_exibicao["Golpe"] = df["Nome"].apply(lambda x: f"<b>{x}</b>")
                        elif "Move" in df.columns:
                            df_exibicao["Golpe"] = df["Move"].apply(lambda x: f"<b>{x}</b>")

                        if "Tipo" in df.columns:
                            df_exibicao["Tipo"] = df["Tipo"].apply(criar_badge_tipo)

                        if "Categoria" in df.columns:
                            df_exibicao["Classe"] = df["Categoria"].apply(criar_badge_categoria)

                        if "Poder" in df.columns:
                            df_exibicao["Poder"] = df["Poder"].apply(
                                lambda x: str(x) if pd.notnull(x) and str(x) != "0" else "—"
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

                        html_table = df_exibicao.to_html(escape=False, index=False)
                        st.write(html_table, unsafe_allow_html=True)

                    with tab_learn:
                        renderizar_tabela_pokemondb(golpes["learnset"], coluna_nivel="Nivel")

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
                use_container_width=True,
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
                st.session_state.id_pokemon_selecionado = df_filtrado.iloc[idx][
                    "ID"
                ]
                st.rerun()


# ==============================================================================
# ABA 2: COMPÊNDIO DE HABILIDADES
# ==============================================================================
with abas[1]:
    st.title("✨ Compêndio de Habilidades (Abilities)")
    st.markdown("Consulte os efeitos passivos e mecânicas das habilidades Pokémon.")

    df_hab = carregar_dados_habilidades()

    if df_hab.empty:
        st.warning("Nenhuma tabela de habilidades foi encontrada no banco de dados.")
    else:
        filtro_hab = st.text_input("Buscar Habilidade por Nome:", "")
        if filtro_hab:
            coluna_nome = df_hab.columns[0]
            df_hab = df_hab[
                df_hab[coluna_nome].str.contains(filtro_hab, case=False, na=False)
            ]

        st.dataframe(
            df_hab.fillna("-"), use_container_width=True, hide_index=True
        )

# ==============================================================================
# ABA 3: COMPÊNDIO DE ITENS
# ==============================================================================
with abas[2]:
    st.title("🎒 Compêndio de Itens & Equipamentos")
    st.markdown(
        "Consulte os consumíveis, esferas de captura, bagas e equipamentos da"
        " região de Aztlas."
    )

    df_itens = carregar_dados_itens()

    if df_itens.empty:
        st.warning("Nenhum item encontrado no banco de dados.")
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

        def processar_exibicao_preco(row):
            preco_raw = row["Preço"]

            try:
                if pd.isnull(preco_raw) or preco_raw is None:
                    return "Inestimável", ""
                preco_original = float(preco_raw)
            except (ValueError, TypeError):
                return "Inestimável", ""

            if preco_original == 0:
                return "Grátis / Inestimável", ""

            if not st.session_state.modo_mestre:
                return f"₽ {preco_original:,.2f}", ""

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
                    titulo_expander = (
                        f"📦 **{item['Nome']}** — *{item['Tipo']}* | 💰 **{preco_txt}**"
                        f" ({status_preco})"
                    )
                else:
                    titulo_expander = (
                        f"📦 **{item['Nome']}** — *{item['Tipo']}* | 💰 **{preco_txt}**"
                    )

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
# ABA 4: ESCUDO DO MESTRE
# ==============================================================================
if st.session_state.modo_mestre:
    with abas[3]:
        st.title("🧙‍♂️ Escudo do Mestre")
        st.markdown("Painel de gerenciamento do ecossistema e economia de Aztlas.")

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
                    st.session_state.modificadores_preco = gerar_flutuacao_automatica(
                        categorias_existentes
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
                    "Nenhuma flutuação gerada ainda hoje. Clique em 'Girar Mercado'"
                    " para simular."
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
            st.subheader("📜 Regras Rápidas & Tabelas de Apoio")

            caminho_regras = os.path.join(
                os.path.dirname(__file__), "regras_mestre.md"
            )

            if os.path.exists(caminho_regras):
                with open(caminho_regras, "r", encoding="utf-8") as f:
                    conteudo_regras = f.read()

                st.markdown(conteudo_regras)
            else:
                st.info(
                    "📄 O arquivo `regras_mestre.md` não foi encontrado na pasta do"
                    " projeto."
                )
                st.caption(
                    "Crie o arquivo `regras_mestre.md` na mesma pasta do `app.py` para"
                    " exibir suas regras e tabelas aqui."
                )
