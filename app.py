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
    #claro = claro[['location_id', 'latitude', 'longitude']]
    
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
            start_date = df['start_date'].dropna().iloc[0]
            end_date = df['end_date'].dropna().iloc[0]
            dias = (end_date - start_date).days + 1  # Adiciona 1 ao cálculo dos dias
            periodo_info = f"Período do arquivo: {start_date.strftime('%Y-%m-%d')} até {end_date.strftime('%Y-%m-%d')} ({dias} dias)"
        else:
            periodo_info = "Colunas 'start_date' e/ou 'end_date' não encontradas no arquivo."

        # Processamento do arquivo
        final = processar_arquivo(df, claro)

        # Criar uma lista das colunas preenchidas (não vazias)
        colunas_preenchidas = final.columns.tolist()

        # Exibição das colunas selecionáveis
        st.header("Seleção de Colunas para Download")
        colunas_selecionadas = st.multiselect(
            "Escolha as colunas que deseja incluir no download:",
            options=colunas_preenchidas,
        )

        # Filtrar o DataFrame com base nas colunas selecionadas
        final_filtrado = final[colunas_selecionadas]

        # Contagem de location_id únicos
        unique_location_ids = final['location_id'].nunique()

        # Cálculo das somas de 'uniques' por classe
        lista_classes = ['A', 'B1', 'B2', 'C1', 'C2', 'DE']
        df_classe = df[((~df['class'].isnull()) & 
                        (df['location_id'].isnull()) & 
                        (df['gender_group'].isnull()) & 
                        (df['country'].isnull()) & 
                        (df['date'].isnull()) & 
                        (df['age_group'].isnull()) & 
                        (df['impression_hour'].isnull()) & 
                        (df['num_total_impressions'].isnull()) & 
                        (df['home'].isnull()))]

        total_por_classe = df_classe[df_classe['class'].isin(lista_classes)].groupby('class')['uniques'].sum().to_dict()

        # Cálculo do total de alcance
        total_alcance = df[((df['class'].isnull()) & 
                            (df['location_id'].isnull()) & 
                            (df['gender_group'].isnull()) & 
                            (df['country'].isnull()) & 
                            (df['date'].isnull()) & 
                            (df['age_group'].isnull()) & 
                            (df['impression_hour'].isnull()) & 
                            (df['num_total_impressions'].isnull()) & 
                            (df['home'].isnull()))]['uniques'].sum()

        # Cálculo do total de impactos
        total_impactos = df[((df['class'].isnull()) & 
                            (df['location_id'].isnull()) & 
                            (df['gender_group'].isnull()) & 
                            (df['country'].isnull()) & 
                            (df['date'].isnull()) & 
                            (df['age_group'].isnull()) & 
                            (df['impression_hour'].isnull()) & 
                            (df['num_total_impressions'].isnull()) & 
                            (df['home'].isnull()))]['impressions'].sum()
        
        # Cálculo da porcentagem por classe
        porcentagem_por_classe = {classe: (total / total_alcance) * 100 
                                  for classe, total in total_por_classe.items()}

        # Cálculo das somas de 'uniques' por gênero
        lista_genero = ['F', 'M']
        df_genero = df[((df['class'].isnull()) & 
                        (df['location_id'].isnull()) & 
                        ~(df['gender_group'].isnull()) & 
                        (df['country'].isnull()) & 
                        (df['date'].isnull()) & 
                        ~(df['age_group'].isnull()) & 
                        (df['impression_hour'].isnull()) & 
                        (df['num_total_impressions'].isnull()) & 
                        (df['home'].isnull()))]

        total_por_genero = df_genero[(df_genero['gender_group'].isin(lista_genero)) & 
                                     (df_genero['age_group'] != 0)].groupby('gender_group')['uniques'].sum().to_dict()

        # Cálculo da porcentagem por gênero
        porcentagem_por_genero = {genero: (total / total_alcance) * 100 
                                  for genero, total in total_por_genero.items()}

        # Cálculo das somas de 'uniques' por faixa etária
        lista_idade = [20, 30, 40, 50, 60, 70, 80]
        df_idade = df[((df['class'].isnull()) & 
                       (df['location_id'].isnull()) & 
                       ~(df['gender_group'].isnull()) & 
                       (df['country'].isnull()) & 
                       (df['date'].isnull()) & 
                       ~(df['age_group'].isnull()) & 
                       (df['impression_hour'].isnull()) & 
                       (df['num_total_impressions'].isnull()) & 
                       (df['home'].isnull()))]

        total_por_idade = df_idade[(df_idade['age_group'].isin(lista_idade)) & 
                                   (df_idade['gender_group'] != 'U')].groupby('age_group')['uniques'].sum().to_dict()

        # Cálculo da porcentagem por faixa etária
        porcentagem_por_idade = {idade: (total / total_alcance) * 100 
                                 for idade, total in total_por_idade.items()}

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
        tab1, tab2 = st.tabs(["Estatísticas Descritivas", "Cálculo de Target"])

        with tab1:
            st.header("Estatísticas Descritivas")
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
                genero_dict = {
                    'F': 'Feminino',
                    'M': 'Masculino'
                }
                st.write(f"{genero}: {porcentagem:.2f}%")

            # Exibir porcentagens por faixa etária
            st.subheader("Porcentagem por Faixa Etária")
            # Dicionário para mapear as idades às faixas desejadas
            faixas_etarias = {
                '20': '20-29',
                '30': '30-39',
                '40': '40-49',
                '50': '50-59',
                '60': '60-69',
                '70': '70-79',
                '80': '80+'
            }

            for idade, porcentagem in porcentagem_por_idade.items():
                faixa = faixas_etarias.get(idade, idade)
                st.write(f"{faixa}: {porcentagem:.2f}%")

        with tab2:
            # Espaço para calcular a composição
            st.header("Cálculo de Composição")
            selected_classes = st.multiselect(
                "Selecione as Classes Sociais",
                options=lista_classes,
            )
            selected_genders = st.multiselect(
                "Selecione os Gêneros",
                options=(genero_dict.values()),
            )
            selected_ages = st.multiselect(
                "Selecione as Faixas Etárias",
                options=list(faixas_etarias.values()),
            )

            # Calcular a soma das porcentagens selecionadas
            soma_porcentagem_classes = sum(porcentagem_por_classe[classe] for classe in selected_classes)
            soma_porcentagem_generos = sum(porcentagem_por_genero[genero] for genero, genero_faixa in genero_dict.items() if genero_faixa in selected_genders)
            soma_porcentagem_idades = sum(porcentagem_por_idade[idade] for idade, faixa in faixas_etarias.items() if faixa in selected_ages)

            # Calcular a composição
            composicao = soma_porcentagem_classes * soma_porcentagem_generos * soma_porcentagem_idades / 10000  # Dividido por 10000 para ajustar a porcentagem

            # Calcular o alcance no target (alcance*composicao)
            alcance_target = (composicao/100)*total_alcance

            #Calcular os impactos no target (impactos*composicao)
            impactos_target = (composicao/100)*total_impactos

            # Exibir o resultado da composição
            st.write(f"Composição Selecionada: {composicao:.2f}%")

            # Título para métricas
            st.header("Métricas")

            # Impactos
            st.subheader("Impactos")

            # Impactos gerais e impactos no target
            st.write(f"Impactos gerais: {round(total_impactos)}")
            st.write(f"Impactos no target: {round(impactos_target)}")

            # Alcance
            st.subheader("Alcance")
            
            # Alcance geral e alcance no target
            st.write(f"Alcance geral: {round(total_alcance)}")
            st.write(f"Alcance no target: {round(alcance_target)}")

        # Seção de Dados Processados e Downloads
        st.header("Download dos Arquivos Processados")        
        col1, col2 = st.columns([2,3])
        with col1:
            st.header("Dados Processados")
            st.dataframe(final_filtrado.head())

            st.download_button(
                label="💾 Baixar Arquivo Processado (CSV)",
                data=output_csv,
                file_name=processed_filename_csv,
                mime='text/csv',
            )
        with col2:
            st.download_button(
                label="💾 Baixar Arquivo Processado (Excel)",
                data=output_excel,
                file_name=processed_filename_xlsx,
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
        #st.map(data=final[['latitude', 'longitude']])

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os arquivos: {e}")
