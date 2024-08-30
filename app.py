import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO
import openpyxl

# Função para aplicar as transformações
def processar_arquivo(df, claro):
    colunas_para_manter = ['location_id', 'impressions', 'uniques']

    # Verifica se as colunas padrão existem
    colunas_esperadas = ['class', 'location_id', 'gender_group', 'country', 'date', 'age_group', 'impression_hour', 'num_total_impressions', 'home']
    
    if all(coluna in df.columns for coluna in colunas_esperadas):
        df1 = df[((df['class'].isnull()) & (~df['location_id'].isnull()) & 
                  (df['gender_group'].isnull()) & (df['country'].isnull()) & 
                  (df['date'].isnull()) & (df['age_group'].isnull()) & 
                  (df['impression_hour'].isnull()) & (df['num_total_impressions'].isnull()) & 
                  (df['home'].isnull()))]
    else:
        # Executa o código alternativo com nomes de colunas diferentes
        df1 = df[((df['social_class'].isnull()) & (~df['location_id'].isnull()) & 
                  (df['gender'].isnull()) & (df['nationality'].isnull()) & 
                  (df['date'].isnull()) & (df['age'].isnull()) & 
                  (df['impression_hour'].isnull()) & (df['num_total_impressions'].isnull()) & 
                  (df['residence_name'].isnull()))]

    df1 = df1.sort_values('impressions', ascending=False)
    df1 = df1[[coluna for coluna in df.columns if coluna in colunas_para_manter]].reset_index(drop=True)
    
    claro = claro.rename(columns={'id': 'location_id'})
    claro = claro[['location_id', 'latitude', 'longitude']]
    
    df1['location_id'] = df1['location_id'].astype(str)
    df1['location_id'] = df1['location_id'].str.extract('([0-9]+)', expand=False)
    
    final = df1.merge(claro, on='location_id')

    # Excluir colunas totalmente vazias
    final = final.dropna(axis=1, how='all')

    return final

# Interface do Streamlit
st.set_page_config(page_title='Processamento de Arquivo', layout='wide')

st.title('Processamento de Arquivo CSV e Parquet')

# Upload do arquivo CSV ou Parquet
uploaded_file = st.file_uploader("Escolha um arquivo CSV ou Parquet para o dataset principal", type=["csv", "parquet"])

if uploaded_file is not None:
    try:
        # Obter o nome do arquivo enviado
        original_filename = os.path.splitext(uploaded_file.name)[0]

        # Leitura do arquivo claro diretamente do computador
        claro_path = 'claro.csv'  # Atualize com o caminho do seu arquivo
        claro = pd.read_csv(claro_path, encoding='latin-1')

        # Leitura do arquivo CSV ou Parquet do dataset principal
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='latin-1')
        elif uploaded_file.name.endswith('.parquet'):
            df = pd.read_parquet(uploaded_file)
        
        # Processamento do arquivo
        final = processar_arquivo(df, claro)

        # Criar uma lista das colunas preenchidas (não vazias)
        colunas_preenchidas = final.columns.tolist()

        # Espaço para selecionar colunas para download
        st.header("Seleção de Colunas para Download")
        colunas_selecionadas = st.multiselect(
            "Escolha as colunas que deseja incluir no download:",
            options=colunas_preenchidas
        )

        # Filtrar o DataFrame com base nas colunas selecionadas
        final_filtrado = final[colunas_selecionadas]

        # Criar buffers para arquivos
        output_csv = BytesIO()
        output_excel = BytesIO()

        # Definir o nome do arquivo processado CSV
        processed_filename_csv = f"{original_filename}_processado_{datetime.now().strftime('%Y-%m-%d')}.csv"

        # Definir o nome do arquivo processado EXCEL
        processed_filename_xlsx = f"{original_filename}_processado_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

        # Criar o CSV
        final_filtrado.to_csv(output_csv, index=False)
        output_csv.seek(0)

        # Criar o Excel
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            final_filtrado.to_excel(writer, index=False, sheet_name='Dados Processados')
        output_excel.seek(0)

        # Abas para Navegação
        tab1, tab2, tab3 = st.tabs(["Ponto a Ponto", "Estatísticas Descritivas", "Composição"])

        with tab1:
            st.header("Ponto a Ponto")
            st.dataframe(final_filtrado)

            st.download_button(
                label="Baixar CSV Processado",
                data=output_csv,
                file_name=processed_filename_csv,
                mime="text/csv"
            )

            st.download_button(
                label="Baixar Excel Processado",
                data=output_excel,
                file_name=processed_filename_xlsx,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with tab2:
            st.header("Estatísticas Descritivas")
            col1, col2 = st.columns([2, 3])

            with col1:
                st.write(periodo_info)
                st.write(f"Quantidade de location_id: {unique_location_ids}")

                if 'impressions' in df.columns:            
                    st.subheader("Estatísticas de 'impressions'")
                    impressions_describe = final['impressions'].describe()
                    st.write(f"Contagem: {impressions_describe['count']}")
                    st.write(f"Média: {impressions_describe['mean']:.2f}")
                    st.write(f"Desvio Padrão: {impressions_describe['std']:.2f}")
                    st.write(f"Mínimo: {impressions_describe['min']}")
                    st.write(f"25º Percentil: {impressions_describe['25%']}")
                    st.write(f"Mediana (50º Percentil): {impressions_describe['50%']}")
                    st.write(f"75º Percentil: {impressions_describe['75%']}")
                    st.write(f"Máximo: {impressions_describe['max']}")

                if 'uniques' in df.columns:
                    st.subheader("Estatísticas de 'uniques'")
                    uniques_describe = final['uniques'].describe()
                    st.write(f"Contagem: {uniques_describe['count']}")
                    st.write(f"Média: {uniques_describe['mean']:.2f}")
                    st.write(f"Desvio Padrão: {uniques_describe['std']:.2f}")
                    st.write(f"Mínimo: {uniques_describe['min']}")
                    st.write(f"25º Percentil: {uniques_describe['25%']}")
                    st.write(f"Mediana (50º Percentil): {uniques_describe['50%']}")
                    st.write(f"75º Percentil: {uniques_describe['75%']}")
                    st.write(f"Máximo: {uniques_describe['max']}")

                # Exibir porcentagens por classe
                st.subheader("Porcentagem por Classe Social")
                for classe, porcentagem in porcentagem_por_classe.items():
                    st.write(f"{classe}: {porcentagem:.2f}%")

                # Exibir porcentagens por gênero
                st.subheader("Porcentagem por Gênero")
                for genero, porcentagem in porcentagem_por_genero.items():
                    st.write(f"{genero}: {porcentagem:.2f}%")

                # Exibir porcentagens por faixa etária
                st.subheader("Porcentagem por Faixa Etária")
                for idade, porcentagem in porcentagem_por_idade.items():
                    faixa = faixas_etarias.get(idade, idade)
                    st.write(f"{faixa}: {porcentagem:.2f}%")

        with tab3:
            st.header("Cálculo de Composição")
            selected_classes = st.multiselect(
                "Selecione as Classes Sociais",
                options=lista_classes,
            )
            selected_genders = st.multiselect(
                "Selecione os Gêneros",
                options=lista_genero,
            )
            selected_ages = st.multiselect(
                "Selecione as Faixas Etárias",
                options=[faixa for idade, faixa in faixas_etarias.items()],
            )

            # Soma das porcentagens selecionadas
            soma_porcentagem_classes = sum(porcentagem_por_classe[classe] for classe in selected_classes)
            soma_porcentagem_generos = sum(porcentagem_por_genero[genero] for genero in selected_genders)
            soma_porcentagem_idades = sum(porcentagem_por_idade[idade] for idade, faixa in faixas_etarias.items() if faixa in selected_ages)

            # Calcular a composição final
            composicao = (soma_porcentagem_classes * soma_porcentagem_generos * soma_porcentagem_idades) / 10000

            st.write(f"Soma das Porcentagens de Classes: {soma_porcentagem_classes:.2f}%")
            st.write(f"Soma das Porcentagens de Gêneros: {soma_porcentagem_generos:.2f}%")
            st.write(f"Soma das Porcentagens de Faixas Etárias: {soma_porcentagem_idades:.2f}%")
            st.write(f"Composição Final: {composicao:.2f}%")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
