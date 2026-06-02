import os
import pandas as pd
import glob

# Configuração de caminhos e padrões
diretorio = r"C:\Users\gusri\OneDrive\Documentos\Teste de COFF\EOL"
prefixo = "RESTRICAO_COFF_EOLICA_DETAIL_2026"

# Define o nome do arquivo que será criado no final com todos os dados
arquivo_saida = os.path.join(diretorio, "RESTRICAO_COFF_EOLICA_DETAIL_2026_COMBINADO.csv")

# Padrão de busca
# Exemplo que ele encontra: RESTRICAO_COFF_EOLICA_DETAIL_2026_01.csv
padrao_busca = os.path.join(diretorio, f"{prefixo}*.csv")
arquivos = glob.glob(padrao_busca)

# Tenta encontrar .cvs 
if len(arquivos) == 0:
    padrao_busca_alt = os.path.join(diretorio, f"{prefixo}*")
    arquivos = [f for f in glob.glob(padrao_busca_alt) if f.lower().endswith(('.csv', '.cvs'))]

print(f"Diretório de busca: {diretorio}")
print(f"Foram encontrados {len(arquivos)} arquivos correspondentes. Iniciando a leitura...\n")

lista_dataframes = []

for arquivo in arquivos:
    try:
        # Se os seus CSVs forem no padrão brasileiro (separados por ;), troque por pd.read_csv(arquivo, sep=';', encoding='latin1')
        df = pd.read_csv(arquivo)
        lista_dataframes.append(df)
        print(f" -> Lido com sucesso: {os.path.basename(arquivo)}")
    except Exception as e:
        print(f" -> Erro ao ler {os.path.basename(arquivo)}: {e}")

# Verificação de segurança
if len(lista_dataframes) > 0:
    print("\nJuntando os arquivos...")
    # Junta tudo em um único DataFrame
    df_final = pd.concat(lista_dataframes, ignore_index=True)
    
    # Salva o arquivo final consolidado (sem exportar a coluna de índice numérico)
    df_final.to_csv(arquivo_saida, index=False)
    print(f"\n[SUCESSO] Processo concluído!")
    print(f"Arquivo consolidado salvo em: {arquivo_saida}")
else:
    print("\n[AVISO] Nenhum arquivo válido foi encontrado para concatenação.")
    print("Por favor, verifique se:")
    print("1. O caminho da pasta está correto.")
    print("2. Os arquivos realmente começam com 'RESTRICAO_COFF_EOLICA_DETAIL_2026'")
