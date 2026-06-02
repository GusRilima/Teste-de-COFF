import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

caminho_entrada = r"C:\Users\gusri\OneDrive\Documentos\Teste de COFF\EOL\RESTRICAO_COFF_EOLICA_DETAIL_2026_COMBINADO_PLAYER.csv"
caminho_saida = r"C:\Users\gusri\OneDrive\Documentos\Teste de COFF\EOL\RELATORIO_COMERCIAL_LEADS.csv"

print("Processando métricas comerciais...")
df = pd.read_csv(caminho_entrada, sep=';', low_memory=False)

# Tratamento e conversão
df['flg_dadoventoinvalido'] = pd.to_numeric(df['flg_dadoventoinvalido'], errors='coerce')
df['val_geracaoestimada'] = pd.to_numeric(df['val_geracaoestimada'], errors='coerce')
df['val_geracaoverificada'] = pd.to_numeric(df['val_geracaoverificada'], errors='coerce')
df['val_ventoverificado'] = pd.to_numeric(df['val_ventoverificado'], errors='coerce')

# Isolando eventos de Curtailment e calculando a perda
df_curtailment = df[df['flg_dadoventoinvalido'] == 1].copy()
df_curtailment['energia_perdida_mwh'] = df_curtailment['val_geracaoestimada'] - df_curtailment['val_geracaoverificada']

# Agrupando métricas por Player
metricas_comerciais = df_curtailment.groupby('Proprietário Grupo Econômico Nome').agg(
    Eventos_Curtailment=('flg_dadoventoinvalido', 'count'),
    Energia_Suprimida_MWh=('energia_perdida_mwh', 'sum'),
    Vento_Medio_Desperdicado=('val_ventoverificado', 'mean')
).reset_index()

# Ordenando pelos players com maior perda de energia
metricas_comerciais = metricas_comerciais.sort_values(by='Energia_Suprimida_MWh', ascending=False)

# Arredondando os valores para ficar amigável na apresentação
metricas_comerciais['Energia_Suprimida_MWh'] = metricas_comerciais['Energia_Suprimida_MWh'].round(2)
metricas_comerciais['Vento_Medio_Desperdicado'] = metricas_comerciais['Vento_Medio_Desperdicado'].round(2)

print("\nTOP 5 LEADS COMERCIAIS (Por Energia Suprimida):")
print(metricas_comerciais.head(5).to_string(index=False))

# Exportando a tabela de Leads para a equipe de vendas
metricas_comerciais.to_csv(caminho_saida, sep=';', index=False)
print(f"\nRelatório comercial salvo em: {caminho_saida}")

# Plotagem: Gráfico para apresentação comercial
plt.figure(figsize=(12, 6))
top_10 = metricas_comerciais.head(10)

barplot = sns.barplot(
    data=top_10, 
    x='Energia_Suprimida_MWh', 
    y='Proprietário Grupo Econômico Nome', 
    palette='Reds_r'
)

plt.title("Impacto do Curtailment: Top 10 Players por Energia Suprimida (MWh)", fontsize=16, fontweight='bold')
plt.xlabel("Energia Suprimida (MWh) - Oportunidade Financeira", fontsize=12)
plt.ylabel("Player", fontsize=12)

# Adicionando os rótulos de dados nas barras
for p in barplot.patches:
    width = p.get_width()
    plt.text(width + (width * 0.01), p.get_y() + p.get_height()/2. + 0.1, 
             f'{width:,.0f}', ha="left", fontsize=10)

plt.tight_layout()
plt.show()
