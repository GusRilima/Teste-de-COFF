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
tela = st.sidebar.radio(
    "Selecione a Visão:", 
    [
        "Visão Geral (Ocorrências)", 
        "Impacto em Energia (MWh)",
        "Detalhamento por Usina",
        "Acompanhamento Comercial (CRM)" # <--- NOVA TELA ADICIONADA
    ]
)
st.sidebar.markdown("---")
st.sidebar.info("Dashboard para identificação de oportunidades de produtos focados em Curtailment Eólico.")

# 3. Carregamento e Tratamento dos Dados em Cache
@st.cache_data
def load_data():
    # ID exato do NOVO arquivo no Google Drive
    file_id = '1-81IsyRU-7DUmbotSe4-f2Xu_1HBWpHC'
    url = f'https://drive.google.com/uc?id={file_id}'
    
    # Nome do arquivo temporário que será salvo
    arquivo_temporario = 'base_dados_drive.csv'
    
    # Baixa o arquivo do Drive apenas se ele ainda não existir na pasta
    if not os.path.exists(arquivo_temporario):
        gdown.download(url, arquivo_temporario, quiet=False)
        
    # Lê o arquivo baixado
    df = pd.read_csv(arquivo_temporario, sep=';', low_memory=False)
    
    # Tratamento de todas as colunas numéricas necessárias para os cálculos
    colunas_numericas = ['flg_dadoventoinvalido', 'val_geracaoestimada', 'val_geracaoverificada', 'val_ventoverificado']
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

df = load_data()

# Isolando eventos de Curtailment e criando a coluna de Energia Perdida
df_curtailment = df[df['flg_dadoventoinvalido'] == 1].copy()
df_curtailment['energia_perdida_mwh'] = df_curtailment['val_geracaoestimada'] - df_curtailment['val_geracaoverificada']

# ==========================================
# INICIALIZANDO O BANCO DE DADOS DO CRM (Sessão)
# ==========================================
# Verifica se a tabela de CRM já existe na memória do dashboard. Se não, cria.
if 'crm_data' not in st.session_state:
    # Cria uma lista de leads baseada na energia total suprimida
    leads = df_curtailment.groupby('Proprietário Grupo Econômico Nome')['energia_perdida_mwh'].sum().reset_index()
    leads.columns = ['Grupo Econômico', 'Potencial_MWh']
    leads['Potencial_MWh'] = leads['Potencial_MWh'].round(2)
    leads = leads.sort_values(by='Potencial_MWh', ascending=False)
    
    # Adiciona uma coluna de Status com o valor padrão
    leads['Status Comercial'] = '1 - A Abordar'
    leads['Anotações'] = ''
    
    # Salva na memória
    st.session_state['crm_data'] = leads

# ==========================================
# TELA 1: VISÃO GERAL (OCORRÊNCIAS)
# ==========================================
if tela == "Visão Geral (Ocorrências)":
    st.title("Radar Comercial: Eventos de Restrição")
    st.markdown("Identificação de players com o **maior volume de eventos de restrição** (quantidade de vezes que sofreram corte).")

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

# ==========================================
# TELA 2: IMPACTO EM ENERGIA (MWh)
# ==========================================
elif tela == "Impacto em Energia (MWh)":
    st.title("Dor Financeira: Energia Suprimida")
    st.markdown("Foco no **tamanho do prejuízo (MWh)**. Quais Grupos Econômicos deixaram de gerar mais energia por causa do curtailment?")

    # Agrupando métricas comerciais de volume
    metricas_comerciais = df_curtailment.groupby('Proprietário Grupo Econômico Nome').agg(
        Eventos_Curtailment=('flg_dadoventoinvalido', 'count'),
        Energia_Suprimida_MWh=('energia_perdida_mwh', 'sum'),
        Vento_Medio_Desperdicado=('val_ventoverificado', 'mean')
    ).reset_index()

    # Ordenando pelo volume de energia perdida
    metricas_comerciais = metricas_comerciais.sort_values(by='Energia_Suprimida_MWh', ascending=False)
    
    # Arredondando para apresentação
    metricas_comerciais['Energia_Suprimida_MWh'] = metricas_comerciais['Energia_Suprimida_MWh'].round(2)
    metricas_comerciais['Vento_Medio_Desperdicado'] = metricas_comerciais['Vento_Medio_Desperdicado'].round(2)

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
        st.markdown("Inclui força do vento ocioso.")
        st.dataframe(metricas_comerciais, use_container_width=True)

# ==========================================
# TELA 3: DETALHAMENTO POR USINA
# ==========================================
elif tela == "Detalhamento por Usina":
    st.title("Busca de Oportunidades: Por Usina")
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
            ['Proprietário Grupo Econômico Nome', 'nom_conjuntousina', 'nom_usina', 'ceg']
        ).agg(
            Eventos_Curtailment=('flg_dadoventoinvalido', 'count'),
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
# TELA 4: ACOMPANHAMENTO COMERCIAL (CRM)
# ==========================================
elif tela == "Acompanhamento Comercial (CRM)":
    st.title("Acompanhamento Comercial (CRM)")
    st.markdown("Gerencie o pipeline de vendas. Altere os status abaixo diretamente na tabela para atualizar os gráficos.")

    # Opções de status disponíveis
    opcoes_status = [
        '1 - A Abordar', 
        '2 - Em Contato', 
        '3 - Em Negociação', 
        '4 - Proposta Enviada',
        '5 - Fechado (Ganha)', 
        '6 - Descartado (Perdida)'
    ]

    # Exibe a tabela interativa para o usuário editar
    st.subheader("Tabela de Pipeline")
    df_crm_editado = st.data_editor(
        st.session_state['crm_data'],
        column_config={
            "Status Comercial": st.column_config.SelectboxColumn(
                "Status Comercial",
                help="Selecione a fase atual da negociação",
                options=opcoes_status,
                required=True,
            ),
            "Anotações": st.column_config.TextColumn(
                "Anotações",
                help="Insira observações sobre a negociação"
            ),
            "Grupo Econômico": st.column_config.TextColumn(disabled=True),
            "Potencial_MWh": st.column_config.NumberColumn(disabled=True)
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Atualiza a memória com as edições do usuário
    st.session_state['crm_data'] = df_crm_editado

    st.markdown("---")
    
    # Criando visualizações baseadas nos status editados
    col_grafico1, col_grafico2 = st.columns(2)
    
    # Resumo da Quantidade de Empresas por Status
    resumo_qtd = df_crm_editado.groupby('Status Comercial').size().reset_index(name='Qtd_Empresas')
    
    # Resumo do MWh em Jogo por Status
    resumo_mwh = df_crm_editado.groupby('Status Comercial')['Potencial_MWh'].sum().reset_index()

    with col_grafico1:
        st.subheader("Empresas por Fase")
        fig_funil_qtd = px.funnel(
            resumo_qtd, 
            x='Qtd_Empresas', 
            y='Status Comercial',
            labels={'Qtd_Empresas': 'Quantidade de Empresas'}
        )
        # Força a ordem correta do funil
        fig_funil_qtd.update_yaxes(categoryorder='array', categoryarray=opcoes_status[::-1])
        st.plotly_chart(fig_funil_qtd, use_container_width=True)

    with col_grafico2:
        st.subheader("MWh Potencial por Fase")
        fig_pizza_mwh = px.pie(
            resumo_mwh, 
            values='Potencial_MWh', 
            names='Status Comercial',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_pizza_mwh, use_container_width=True)
