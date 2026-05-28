# -*- coding: utf-8 -*-
import pandas as pd
import os

# Configuração dos caminhos dos arquivos
caminho_csv = r"C:\Users\gusri\OneDrive\Documentos\Teste de COFF\EOL\RESTRICAO_COFF_EOLICA_DETAIL_2026_COMBINADO.csv"
caminho_xlsx = r"C:\Users\gusri\OneDrive\Documentos\Teste de COFF\Tags Player_CEG\Correlaçao CEG player UFV EOL.xlsx"

# Caminho onde o novo arquivo será salvo (para não sobrescrever o original e perder dados por engano)
caminho_saida = r"C:\Users\gusri\OneDrive\Documentos\Teste de COFF\EOL\RESTRICAO_COFF_EOLICA_DETAIL_2026_COMBINADO_PLAYER.csv"

try:
    print("Iniciando a leitura do arquivo CSV (Restrição)...")
    # Lendo o CSV. Arquivos desse tipo do ONS costumam usar ponto e vírgula como separador.
    # Caso o seu CSV combinado esteja separado por vírgula, troque sep=';' por sep=','
    df_csv = pd.read_csv(caminho_csv, sep=';')

    print("Iniciando a leitura do arquivo Excel (Correlação)...")
    # Lendo apenas as colunas necessárias do Excel para otimizar a memória
    df_xlsx = pd.read_excel(caminho_xlsx, usecols=['CEG', 'Proprietário Grupo Econômico Nome'])

    # Removendo possíveis espaços em branco nas extremidades dos códigos CEG que poderiam atrapalhar o cruzamento
    if 'ceg' in df_csv.columns:
        df_csv['ceg'] = df_csv['ceg'].astype(str).str.strip()
    
    df_xlsx['CEG'] = df_xlsx['CEG'].astype(str).str.strip()

    print("Realizando o cruzamento de dados (PROCV/Merge)...")
    # Fazendo o merge (equivalente ao PROCV do Excel ou LEFT JOIN do SQL)
    # left_on é a coluna no CSV (normalmente minúscula 'ceg')
    # right_on é a coluna no Excel ('CEG')
    df_final = pd.merge(
        df_csv, 
        df_xlsx, 
        left_on='ceg', 
        right_on='CEG', 
        how='left'
    )

    # Removendo a coluna 'CEG' maiúscula que veio do Excel para não ficar duplicada, 
    # mantendo apenas a 'ceg' original do CSV e a nova coluna de Proprietário
    if 'CEG' in df_final.columns and 'ceg' in df_final.columns:
        df_final = df_final.drop(columns=['CEG'])

    print("Salvando o arquivo final gerado...")
    # Salvando o resultado. Mantemos o separador ';' que é o padrão brasileiro
    df_final.to_csv(caminho_saida, sep=';', index=False)

    print(f"\n[SUCESSO] Processo concluído!")
    print(f"O novo arquivo com a coluna 'Proprietário Grupo Econômico Nome' foi salvo em:\n{caminho_saida}")

except FileNotFoundError as e:
    print(f"\n[ERRO] Arquivo não encontrado: {e.filename}")
    print("Verifique se os caminhos apontam exatamente para onde os arquivos estão salvos.")
except Exception as e:
    print(f"\n[ERRO] Ocorreu um erro inesperado: {e}")