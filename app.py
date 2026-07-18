import streamlit as st
import sqlite3
import pandas as pd
import os

# Configuração da página - Mantendo o modo Wide para caber o mapa e as tabelas
st.set_page_config(
    page_title="Aztlas Compendium",
    page_icon="🌵",
    layout="wide"
)

# Estilização CSS para imitar o esquema de cores limpo e moderno do PokémonDB e do 5e
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    h1, h2, h3 { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #2d3748; }
    .stDataFrame { border: 1px solid #e2e8f0; border-radius: 8px; }
    .pokecard {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# Função para carregar os dados tratando caminhos e nomes de tabelas
def carregar_dados_pokemon_db(db_path):
    try:
        diretorio_atual = os.path.dirname(os.path.abspath(__file__))
        caminho_absoluto = os.path.join(diretorio_atual, db_path)
        
        if not os.path.exists(caminho_absoluto):
            st.error("❌ **Arquivo de Banco de Dados não encontrado!**")
            st.info(f"O seu arquivo `{db_path}` PRECISA estar dentro da pasta:\n`{diretorio_atual}`")
            return None, None, None
            
        conn = sqlite3.connect(caminho_absoluto)
        
        try:
            df_poke = pd.read_sql_query("SELECT * FROM pokemon", conn)
        except Exception:
            try:
                df_poke = pd.read_sql_query("SELECT * FROM Pokemon", conn)
            except Exception as e:
                st.error(f"Erro crítico: A tabela 'pokemon' não existe. Detalhes: {e}")
                conn.close()
                return None, None, None
            
        if "Habildade 2" in df_poke.columns:
            df_poke = df_poke.rename(columns={"Habildade 2": "Habilidade 2"})
            
        df_desc = None
        try: 
            df_desc = pd.read_sql_query("SELECT * FROM descricao_pokedexrpg", conn)
        except Exception: 
            pass
        
        df_status = None
        try: 
            df_status = pd.read_sql_query('SELECT * FROM "Base Stats"', conn)
        except Exception: 
            pass

        conn.close()
        return df_poke, df_desc, df_status
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None, None, None

# Título da aplicação
st.title("🎯 Aztlas Compendium")
st.markdown("---")

# Seleção do Banco de Dados na barra lateral
st.sidebar.header("System Settings")
db_opcao = st.sidebar.selectbox(
    "Database Version:",
    ["Aztlas Nativa (pokedex aztlas.db)", "Pokédex Final (pokedex aztlas - Copia.db)"]
)
nome_arquivo_db = "pokedex aztlas.db" if "Nativa" in db_opcao else "pokedex aztlas - Copia.db"

df_pokemon, df_descricoes, df_status_base = carregar_dados_pokemon_db(nome_arquivo_db)

if df_pokemon is not None:
    
    # Criando as Três Abas Principais do Sistema no topo
    aba_principal_pokedex, aba_principal_itens, aba_principal_mapa = st.tabs([
        "📊 Pokédex & Moves", 
        "🎒 Items Compendium", 
        "🗺️ World Map (Beta)"
    ])
    
    # =========================================================================
    # --- ABA 1: POKÉDEX & MOVES ---
    # =========================================================================
    with aba_principal_pokedex:
        st.sidebar.subheader("Pokedex Filters")
        busca_nome = st.sidebar.text_input("🔍 Search name:")
        
        todos_tipos = sorted(list(set(df_pokemon["Tipo 1"].dropna().unique()) | set(df_pokemon["Tipo 2"].dropna().unique()))) if "Tipo 1" in df_pokemon.columns else []
        tipo_selecionado = st.sidebar.selectbox("Filter by Type:", ["All"] + todos_tipos)

        df_filtrado = df_pokemon.copy()
        if busca_nome:
            df_filtrado = df_filtrado[df_filtrado["Nome"].str.contains(busca_nome, case=False, na=False)]
        if tipo_selecionado != "All":
            df_filtrado = df_filtrado[(df_filtrado["Tipo 1"] == tipo_selecionado) | (df_filtrado["Tipo 2"] == tipo_selecionado)]

        col_lista, col_detalhes = st.columns([1.2, 1.8])

        with col_lista:
            st.markdown(f"#### Pokémon List ({len(df_filtrado)})")
            colunas_exibir = [col for col in ["ID", "Nome", "Tipo 1", "Tipo 2"] if col in df_filtrado.columns]
            st.dataframe(df_filtrado[colunas_exibir], use_container_width=True, hide_index=True)

        with col_detalhes:
            if not df_filtrado.empty and "Nome" in df_filtrado.columns:
                pokemon_escolhido = st.selectbox("Select a Pokémon to view data:", df_filtrado["Nome"].unique())
                poke_dados = df_filtrado[df_filtrado["Nome"] == pokemon_escolhido].iloc[0]
                
                st.markdown(f"## {poke_dados['Nome']} <span style='color: #a0aec0; font-size: 20px;'>#0{poke_dados.get('Dex No.', poke_dados['ID'])}</span>", unsafe_allow_html=True)
                
                aba_dados, aba_movimentos = st.tabs(["Pokédex data", "Training & Moves"])
                
                with aba_dados:
                    col_sprite, col_tabela = st.columns([1, 1.5])
                    
                    with col_sprite:
                        caminho_sprite = f"sprites/{poke_dados['ID']}.png"
                        if os.path.exists(caminho_sprite):
                            st.image(caminho_sprite, use_container_width=True)
                        else:
                            st.info("No sprite available")
                    
                    with col_tabela:
                        st.markdown("#### Pokédex Data")
                        t1 = poke_dados.get('Tipo 1', 'Desconhecido')
                        t2 = f" / {poke_dados['Tipo 2']}" if pd.notna(poke_dados.get('Tipo 2')) and poke_dados['Tipo 2'] else ""
                        
                        lista_habs = []
                        if pd.notna(poke_dados.get('Habilidade 1')) and str(poke_dados['Habilidade 1']).strip() not in ["", "-"]:
                            lista_habs.append(f"1. {poke_dados['Habilidade 1']}")
                        if pd.notna(poke_dados.get('Habilidade 2')) and str(poke_dados['Habilidade 2']).strip() not in ["", "-"]:
                            lista_habs.append(f"2. {poke_dados['Habilidade 2']}")
                        if pd.notna(poke_dados.get('Habilidade E')) and str(poke_dados['Habilidade E']).strip() not in ["", "-"]:
                            lista_habs.append(f"<span style='color:#718096; font-size:12px;'><em>Hidden: {poke_dados['Habilidade E']}</em></span>")

                        habs_final = "<br>".join(lista_habs) if lista_habs else "—"

                        tabela_html = f"""
                        <table style="width:100%; border-collapse: collapse;">
                            <tr style="border-bottom: 1px solid #edf2f7; padding: 8px 0;"><td style="font-weight: bold; color: #718096; width: 35%;">National No.</td><td><strong>{poke_dados.get('Dex No.', poke_dados['ID'])}</strong></td></tr>
                            <tr style="border-bottom: 1px solid #edf2f7; padding: 8px 0;"><td style="font-weight: bold; color: #718096;">Type</td><td><span style="color: #2d3748; font-weight: bold;">{t1}{t2}</span></td></tr>
                            <tr style="border-bottom: 1px solid #edf2f7; padding: 8px 0;"><td style="font-weight: bold; color: #718096;">Height</td><td>{poke_dados.get('Altura', '—')} m</td></tr>
                            <tr style="border-bottom: 1px solid #edf2f7; padding: 8px 0;"><td style="font-weight: bold; color: #718096;">Weight</td><td>{poke_dados.get('Peso', '—')} kg</td></tr>
                            <tr style="border-bottom: 1px solid #edf2f7; padding: 8px 0;"><td style="font-weight: bold; color: #718096;">Abilities</td><td>{habs_final}</td></tr>
                        </table>
                        """
                        st.markdown(tabela_html, unsafe_allow_html=True)

                    st.markdown("---")
                    st.markdown("#### Base Stats")
                    hp, atk, deffen, sp_atk, sp_def, spe = 60, 60, 60, 60, 60, 60
                    
                    if df_status_base is not None and not df_status_base.empty:
                        status_poke = df_status_base[df_status_base["ID"] == poke_dados["ID"]]
                        if not status_poke.empty:
                            hp = status_poke.iloc[0].get('HP', hp)
                            atk = status_poke.iloc[0].get('Atk', atk)
                            deffen = status_poke.iloc[0].get('Def', deffen)
                            sp_atk = status_poke.iloc[0].get('Sp. Atk', sp_atk)
                            sp_def = status_poke.iloc[0].get('Sp. Def', sp_def)
                            spe = status_poke.iloc[0].get('Spe', spe)

                    def converter_status(valor, padrao=60):
                        try:
                            if pd.isna(valor) or str(valor).strip() == "":
                                return padrao
                            return int(float(valor))
                        except (ValueError, TypeError):
                            return padrao

                    hp_num = converter_status(hp)
                    atk_num = converter_status(atk)
                    def_num = converter_status(deffen)
                    sp_atk_num = converter_status(sp_atk)
                    sp_def_num = converter_status(sp_def)
                    spe_num = converter_status(spe)

                    st.progress(min(hp_num / 150, 1.0), text=f"HP: {hp_num}")
                    st.progress(min(atk_num / 150, 1.0), text=f"Attack: {atk_num}")
                    st.progress(min(def_num / 150, 1.0), text=f"Defense: {def_num}")
                    st.progress(min(sp_atk_num / 150, 1.0), text=f"Sp. Atk: {sp_atk_num}")
                    st.progress(min(sp_def_num / 150, 1.0), text=f"Sp. Def: {sp_def_num}")
                    st.progress(min(spe_num / 150, 1.0), text=f"Speed: {spe_num}")
                    
                    st.markdown("---")
                    st.markdown("#### Pokédex Entries")
                    texto_lore = "No entry available for this Pokémon yet."
                    
                    if df_descricoes is not None:
                        linha_desc = df_descricoes[df_descricoes["ID"] == poke_dados["ID"]]
                        if linha_desc.empty and "Nome" in df_descricoes.columns:
                            linha_desc = df_descricoes[df_descricoes["Nome"] == poke_dados["Nome"]]
                            
                        if not linha_desc.empty:
                            if "Descrição" in linha_desc.columns:
                                texto_lore = linha_desc.iloc[0]["Descrição"]
                            elif "DescriÃ§Ã£o" in linha_desc.columns:
                                texto_lore = linha_desc.iloc[0]["DescriÃ§Ã£o"]
                                
                    st.markdown(f"""
                    <div style='
                        background-color: #2d3748; 
                        color: #ffffff; 
                        padding: 18px; 
                        border-left: 4px solid #3182ce; 
                        border-radius: 6px; 
                        font-style: italic;
                        line-height: 1.5;
                    '>
                        "{texto_lore}"
                    </div>
                    """, unsafe_allow_html=True)

                with aba_movimentos:
                    st.markdown("#### Move Pool & Game Mechanics")
                    sub_lv, sub_tm, sub_ovo, sub_prof = st.tabs(["Level Up", "TMs", "Egg Moves", "Professor"])
                    
                    try:
                        diretorio_atual = os.path.dirname(os.path.abspath(__file__))
                        caminho_absoluto = os.path.join(diretorio_atual, nome_arquivo_db)
                        conn = sqlite3.connect(caminho_absoluto)
                        
                        with sub_lv:
                            df_lv = pd.read_sql_query(f"SELECT Nome_Move, Level_Requisito FROM moves_level WHERE ID_Pokemon = {poke_dados['ID']} ORDER BY Level_Requisito", conn)
                            st.dataframe(df_lv, use_container_width=True, hide_index=True)
                            
                        with sub_tm:
                            query_tm = f"""
                                SELECT t.Nome_Move, i.Nome_Item 
                                FROM moves_tm t
                                LEFT JOIN itens i ON t.ID_Item = i.ID_Item
                                WHERE t.ID_Pokemon = {poke_dados['ID']}
                            """
                            df_tm = pd.read_sql_query(query_tm, conn)
                            st.dataframe(df_tm, use_container_width=True, hide_index=True)
                            
                        with sub_ovo:
                            df_ovo = pd.read_sql_query(f"SELECT Nome_Move FROM moves_egg WHERE ID_Pokemon = {poke_dados['ID']}", conn)
                            st.dataframe(df_ovo, use_container_width=True, hide_index=True)
                            
                        with sub_prof:
                            df_prof = pd.read_sql_query(f"SELECT Nome_Move FROM moves_tutor WHERE ID_Pokemon = {poke_dados['ID']}", conn)
                            st.dataframe(df_prof, use_container_width=True, hide_index=True)
                            
                        conn.close()
                    except Exception as e:
                        st.info("Aba de movimentos estruturada. Aguardando a criação/vinculação das tabelas de golpes no SQLite.")

            else:
                st.warning("No Pokémon matched the filters.")

    # =========================================================================
    # --- ABA 2: COMPÊNDIO DE ITENS (GALAR STYLE) ---
    # =========================================================================
    with aba_principal_itens:
        st.markdown("### 🎒 Item Compendium — Galar Style")
        
        try:
            diretorio_atual = os.path.dirname(os.path.abspath(__file__))
            caminho_absoluto = os.path.join(diretorio_atual, nome_arquivo_db)
            conn = sqlite3.connect(caminho_absoluto)
            df_itens = pd.read_sql_query("SELECT * FROM itens", conn)
            conn.close()
            
            if not df_itens.empty:
                col_busca_item, col_filtro_cat = st.columns([2, 1])
                with col_busca_item:
                    busca_item = st.text_input("🔍 Search item by name...", key="busca_item_galar")
                with col_filtro_cat:
                    categorias_disponiveis = ["All"] + sorted(df_itens["Categoria"].dropna().unique().tolist()) if "Categoria" in df_itens.columns else ["All"]
                    cat_selecionada = st.selectbox("Category:", categorias_disponiveis)
                
                df_itens_filtrado = df_itens.copy()
                if busca_item:
                    df_itens_filtrado = df_itens_filtrado[df_itens_filtrado["Nome_Item"].str.contains(busca_item, case=False, na=False)]
                if cat_selecionada != "All" and "Categoria" in df_itens.columns:
                    df_itens_filtrado = df_itens_filtrado[df_itens_filtrado["Categoria"] == cat_selecionada]

                st.markdown(f"**Showing {len(df_itens_filtrado)} items**")
                st.markdown("---")

                for index, item in df_itens_filtrado.iterrows():
                    nome = item.get("Nome_Item", "Unknown Item")
                    categoria = item.get("Categoria", "General")
                    descricao = item.get("Descricao", item.get("Descrição", "No description available."))
                    custo = item.get("Custo", item.get("Preco", item.get("Preço", "—")))
                    peso = item.get("Peso", "—")
                    
                    cor_badge = "#3182ce" if "TM" in categoria or "TR" in categoria else "#e53e3e" if "Ball" in categoria else "#319795"
                    
                    item_html = f"""
                    <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 18px; font-weight: bold; color: #2d3748;">📦 {nome}</span>
                            <span style="background-color: {cor_badge}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">{categoria}</span>
                        </div>
                        <p style="color: #4a5568; font-size: 14px; margin: 5px 0;">{descricao}</p>
                        <div style="font-size: 12px; color: #718096; margin-top: 8px; display: flex; gap: 15px;">
                            <span><strong>Cost:</strong> {custo} ₽</span>
                            <span><strong>Weight:</strong> {peso} lbs</span>
                        </div>
                    </div>
                    """
                    st.markdown(item_html, unsafe_allow_html=True)
            else:
                st.info("A tabela 'itens' foi encontrada, mas está vazia no momento.")
        except Exception as e:
            st.info("Aba Galar Itens configurada. Crie a tabela 'itens' no seu SQLite para listar os dados automaticamente.")

   # --- ABA 3: SEÇÃO MAPA INTERATIVO (CORREÇÃO DE LAYOUT) ---
    with aba_principal_mapa:
        st.markdown("### 🗺️ Aztlas Tactical Visor — Quadrant Zoom Navigation")
        st.markdown("---")
        
        from streamlit_image_coordinates import streamlit_image_coordinates

        # CRIANDO UMA LINHA DE CONTROLE ACIMA DO MAPA (EM VEZ DA BARRA LATERAL)
        col_lente, col_status = st.columns([1.5, 1.5])
        
        with col_lente:
            # Textos mais curtos e diretos para não estourarem a tela de jeito nenhum
            nivel_zoom = st.selectbox(
                "Select Map Lens / Zoom:", 
                [
                    "🔍 Global (Full)", 
                    "🌓 Half Left", 
                    "🌗 Half Right",
                    "🧩 Quarter NW", 
                    "🧩 Quarter NE", 
                    "🧩 Quarter SW", 
                    "🧩 Quarter SE"
                ]
            )

        # 2. Configuração dinâmica de arquivos e coordenadas por Quadrante
        if "Global" in nivel_zoom:
            caminho_mapa = "mapas/MApa Aztlas (1).png"
            largura_visor = 700
            locais_mapa = {
                "Nova Likiln do Norte": {"tipo": "cidade", "regiao": "Oeste", "box": [79, 85, 210, 215]},
                "Nova Likiln": {"tipo": "cidade", "regiao": "Sudoeste", "box": [39, 49, 279, 285]},
                "Aronos": {"tipo": "cidade", "regiao": "Sudoeste", "box": [103, 109, 270, 277]},
                "Pragmeadows": {"tipo": "cidade", "regiao": "Oeste", "box": [122, 129, 220, 227]},
                "Coahaven": {"tipo": "cidade", "regiao": "Sudoeste", "box": [194, 201, 255, 261]},
                "Rey Solipstown": {"tipo": "cidade", "regiao": "Sul", "box": [208, 214, 221, 227]},
                "Publia": {"tipo": "cidade", "regiao": "Oeste", "box": [117, 184, 197, 204]},
                "Huaztec": {"tipo": "cidade", "regiao": "Central", "box": [230, 237, 202, 208]},
                "Sceptos": {"tipo": "cidade", "regiao": "Centro-Oeste", "box": [224, 230, 143, 149]},
                "Ialiscove": {"tipo": "cidade", "regiao": "Oeste", "box": [156, 163, 147, 155]},
                "Veracruzora": {"tipo": "cidade", "regiao": "Centro-Oeste", "box": [251, 256, 109, 116]},
                "Yucasula": {"tipo": "cidade", "regiao": "Central", "box": [332, 341, 160, 169]},
                "Buccanopy": {"tipo": "cidade", "regiao": "Centro-Norte", "box": [384, 392, 76, 84]},
                "Rishore": {"tipo": "cidade", "regiao": "Norte", "box": [413, 422, 15, 24]},
                "Ampána": {"tipo": "cidade", "regiao": "Norte", "box": [479, 486, 4, 10]},
                "Fortress": {"tipo": "cidade", "regiao": "Centro-Sudeste", "box": [459, 466, 175, 183]},
                "Sunset Port": {"tipo": "cidade", "regiao": "Sudeste", "box": [440, 447, 221, 228]}
            }
            
        elif "Half Left" in nivel_zoom:
            caminho_mapa = "mapas/MApa Aztlas (2) - Half Left.png"
            largura_visor = 650
            # ... mantém o resto das coordenadas igual ao código anterior ...
            locais_mapa = {
                "Nova Likiln do Norte": {"tipo": "cidade", "regiao": "Costa Oeste", "box": [80, 200, 600, 800]},
                "Aronos": {"tipo": "cidade", "regiao": "Costa Oeste", "box": [230, 350, 620, 810]},
                "Rota 1": {"tipo": "rota", "regiao": "Costa Oeste", "box": [140, 240, 400, 550]}
            }
            
        elif "Half Right" in nivel_zoom:
            caminho_mapa = "mapas/MApa Aztlas (2) - Half Right.png"
            largura_visor = 650
            locais_mapa = {
                "Sunset Port": {"tipo": "cidade", "regiao": "Ilhas", "box": [200, 320, 400, 550]}
            }
            
        elif "Quarter NW" in nivel_zoom:
            caminho_mapa = "mapas/MApa Aztlas (3) - Quarter NW.png"
            largura_visor = 600
            locais_mapa = {
                "Veracruzora": {"tipo": "cidade", "regiao": "Norte", "box": [150, 280, 150, 300]}
            }
            
        elif "Quarter NE" in nivel_zoom:
            caminho_mapa = "mapas/MApa Aztlas (3) - Quarter NE.png"
            largura_visor = 600
            locais_mapa = {
                "Yucasula": {"tipo": "cidade", "regiao": "Norte", "box": [100, 250, 200, 350]}
            }
            
        elif "Quarter SW" in nivel_zoom:
            caminho_mapa = "mapas/MApa Aztlas (3) - Quarter SW.png"
            largura_visor = 600
            locais_mapa = {
                "Coahaven": {"tipo": "cidade", "regiao": "Sul", "box": [100, 250, 400, 600]}
            }
            
        else: # Quarter SE
            caminho_mapa = "mapas/MApa Aztlas (3) - Quarter SE.png"
            largura_visor = 600
            locais_mapa = {
                "Huaztec": {"tipo": "cidade", "regiao": "Sul", "box": [200, 350, 300, 500]}
            }

        # Estado do destino selecionado
        if "destino_selecionado" not in st.session_state:
            st.session_state.destino_selecionado = "Publia"

       # Organização visual das colunas (Mapa na Esquerda, Detalhes na Direita)
        col_visor_mapa, col_display_info = st.columns([2.2, 0.8])

        # --- COLUNA 1: VISOR CLICÁVEL ---
        with col_visor_mapa:
            st.markdown(f"#### 📺 Active Radar Frame: `{nivel_zoom}`")
            
            # Fallback de segurança: se a imagem do quadrante não existir, usa a global
            if not os.path.exists(caminho_mapa):
                caminho_mapa = "mapas/MApa Aztlas (1).jpg"
            
            if os.path.exists(caminho_mapa):
                # Executa o componente de captura de coordenadas
                value = streamlit_image_coordinates(caminho_mapa, width=largura_visor, key=f"mapa_click_{nivel_zoom}")
                
                if value is not None:
                    click_x = value["x"]
                    click_y = value["y"]
                    
                    # --- FERRAMENTA DE CALIBRAÇÃO (GERADOR DE BOX AUTOMÁTICO) ---
                    st.info("🛠️ **Dev Mode - Map Calibrator**")
                    margem = 20  # Tamanho da área do clique ao redor do ponto
                    x_min, x_max = click_x - margem, click_x + margem
                    y_min, y_max = click_y - margem, click_y + margem
                    
                    texto_pronto = f'"{st.session_state.destino_selecionado}": {{"tipo": "cidade", "regiao": "Aztlas", "box": [{x_min}, {x_max}, {y_min}, {y_max}]}},'
                    st.code(texto_pronto, language="python")
                    st.markdown(f"📍 Clique detectado em: X=`{click_x}` | Y=`{click_y}`")
                    # ------------------------------------------------------------
                    
                    # Lógica para identificar se o clique acertou alguma caixa cadastrada
                    local_encontrado = None
                    for nome_local, dados in locais_mapa.items():
                        b = dados["box"]
                        if b[0] <= click_x <= b[1] and b[2] <= click_y <= b[3]:
                            local_encontrado = nome_local
                            break
                    
                    if local_encontrado and local_encontrado != st.session_state.destino_selecionado:
                        st.session_state.destino_selecionado = local_encontrado
                        st.rerun()
            else:
                st.error("🖼️ Nenhuma imagem encontrada na pasta `mapas/`. Verifique o nome dos arquivos.")

        # --- COLUNA 2: DISPLAY DE ENCONTROS E LORE ---
        with col_display_info:
            destino_atual = st.session_state.destino_selecionado
            dados_locais = locais_mapa.get(destino_atual, {"tipo": "cidade", "regiao": "Aztlas"})
            
            st.markdown(f"### 🛬 Scanner: {destino_atual}")
            st.caption(f"CLASSIFICAÇÃO: {dados_locais.get('tipo', 'cidade').upper()}")
            
            piadas_fly = {
                "Nova Likiln": "O vento aqui é tão forte que seu Pokémon voador ia acabar fazendo drift no ar.",
                "Publia": "Pouso autorizado bem no meio da praça central. Cuidado com as barracas de frutas!",
                "Sunset Port": "Seu Pokémon se recusa a decolar daqui porque prefere ficar assistindo ao pôr do sol na praia."
            }
            
            mensagem_lore = piadas_fly.get(destino_atual, "Área escaneada com sucesso pelos sensores de voo.")
            st.markdown(f"""
            <div style="background-color: #e2e8f0; padding: 12px; border-left: 4px solid #3182ce; border-radius: 4px; margin-bottom: 20px; color: #2d3748; font-size: 13px;">
                <strong>💡 Pilot Note:</strong> <em>"{mensagem_lore}"</em>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### 🐾 Wild Encounters Radar")
            
            try:
                diretorio_atual = os.path.dirname(os.path.abspath(__file__))
                caminho_absoluto = os.path.join(diretorio_atual, nome_arquivo_db)
                conn = sqlite3.connect(caminho_absoluto)
                
                query_busca = f"""
                    SELECT p.Nome, l.Chance, l.Level_Min, l.Level_Max 
                    FROM locations l
                    JOIN pokemon p ON l.ID_Pokemon = p.ID
                    WHERE l.Nome_Local = '{destino_atual}'
                """
                df_encontros_locais = pd.read_sql_query(query_busca, conn)
                conn.close()
                
                if not df_encontros_locais.empty:
                    for _, row in df_encontros_locais.iterrows():
                        st.markdown(f"""
                        <div style="background-color: #2d3748; color: #ffffff; padding: 10px 15px; border-radius: 6px; margin-bottom: 6px; border-left: 4px solid #319795;">
                            <div style="display: flex; justify-content: space-between;">
                                <strong style="color: #ffffff;">{row['Nome']}</strong>
                                <span style="color: #cbd5e0; font-size: 12px;">{row['Chance']}</span>
                            </div>
                            <span style="font-size: 11px; color: #a0aec0;">Levels: {row['Level_Min']} - {row['Level_Max']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning(f"Nenhum monstrinho selvagem registrado em '{destino_atual}'.")
            except Exception:
                st.info("ℹ️ Banco de dados em modo simulado:")
                st.markdown(f"""
                <div style="background-color: #2d3748; color: #ffffff; padding: 10px 15px; border-radius: 6px; margin-bottom: 6px; border-left: 4px solid #f6ad55;">
                    <div style="display: flex; justify-content: space-between;">
                        <strong style="color: #ffffff;">Pidgey</strong>
                        <span style="color: #cbd5e0; font-size: 12px;">Common (60%)</span>
                    </div>
                    <span style="font-size: 11px; color: #a0aec0;">Levels: 3 - 7</span>
                </div>
                """, unsafe_allow_html=True)