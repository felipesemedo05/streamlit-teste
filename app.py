import streamlit as st
import pandas as pd

# Função para aplicar as transformações
def processar_arquivo(df, claro):
    colunas_para_manter = ['location_id', 'impressions', 'uniques']
    
    df1 = df[((df['class'].isnull()) & (~df.location_id.isnull()) & 
              (df.gender_group.isnull()) & (df.country.isnull()) & 
              (df.date.isnull()) & (df.age_group.isnull()) & 
              (df.impression_hour.isnull()) & (df.num_total_impressions.isnull()) & 
              (df.home.isnull()))]
    
    df1 = df1.sort_values('impressions', ascending=False)
    df1 = df1.drop(columns=[coluna for coluna in df.columns if coluna not in colunas_para_manter]).reset_index(drop=True)
    
    claro = claro.rename(columns={'id': 'location_id'})
    claro = claro[['location_id', 'latitude', 'longitude']]
    
    df1['location_id'] = df['location_id'].str.extract('([0-9]+)', expand=False)
    
    final = df1.merge(claro, on='location_id')
    
    return final

# Interface do Streamlit
st.title('Processamento de Arquivo CSV')

# Upload do arquivo (dataset principal)
uploaded_file = st.file_uploader("Escolha um arquivo CSV para o dataset principal", type="csv")

if uploaded_file is not None:
    # Leitura do arquivo claro diretamente do computador
    claro_path = 'claro.csv'  # Atualize com o caminho do seu arquivo
    claro = pd.read_csv(claro_path, encoding='latin-1')

    # Leitura do arquivo CSV do dataset principal
    df = pd.read_csv(uploaded_file)
    
    # Exibindo o período das datas
    if 'start_date' in df.columns and 'end_date' in df.columns:
        start_date = df['start_date'].dropna().iloc[0]
        end_date = df['end_date'].dropna().iloc[0]
        st.write(f"Período do CSV: {start_date} até {end_date}")
    else:
        st.write("Colunas 'start_date' e/ou 'end_date' não encontradas no arquivo CSV.")
    
    # Processamento do arquivo
    final = processar_arquivo(df, claro)
    
    # Exibe uma amostra do dataframe final
    st.write("Amostra dos dados processados:")
    st.dataframe(final.head())

    # Criação do botão de download
    csv = final.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Baixar arquivo processado",
        data=csv,
        file_name='arquivo_processado.csv',
        mime='text/csv',
    )
