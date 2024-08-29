import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO
import openpyxl

# Função para aplicar as transformações
def processar_arquivo(df, claro, com_data):
    colunas_para_manter = ['location_id', 'impressions', 'uniques']

    # Verifica se as colunas padrão existem
    colunas_esperadas = ['class', 'location_id', 'gender_group', 'country', 'date', 'age_group', 'impression_hour', 'num_total_impressions', 'home']
    
    if all(coluna in df.columns for coluna in colunas_esperadas):
        if com_data:
            df1 = df[((df['class'].isnull()) & (~df['location_id'].isnull()) & 
                      (df['gender_group'].isnull()) & (df['country'].isnull()) & 
                      (~df['date'].isnull()) & (df['age_group'].isnull()) & 
                      (df['impression_hour'].isnull()) & (df['num_total_impressions'].isnull()) & 
                      (df['home'].isnull()))]
        else:
            df1 = df[((df['class'].isnull()) & (~df['location_id'].isnull()) & 
                      (df['gender_group'].isnull()) & (df['country'].isnull()) & 
                      (df['date'].isnull()) & (df['age_group'].isnull()) & 
                      (df['impression_hour'].isnull()) & (df['num_total_impressions'].isnull()) & 
                      (df['home'].isnull()))]
    else:
        # Executa o código alternativo com nomes de colunas diferentes
        if com_data:
            df1 = df[((df['social_class'].isnull()) & (~df['location_id'].isnull()) & 
                      (df['gender'].isnull()) & (df['nationality'].isnull()) & 
                      (~df['date'].isnull()) & (df['age'].isnull()) & 
                      (df['impression_hour'].isnull()) & (df['num_total_impressions'].isnull()) & 
                      (df['residence_name'].isnull()))]
        else:
            df1 = df[((df['social_class'].isnull()) & (~df['location_id'].isnull()) & 
                      (df['gender'].isnull()) & (df['nationality'].isnull()) & 
                      (df['date'].isnull()) & (df['age'].isnull()) & 
                      (df['impression_hour'].isnull()) & (df['num_total_impressions'].isnull()) & 
                      (df['residence_name'].isnull()))]

    df1 = df1.sort_values('impressions', ascending=False)
    df1 = df1[[coluna for coluna in df.columns if coluna in colunas_para_manter]].reset_index(drop=True)
    
    claro = claro.rename(columns={'id': 'location_id'})
    claro = claro[['location_id', 'latitude', 'longitude']]
    
    # Garantir que location_id é tratado como string
    df1['location_id'] = df1['location_id'].astype(str)
    
    final = df1.merge(claro, on='location_id')
    final['location_id'] = final['location_id'].str.extract('([0-9]+)', expand=False)
    final['frequencia'] = final['impressions'] / final['uniques']
    
    # Filtragem adicional com base na opção com_data
    if com_data:
        final = final[~final['date'].isnull()]
    else:
        final['date'] = df['date']
        final = final[final['date'].isnull()]

    return final

# Interface do Streamlit
st.set_page_config(page_title='Processamento de Arquivo', layout='wide')

st.title('Processamento de Arquivo CSV e Parquet')

# Navegação entre abas
aba_selecionada = st.sidebar.radio("Escolha uma aba", ["Processamento de Arquivo", "Dashboard"])

if aba_selecionada == "Processamento de Arquivo":
    # Upload do arquivo CSV ou Parquet
    uploaded_file = st.file_uploader("Escolha um arquivo CSV ou Parquet para o dataset principal", type=["csv", "parquet"])

    if uploaded_file is not None:
        try:
            # Obter o nome do arquivo enviado
            original_filename = os.path.splitext(uploaded_file.name)[0]  # Pega o nome sem a extensão

            # Leitura do arquivo claro diretamente do computador
            claro_path = 'claro.csv'  # Atualize com o caminho do seu arquivo
            claro = pd.read_csv(claro_path, encoding='latin-1')

            # Leitura do arquivo CSV ou Parquet do dataset principal
            if uploaded_file.name.endswith('.csv'):
                try:
                    df = pd.read_csv(uploaded_file, encoding='latin-1')
                except UnicodeDecodeError:
                    st.error("Erro ao ler o arquivo CSV com codificação 'latin-1'.")
                    st.error("Tente usar outra codificação ou verifique o arquivo.")
                    st.stop()
            elif uploaded_file.name.endswith('.parquet'):
                try:
                    df = pd.read_parquet(uploaded_file)
                except Exception as e:
                    st.error(f"Erro ao ler o arquivo Parquet: {e}")
                    st.stop()

            # Exibindo o período das datas, se as colunas existirem
            if 'start_date' in df.columns and 'end_date' in df.columns:
                df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
                df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')
                
                # Verifica se existem valores não nulos
                if not df['start_date'].dropna().empty and not df['end_date'].dropna().empty:
                    start_date = df['start_date'].dropna().iloc[0]
                    end_date = df['end_date'].dropna().iloc[0]
                    dias = (end_date - start_date).days + 1  # Adiciona 1 ao cálculo dos dias
                    periodo_info = f"Período do arquivo: {start_date.strftime('%Y-%m-%d')} até {end_date.strftime('%Y-%m-%d')} ({dias} dias)"
                else:
                    periodo_info = "Não há datas válidas no arquivo."
            else:
                periodo_info = "Colunas 'start_date' e/ou 'end_date' não encontradas no arquivo."

            # Opção para incluir ou não dados com datas
            com_data = st.radio("Você deseja incluir dados com datas?", ("Sim", "Não")) == "Sim"

            # Processamento do arquivo
            final = processar_arquivo(df, claro, com_data)

            # Salvar os dados processados no session_state
            st.session_state['final'] = final

            if st.session_state['final'] is not None:
                # Layout de colunas
                col1, col2 = st.columns([2, 3])

                # Seção de Estatísticas Descritivas
                with col1:
                    st.header("Estatísticas Descritivas")
                    st.write(periodo_info)
                    st.write(f"Quantidade de location_id: {st.session_state['final']['location_id'].nunique()}")

                    if 'impressions' in df.columns:            
                        st.subheader("Estatísticas de 'impressions'")
                        impressions_describe = round(st.session_state['final']['impressions'].describe(), 2).to_dict()
                        st.write(impressions_describe)

                    if 'uniques' in df.columns:
                        st.subheader("Estatísticas de 'uniques'")
                        uniques_describe = round(st.session_state['final']['uniques'].describe(), 2).to_dict()
                        st.write(uniques_describe)

                # Seção de Dados Processados e Downloads
                with col2:
                    st.header("Dados Processados")
                    st.dataframe(st.session_state['final'].head())

                    # Criar buffers para arquivos
                    output_csv = BytesIO()
                    output_excel = BytesIO()

                    # Definir o nome do arquivo processado CSV
                    processed_filename_csv = f"{original_filename}_processado_{datetime.now().strftime('%Y-%m-%d')}.csv"

                    # Definir o nome do arquivo processado EXCEL
                    processed_filename_xlsx = f"{original_filename}_processado_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

                    # Criar o CSV
                    st.session_state['final'].to_csv(output_csv, index=False)
                    output_csv.seek(0)

                    # Criar o Excel
                    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                        st.session_state['final'].to_excel(writer, index=False, sheet_name='Dados Processados')
                    output_excel.seek(0)

                    st.download_button(
                        label="💾 Baixar Arquivo Processado (CSV)",
                        data=output_csv,
                        file_name=processed_filename_csv,
                        mime='text/csv',
                    )

                    st.download_button(
                        label="💾 Baixar Arquivo Processado (Excel)",
                        data=output_excel,
                        file_name=processed_filename_xlsx,
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    )
            else:
                st.warning("Nenhum dado processado encontrado. Por favor, carregue e processe um arquivo primeiro.")

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

elif aba_selecionada == "Dashboard":
    if 'final' in st.session_state:
        final = st.session_state['final']
        st.header("Dashboard de Análise de Dados")
        
        st.write("Os gráficos foram removidos. Adicione aqui qualquer outra informação ou análise desejada.")
        
    else:
        st.warning("Nenhum dado processado encontrado. Por favor, carregue e processe um arquivo primeiro.")
