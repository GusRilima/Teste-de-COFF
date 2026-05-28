# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import gdown
import os

# 1. Configuração inicial da página
st.set_page_config(page_title="Radar de Curtailment", layout="wide")

# 2. Criando o Menu de Navegação Lateral
st.sidebar.title("Navegação Comercial")

# Novo filtro de Fonte de Energia
filtro_fonte = st.sidebar.radio(
    "Selecione o Cenário:",
    [
        "Consolidado (Solar + Eólica)",
        "Apenas Eólica",
        "Apenas Solar"
    ]
)

st.sidebar.markdown("---")

tela = st.sidebar.radio(
    "Selecione a Visão:", 
    [
        "Visão Geral (Ocorrências)", 
        "Impacto em Energia (MWh)",
        "Detalhamento por Usina",
        "Ranking de Clientes Alvo" # <--- NOVA TELA ADICIONADA
    ]
)
st.sidebar.markdown("---")
st.sidebar.info("Dashboard para identificação de oportunidades em Curtailment (Eólico e Solar).")

# 3. Carregamento e Tratamento dos Dados em Cache
@st.cache_data
def load_data():
    # IDs do Google Drive
    id_eol = '1-81IsyRU-7DUmbotSe4-f2Xu_1HBWpHC'
    id_ufv = '1bNp4ziuB7H6HQLRibTQ2uLrH28IZADY-'
    
    # --- DADOS EÓLICOS ---
    arq_eol = 'base_eol_drive.csv'
    if not os.path.exists(arq_eol):
        gdown.download(f'https://drive.google.com/uc?id={id_eol}', arq_eol, quiet=False)
    
    df_eol = pd.read_csv(arq_eol, sep=';', low_memory=False)
    df_eol['Fonte'] = 'Eólica'
    # Padronizando o nome da coluna de flag para as duas fontes
    if 'flg_dadoventoinvalido' in df_eol.columns:
        df_eol['flg_restricao'] = pd.to_numeric(df_eol['flg_dadoventoinvalido'], errors='coerce')
    
    # --- DADOS SOLARES ---
    arq_ufv = 'base_ufv_drive.csv'
    if not os.path.exists(arq_ufv):
        gdown.download(f'https://drive.google.com/uc?id={id_ufv}', arq_ufv, quiet=False)
        
    df_ufv = pd.read_csv(arq_ufv, sep=';', low_memory=False)
    df_ufv['Fonte'] = 'Solar'
    # Padronizando o nome da coluna de flag para as duas fontes
    if 'flg_dadoirradianciainvalido' in df_ufv.columns:
        df_ufv['flg_restricao'] = pd.to_numeric(df_ufv['flg_dadoirradianciainvalido'], errors='coerce')
        
    # --- JUNTANDO TUDO ---
    df_completo = pd.concat([df_eol, df_ufv], ignore_index=True)
    
    # Garantindo que as colunas de cálculo são numéricas
    colunas_numericas = ['val_geracaoestimada', 'val_geracaoverificada']
    for col in colunas_numericas:
        if col in df_completo.columns:
            df_completo[col] = pd.to_numeric(df_completo[col], errors='coerce')
            
    return df_completo

df = load_data()

# Isolando eventos de Curtailment e criando a coluna de Energia Perdida
df_curtailment = df[df['flg_restricao'] == 1].copy()
df_curtailment['energia_perdida_mwh'] = df_curtailment['val_geracaoestimada'] - df_curtailment['val_geracaoverificada']

# Aplicando o filtro do Menu Lateral
if filtro_fonte == "Apenas Eólica":
    df_curtailment = df_curtailment[df_curtailment['Fonte'] == 'Eólica']
elif filtro_fonte == "Apenas Solar":
    df_curtailment = df_curtailment[df_curtailment['Fonte'] == 'Solar']


# ==========================================
# TELA 1: VISÃO GERAL (OCORRÊNCIAS)
# ==========================================
if tela == "Visão Geral (Ocorrências)":
    st.title(f"Radar Comercial: Eventos de Restrição - {filtro_fonte}")
    st.markdown("Identificação de players com o **maior volume de eventos de restrição** (quantidade de vezes que sofreram corte).")

    if not df_curtailment.empty:
        # Criando o ranking por proprietário (Frequência)
        ranking = df_curtailment.groupby('Proprietário Grupo Econômico Nome').size().reset_index(name='Ocorrencias')
        ranking = ranking.sort_values(by='Ocorrencias', ascending=False)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Ranking de Frequência de Cortes")
            fig = px.bar(
                ranking.head(20), 
                x='Ocorrencias', 
                y='Proprietário Grupo Econômico Nome', 
                orientation='h',
                color='Ocorrencias',
                color_continuous_scale='Reds',
                labels={'Ocorrencias': 'Número de Eventos', 'Proprietário Grupo Econômico Nome': 'Player'}
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Base Comercial (Eventos)")
            st.dataframe(ranking, use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado para este filtro.")


# ==========================================
# TELA 2: IMPACTO EM ENERGIA (MWh)
# ==========================================
elif tela == "Impacto em Energia (MWh)":
    st.title(f"Dor Financeira: Energia Suprimida - {filtro_fonte}")
    st.markdown("Foco no **tamanho do prejuízo (MWh)**. Quais Grupos Econômicos deixaram de gerar mais energia por causa do curtailment?")

    if not df_curtailment.empty:
        # Agrupando métricas comerciais de volume
        metricas_comerciais = df_curtailment.groupby('Proprietário Grupo Econômico Nome').agg(
            Eventos_Curtailment=('flg_restricao', 'count'),
            Energia_Suprimida_MWh=('energia_perdida_mwh', 'sum')
        ).reset_index()

        # Ordenando pelo volume de energia perdida
        metricas_comerciais = metricas_comerciais.sort_values(by='Energia_Suprimida_MWh', ascending=False)
        
        # Arredondando para apresentação
        metricas_comerciais['Energia_Suprimida_MWh'] = metricas_comerciais['Energia_Suprimida_MWh'].round(2)

        col1, col2 = st.columns([2, 1.2])

        with col1:
            st.subheader("Top Players por Energia Suprimida")
            fig2 = px.bar(
                metricas_comerciais.head(20), 
                x='Energia_Suprimida_MWh', 
                y='Proprietário Grupo Econômico Nome', 
                orientation='h',
                color='Energia_Suprimida_MWh',
                color_continuous_scale='Oranges',
                labels={'Energia_Suprimida_MWh': 'Energia Suprimida (MWh)', 'Proprietário Grupo Econômico Nome': 'Player'}
            )
            fig2.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            st.subheader("Tabela de Leads")
            st.dataframe(metricas_comerciais, use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado para este filtro.")


# ==========================================
# TELA 3: DETALHAMENTO POR USINA
# ==========================================
elif tela == "Detalhamento por Usina":
    st.title(f"Busca de Oportunidades: Por Usina - {filtro_fonte}")
    st.markdown("Pesquise por Grupo ou Usina e veja a quantidade de cortes **e o total de MWh perdidos** em cada local.")

    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        proprietarios = sorted(df_curtailment['Proprietário Grupo Econômico Nome'].dropna().unique())
        proprietario_selecionado = st.selectbox("1. Selecione o Grupo Econômico:", ["Todos"] + list(proprietarios))
        
    with col_filtro2:
        busca_usina = st.text_input("2. Pesquisar por Nome da Usina (Opcional):", "")

    df_filtrado = df_curtailment.copy()
    
    if proprietario_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Proprietário Grupo Econômico Nome'] == proprietario_selecionado]
        
    if busca_usina:
        df_filtrado = df_filtrado[df_filtrado['nom_usina'].str.contains(busca_usina, case=False, na=False)]

    if not df_filtrado.empty:
        # Agrupando por detalhes da usina e trazendo Ocorrências + Energia
        ranking_usinas = df_filtrado.groupby(
            ['Proprietário Grupo Econômico Nome', 'Fonte', 'nom_conjuntousina', 'nom_usina', 'ceg']
        ).agg(
            Eventos_Curtailment=('flg_restricao', 'count'),
            MWh_Suprimidos=('energia_perdida_mwh', 'sum')
        ).reset_index()
        
        ranking_usinas['MWh_Suprimidos'] = ranking_usinas['MWh_Suprimidos'].round(2)
        ranking_usinas = ranking_usinas.sort_values(by='MWh_Suprimidos', ascending=False)
        
        st.subheader(f"Resultados Encontrados: {len(ranking_usinas)} usinas afetadas")
        st.dataframe(ranking_usinas, use_container_width=True)
        
        st.subheader("Top Usinas do Filtro Atual (Por MWh Perdido)")
        fig_usinas = px.bar(
            ranking_usinas.head(15),
            x='MWh_Suprimidos',
            y='nom_usina',
            orientation='h',
            color='Eventos_Curtailment',
            color_continuous_scale='Blues',
            labels={'MWh_Suprimidos': 'Energia Suprimida (MWh)', 'Eventos_Curtailment': 'Qtd. Cortes', 'nom_usina': 'Usina'}
        )
        fig_usinas.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_usinas, use_container_width=True)
        
    else:
        st.warning("Nenhum dado encontrado com os filtros aplicados. Tente alterar a pesquisa.")

# ==========================================
# TELA 4: RANKING DE CLIENTES ALVO
# ==========================================
elif tela == "Ranking de Clientes Alvo":
    st.title(f"Monitoramento de Clientes Alvo - {filtro_fonte}")
    st.markdown("Acompanhamento do impacto de curtailment especificamente na carteira selecionada.")

    # Lista original passada para monitoramento
    lista_clientes_alvo = [
        "Auren Energia", "COPEL", "Axia Energia (CGT Eletrosul)", "Essentia Energia",
        "Pontal Energy", "Renova Energia", "Alupar", "GD Sun", "Serveng Energia",
        "Statkraft", "Axis Renováveis", "New Energy Options (NEO)", 
        "Eólica Serra das Vacas - PEC Energia", "Matrix + Proton", "BW Guirapá", 
        "V2i", "Aliança", "Raízen", "Bons Ventos da Serra II", "Bons Ventos da Serra I", 
        "UFV Irecê - Perfin", "Fazsol", "SPP Energias", "CPFL Energia", 
        "ADS Energias Renováveis", "SIMM Soluções", "Orion Transmissão", "Bulbe Energia", 
        "Eólicas Babilônia (Actis)"
    ]

    # Todos os proprietários disponíveis na base atual
    proprietarios_base = df_curtailment['Proprietário Grupo Econômico Nome'].dropna().unique().tolist()

    # Tentando achar correspondências aproximadas ou exatas para deixar pré-selecionado
    clientes_pre_selecionados = [c for c in proprietarios_base if any(alvo.lower() in c.lower() or c.lower() in alvo.lower() for alvo in lista_clientes_alvo)]

    st.markdown("### Selecione os Clientes para Monitorar")
    clientes_selecionados = st.multiselect(
        "A lista abaixo tentou encontrar os nomes exatos na base de dados. Adicione ou remova conforme necessário:",
        options=sorted(proprietarios_base),
        default=clientes_pre_selecionados
    )

    if clientes_selecionados:
        df_alvo = df_curtailment[df_curtailment['Proprietário Grupo Econômico Nome'].isin(clientes_selecionados)]
        
        if not df_alvo.empty:
            # Agrupando dados dos clientes alvo
            ranking_alvos = df_alvo.groupby('Proprietário Grupo Econômico Nome').agg(
                Eventos_Curtailment=('flg_restricao', 'count'),
                Energia_Suprimida_MWh=('energia_perdida_mwh', 'sum')
            ).reset_index()

            ranking_alvos['Energia_Suprimida_MWh'] = ranking_alvos['Energia_Suprimida_MWh'].round(2)
            ranking_alvos = ranking_alvos.sort_values(by='Energia_Suprimida_MWh', ascending=False)

            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("Ranking por MWh Suprimido (Carteira Alvo)")
                fig_alvos = px.bar(
                    ranking_alvos,
                    x='Energia_Suprimida_MWh',
                    y='Proprietário Grupo Econômico Nome',
                    orientation='h',
                    color='Eventos_Curtailment',
                    color_continuous_scale='Purples',
                    labels={'Energia_Suprimida_MWh': 'Energia Suprimida (MWh)', 'Eventos_Curtailment': 'Eventos', 'Proprietário Grupo Econômico Nome': 'Cliente'}
                )
                fig_alvos.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_alvos, use_container_width=True)

            with col2:
                st.subheader("Dados da Carteira")
                st.dataframe(ranking_alvos, use_container_width=True)
                
            st.info(f"**Resumo da Carteira Alvo:** Os clientes selecionados sofreram um total de **{ranking_alvos['Energia_Suprimida_MWh'].sum():,.2f} MWh** suprimidos.")
        else:
            st.warning("Nenhum dado de curtailment encontrado para os clientes selecionados neste filtro.")
    else:
        st.info("Por favor, selecione pelo menos um cliente na caixa acima para visualizar o ranking.")
