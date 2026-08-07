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
# 1. FUNÇÕES DE BANCO DE DADOS (COM CACHE)
# -----------------------------------------------------------------------------
def obter_caminho_banco():
    caminho_atual = os.path.dirname(__file__)
    return os.path.join(caminho_atual, "pokedex aztlas - Copia.db")


@st.cache_data(ttl=3600)
def carregar_dados_pokemon():
    caminho_banco = obter_caminho_banco()
    if not os.path.exists(caminho_banco):
        return pd.DataFrame()

    with sqlite3.connect(caminho_banco) as conn:
        query = "SELECT `ID`, `Dex No.`, `Nome`, `Tipo 1`, `Tipo 2`, `Tamanho`, `SR` FROM pokemon"
        df = pd.read_sql_query(query, conn)
    return df


def buscar_detalhes_completos(pokemon_id):
    caminho_banco = obter_caminho_banco()
    with sqlite3.connect(caminho_banco) as conn:
        cursor = conn.cursor()

        # 1. Dados Gerais
        cursor.execute('SELECT * FROM pokemon WHERE "ID" = ?', (pokemon_id,))
        gerais = cursor.fetchone()

        # 2. Descrição
        try:
            cursor.execute('SELECT "Espécie", "Descrição" FROM descricao_pokedexrpg WHERE "ID" = ?', (pokemon_id,))
            descricao = cursor.fetchone()
        except Exception:
            descricao = ("Sem espécie", "Sem descrição disponível.")

        if not descricao:
            descricao = ("Sem espécie", "Sem descrição disponível.")

        # 3. Base Stats
        cursor.execute('SELECT * FROM "Base Stats" WHERE "id_pokemon" = ?', (pokemon_id,))
        stats = cursor.fetchone()
        if not stats:
            cursor.execute('SELECT * FROM "Base Stats" WHERE "ID" = ?', (pokemon_id,))
            stats = cursor.fetchone()

        # 4. Breeding & Training
        cursor.execute('SELECT * FROM "Training_Breeding" WHERE "ID" = ?', (pokemon_id,))
        breeding = cursor.fetchone()

        # 5. Moves (Divididos por método/origem)
        try:
            query_moves = """
                SELECT *
                FROM "pokemon_moves" 
                WHERE "pokemon_id" = ?
            """
            moves_df = pd.read_sql_query(query_moves, conn, params=(pokemon_id,))
        except Exception:
            moves_df = pd.DataFrame()

        # 6. Evoluções
        try:
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
            evo_df = pd.read_sql_query(query_evo, conn, params=(pokemon_id, pokemon_id, pokemon_id))
            evo_df = evo_df.fillna("-") if not evo_df.empty else pd.DataFrame()
        except Exception:
            evo_df = pd.DataFrame()

        # 7. Localização / Spawns
        loc_df = pd.DataFrame()
        tabelas_possiveis = ["Locations_Pok mon", "Locations_Pokémon", "Locations_Pok_mon", "location_pokemon"]
        
        for nome_tabela in tabelas_possiveis:
            try:
                query_loc = f"""
                    SELECT l.Location AS [Local], lp.spawn_method AS [Método], lp.chance_rate AS [Chance],
                           lp.min_level AS [Nível Mín], lp.max_level AS [Nível Máx], lp.time_of_day AS [Horário]
                    FROM "{nome_tabela}" lp
                    JOIN Locations l ON lp.location_id = l.ID
                    WHERE lp.pokemon_id = ?
                """
                loc_df = pd.read_sql_query(query_loc, conn, params=(pokemon_id,))
                break
            except Exception:
                continue

    return gerais, descricao, stats, breeding, moves_df, evo_df, loc_df


@st.cache_data(ttl=3600)
def carregar_dados_itens():
    caminho_banco = obter_caminho_banco()
    if not os.path.exists(caminho_banco):
        return pd.DataFrame()

    with sqlite3.connect(caminho_banco) as conn:
        try:
            query = 'SELECT `ID`, `Tipo`, `Nome`, `Efeito`, `Descrição`, `Preço` FROM "Itens"'
            df_itens = pd.read_sql_query(query, conn)
            df_itens["Preço"] = pd.to_numeric(df_itens["Preço"], errors="coerce")
            return df_itens
        except Exception:
            return pd.DataFrame()


@st.cache_data(ttl=3600)
def carregar_dados_habilidades():
    caminho_banco = obter_caminho_banco()
    if not os.path.exists(caminho_banco):
        return pd.DataFrame()

    with sqlite3.connect(caminho_banco) as conn:
        try:
            return pd.read_sql_query('SELECT * FROM "Habilidades"', conn)
        except Exception:
            try:
                return pd.read_sql_query('SELECT * FROM "abilities"', conn)
            except Exception:
                return pd.DataFrame()


@st.cache_data(ttl=3600)
def carregar_dados_golpes_gerais():
    caminho_banco = obter_caminho_banco()
    if not os.path.exists(caminho_banco):
        return pd.DataFrame()

    with sqlite3.connect(caminho_banco) as conn:
        try:
            return pd.read_sql_query('SELECT * FROM "Golpes"', conn)
        except Exception:
            try:
                return pd.read_sql_query('SELECT * FROM "moves"', conn)
            except Exception:
                return pd.DataFrame()


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
        if variacao == 1.0:
            variacao = 1.10
        novos_modificadores[cat] = variacao
    return novos_modificadores


# -----------------------------------------------------------------------------
# 3. BARRA LATERAL
# -----------------------------------------------------------------------------
st.sidebar.title("Pocket & Monsters RPG")
st.sidebar.markdown("---")
st.sidebar.subheader("Painel de Acesso")

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
# 4. ESTRUTURA DE ABAS PRINCIPAIS
# -----------------------------------------------------------------------------
abas_disponiveis = [
    "🐾 Pokédex Regional", 
    "⚔️ Compêndio de Golpes", 
    "✨ Habilidades", 
    "🎒 Compêndio de Itens"
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

        tipos_1 = set(df_pokemon["Tipo 1"].dropna().unique())
        tipos_2 = set(df_pokemon["Tipo 2"].dropna().unique())
        tipos_disponiveis = sorted(list(tipos_1 | tipos_2))

        filtro_tipo = st.sidebar.selectbox("Filtrar por Tipo:", ["Todos"] + tipos_disponiveis)
        coluna_ordenar = st.sidebar.selectbox("Ordenar Pokémon por:", options=df_pokemon.columns.tolist(), index=2)
        ordem_crescente = st.sidebar.radio("Ordem Pokémon:", ["Crescente", "Decrescente"])
        ascendente = ordem_crescente == "Crescente"

        df_filtrado = df_pokemon.copy()

        if filtro_nome:
            df_filtrado = df_filtrado[df_filtrado["Nome"].str.contains(filtro_nome, case=False, na=False)]

        if filtro_tipo != "Todos":
            df_filtrado = df_filtrado[(df_filtrado["Tipo 1"] == filtro_tipo) | (df_filtrado["Tipo 2"] == filtro_tipo)]

        df_filtrado = df_filtrado.sort_values(by=coluna_ordenar, ascending=ascendente)

        if st.session_state.id_pokemon_selecionado is not None:
            if st.button("⬅ Voltar para a Lista"):
                st.session_state.id_pokemon_selecionado = None
                st.rerun()

            (poke_geral, poke_desc, poke_stats, poke_breed, poke_moves, poke_evo, poke_loc) = buscar_detalhes_completos(
                int(st.session_state.id_pokemon_selecionado)
            )

            if poke_geral:
                nome_poke = poke_geral[2] if len(poke_geral) > 2 else "Pokémon"
                dex_poke = f"#{poke_geral[1]}" if len(poke_geral) > 1 and poke_geral[1] else ""
                st.title(f"{nome_poke} {dex_poke}")

                aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
                    "📋 Dados Gerais", "📊 Atributos & Stats RPG", "🧬 Evoluções", 
                    "🗺️ Localização & Spawn", "🥚 Breeding & Training", "⚔️ Golpes / Learnsets"
                ])

                with aba1:
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        github_base_url = "https://raw.githubusercontent.com/Foguender/Aztlas_Heart_-Pok-monRPG-/main/sprites"
                        pokemon_id = poke_geral[0]
                        st.image(f"{github_base_url}/{pokemon_id}.png", caption=nome_poke, use_container_width=True)
                    with col2:
                        st.subheader("Informações Biológicas")
                        if poke_desc:
                            st.markdown(f"**Espécie:** {poke_desc[0] if len(poke_desc) > 0 else 'N/A'}")
                            st.markdown(f"*\"{poke_desc[1] if len(poke_desc) > 1 else ''}\"*")

                        st.write("---")
                        tipo1 = poke_geral[3] if len(poke_geral) > 3 else "Desconhecido"
                        tipo2 = poke_geral[4] if len(poke_geral) > 4 and poke_geral[4] else "Nenhum"
                        st.markdown(f"**Tipo 1:** {tipo1} | **Tipo 2:** {tipo2}")

                        tamanho_val = poke_geral[5] if len(poke_geral) > 5 and poke_geral[5] else "N/A"
                        sr_val = poke_geral[6] if len(poke_geral) > 6 and poke_geral[6] is not None else "N/A"
                        st.markdown(f"📏 **Tamanho:** {tamanho_val} | 🎯 **SR:** {sr_val}")

                with aba2:
                    st.subheader("Atributos de RPG (Sistema D20)")
                    if poke_stats:
                        col_s1, col_s2, col_s3 = st.columns(3)
                        with col_s1:
                            st.metric("HP", poke_stats[2] if len(poke_stats) > 2 else "N/A")
                            st.metric("FOR", poke_stats[3] if len(poke_stats) > 3 else "N/A")
                            st.metric("DES", poke_stats[4] if len(poke_stats) > 4 else "N/A")
                        with col_s2:
                            st.metric("CON", poke_stats[5] if len(poke_stats) > 5 else "N/A")
                            st.metric("INT", poke_stats[6] if len(poke_stats) > 6 else "N/A")
                            st.metric("SAB", poke_stats[7] if len(poke_stats) > 7 else "N/A")
                        with col_s3:
                            st.metric("CAR", poke_stats[8] if len(poke_stats) > 8 else "N/A")

                with aba3:
                    st.subheader("Linhagem de Evolução")
                    if not poke_evo.empty:
                        st.dataframe(poke_evo, hide_index=True, use_container_width=True)
                    else:
                        st.info("Este Pokémon não possui linhagem de evolução cadastrada.")

                with aba4:
                    st.subheader("Locais de Aparição em Aztlas")
                    if not poke_loc.empty:
                        st.dataframe(poke_loc, hide_index=True, use_container_width=True)
                    else:
                        st.info("Nenhum local de spawn selvagem registrado.")

                with aba5:
                    st.subheader("Dados de Cruzamento e Treinamento")
                    if poke_breed:
                        st.markdown(f"**Rendimento de EV:** {poke_breed[2] if len(poke_breed) > 2 else 'N/A'}")
                        st.markdown(f"**Amizade Base:** {poke_breed[3] if len(poke_breed) > 3 else 'N/A'}")

                # ABA DE GOLPES DO POKÉMON (ESTILO POKEMONDB - 4 SUB-ABAS)
                with aba6:
                    st.subheader("Lista de Golpes (Learnsets)")
                    if not poke_moves.empty:
                        tab_level, tab_tm, tab_egg, tab_tutor = st.tabs([
                            "📈 Nível (Learnset)", 
                            "💿 TMs / HMs", 
                            "🥚 Egg Moves", 
                            "🎓 Tutor / Professor"
                        ])

                        # Identificação da coluna de método/categoria na tabela de golpes
                        col_metodo = next((c for c in ["Metodo", "método", "Method", "Categoria", "Tipo_Aprendizado"] if c in poke_moves.columns), None)

                        with tab_level:
                            if col_metodo:
                                df_lvl = poke_moves[poke_moves[col_metodo].str.contains("Level|Nível|Nivel", case=False, na=False)]
                            else:
                                df_lvl = poke_moves
                            st.dataframe(df_lvl, hide_index=True, use_container_width=True)

                        with tab_tm:
                            if col_metodo:
                                df_tm = poke_moves[poke_moves[col_metodo].str.contains("TM|HM|Disco", case=False, na=False)]
                                st.dataframe(df_tm, hide_index=True, use_container_width=True)
                            else:
                                st.info("Filtro de TM não aplicável ou sem dados registrados.")

                        with tab_egg:
                            if col_metodo:
                                df_egg = poke_moves[poke_moves[col_metodo].str.contains("Egg|Ovo", case=False, na=False)]
                                st.dataframe(df_egg, hide_index=True, use_container_width=True)
                            else:
                                st.info("Filtro de Egg Moves não aplicável ou sem dados registrados.")

                        with tab_tutor:
                            if col_metodo:
                                df_tutor = poke_moves[poke_moves[col_metodo].str.contains("Tutor|Professor", case=False, na=False)]
                                st.dataframe(df_tutor, hide_index=True, use_container_width=True)
                            else:
                                st.info("Filtro de Professor/Tutor não aplicável ou sem dados registrados.")
                    else:
                        st.info("Nenhum golpe cadastrado para este Pokémon.")

        else:
            st.title("PokéDex Completa")
            df_tabela = df_filtrado.fillna("-")
            evento_selecao = st.dataframe(
                df_tabela,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
            )

            if evento_selecao and "selection" in evento_selecao and "rows" in evento_selecao["selection"]:
                linhas = evento_selecao["selection"]["rows"]
                if len(linhas) > 0:
                    st.session_state.id_pokemon_selecionado = df_filtrado.iloc[linhas[0]]["ID"]
                    st.rerun()


# ==============================================================================
# ABA 2: COMPÊNDIO DE GOLPES (NOVA)
# ==============================================================================
with abas[1]:
    st.title("⚔️ Compêndio Geral de Golpes")
    st.markdown("Lista completa de todos os ataques e movimentos disponíveis no RPG.")

    df_golpes = carregar_dados_golpes_gerais()

    if df_golpes.empty:
        st.warning("A tabela de Golpes não foi encontrada ou está vazia.")
    else:
        filtro_golpe_nome = st.text_input("Buscar Golpe por Nome:", "")

        df_golpes_filtrados = df_golpes.copy()
        if filtro_golpe_nome:
            col_nome_golpe = next((c for c in ["Nome", "Ataque", "Name", "Move"] if c in df_golpes.columns), df_golpes.columns[0])
            df_golpes_filtrados = df_golpes_filtrados[df_golpes_filtrados[col_nome_golpe].str.contains(filtro_golpe_nome, case=False, na=False)]

        st.dataframe(df_golpes_filtrados.fillna("-"), use_container_width=True, hide_index=True)


# ==============================================================================
# ABA 3: HABILIDADES (NOVA)
# ==============================================================================
with abas[2]:
    st.title("✨ Dicionário de Habilidades (Abilities)")
    st.markdown("Consulte os efeitos passivos e habilidades especiais dos Pokémon.")

    df_hab = carregar_dados_habilidades()

    if df_hab.empty:
        st.warning("A tabela de Habilidades não foi encontrada ou está vazia.")
    else:
        filtro_hab_nome = st.text_input("Buscar Habilidade por Nome:", "")

        df_hab_filtradas = df_hab.copy()
        if filtro_hab_nome:
            col_nome_hab = next((c for c in ["Nome", "Habilidade", "Ability", "Name"] if c in df_hab.columns), df_hab.columns[0])
            df_hab_filtradas = df_hab_filtradas[df_hab_filtradas[col_nome_hab].str.contains(filtro_hab_nome, case=False, na=False)]

        st.dataframe(df_hab_filtradas.fillna("-"), use_container_width=True, hide_index=True)


# ==============================================================================
# ABA 4: COMPÊNDIO DE ITENS
# ==============================================================================
with abas[3]:
    st.title("🎒 Compêndio de Itens & Equipamentos")

    df_itens = carregar_dados_itens()

    if df_itens.empty:
        st.warning("Nenhum item encontrado no banco de dados.")
    else:
        filtro_item_nome = st.sidebar.text_input("Buscar Item por Nome:", "")
        tipos_itens = ["Todos"] + sorted(list(df_itens["Tipo"].dropna().unique()))
        filtro_item_tipo = st.sidebar.selectbox("Filtrar por Categoria/Tipo:", tipos_itens)

        df_itens_filtrados = df_itens.copy()

        if filtro_item_nome:
            df_itens_filtrados = df_itens_filtrados[df_itens_filtrados["Nome"].str.contains(filtro_item_nome, case=False, na=False)]

        if filtro_item_tipo != "Todos":
            df_itens_filtrados = df_itens_filtrados[df_itens_filtrados["Tipo"] == filtro_item_tipo]

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

            status = f"📈 +{pct}% (Alta)" if mod > 1.0 else f"📉 -{pct}% (Desconto)" if mod < 1.0 else "⚖️ Base"
            return f"₽ {preco_final:,.2f}", status

        visualizacao = st.radio("Modo de Visualização:", ["📋 Fichas Detalhadas", "📊 Tabela Geral"], horizontal=True)

        if visualizacao == "📋 Fichas Detalhadas":
            for _, item in df_itens_filtrados.iterrows():
                preco_txt, status_preco = processar_exibicao_preco(item)
                titulo_expander = f"📦 **{item['Nome']}** — *{item['Tipo']}* | 💰 **{preco_txt}**"
                with st.expander(titulo_expander):
                    st.markdown(f"**Categoria:** `{item['Tipo']}`")
                    st.markdown(f"**Preço:** {preco_txt}")
                    st.write(item["Descrição"] if item["Descrição"] else "Sem descrição.")
        else:
            df_exibicao = df_itens_filtrados.copy()
            df_exibicao["Preço"] = df_exibicao.apply(lambda r: processar_exibicao_preco(r)[0], axis=1)
            st.dataframe(df_exibicao.fillna("-"), use_container_width=True, hide_index=True)


# ==============================================================================
# ABA 5: ESCUDO DO MESTRE
# ==============================================================================
if st.session_state.modo_mestre:
    with abas[4]:
        st.title("🧙‍♂️ Escudo do Mestre")
        sub_mercado, sub_regras = st.tabs(["🎲 Algoritmo de Mercado", "📜 Regras Rápidas"])

        df_itens = carregar_dados_itens()
        categorias_existentes = sorted(list(df_itens["Tipo"].dropna().unique())) if not df_itens.empty else []

        with sub_mercado:
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🎲 Girar Mercado (Simular Novo Dia)", type="primary"):
                    st.session_state.modificadores_preco = gerar_flutuacao_automatica(categorias_existentes)
                    st.success("🎉 Mercado atualizado!")
                    st.rerun()

            with col_btn2:
                if st.button("🔄 Resetar Mercado"):
                    st.session_state.modificadores_preco = {cat: 1.0 for cat in categorias_existentes}
                    st.info("Preços restaurados ao valor base.")
                    st.rerun()

        with sub_regras:
            caminho_regras = os.path.join(os.path.dirname(__file__), "regras_mestre.md")
            if os.path.exists(caminho_regras):
                with open(caminho_regras, "r", encoding="utf-8") as f:
                    st.markdown(f.read())
            else:
                st.info("📄 Arquivo `regras_mestre.md` não encontrado.")
