import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
import regex as re
from datetime import datetime
from io import BytesIO
import openpyxl
import matplotlib.pyplot as plt
import json
from keplergl import KeplerGl
import seaborn as sns

# Função para aplicar as transformações

# Função para processar a coluna 'location_id'
def process_location_id(x):
    # Encontra todos os números na string
    numbers = re.findall(r'\d+', x)
    # Junta todos os números em uma única string
    num_str = ''.join(numbers)
    # Verifica se a string resultante tem exatamente 5 dígitos
    if len(num_str) == 5:
        return num_str
    else:
        # Se tiver menos que 5 dígitos, retorna o valor original
        return x
        
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

    # Aplica a função na coluna 'location_id'
    df1['location_id'] = df1['location_id'].apply(process_location_id)

    final = df1.merge(claro, on='location_id')

    # Excluir colunas totalmente vazias
    final = final.dropna(axis=1, how='all')

    return final

# Interface do Streamlit
st.set_page_config(page_title='Processamento de Arquivo', layout='wide')

# Título
#st.title('Processamento de Análise da Claro')

col1, col2, col3 = st.columns([4, 1, 1])
with col1:
    st.image("eletro.png", width=250)

with col1:
    st.title('Processamento de Análise da Claro')

# Conteúdo restant

# Upload do arquivo CSV ou Parquet
uploaded_file = st.file_uploader("Escolha um arquivo CSV ou Parquet para o dataset principal", type=["csv", "parquet"])

if uploaded_file is not None:
    try:
        # Obter o nome do arquivo enviado
        original_filename = os.path.splitext(uploaded_file.name)[0]

        # Leitura do arquivo claro diretamente do computador
        claro_path = 'claro.csv'  # Atualize com o caminho do seu arquivo
        claro = pd.read_csv(claro_path, encoding='latin-1', low_memory=False)

        # Leitura do arquivo CSV ou Parquet do dataset principal
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, encoding='latin-1', low_memory=False)
        elif uploaded_file.name.endswith('.parquet'):
            df = pd.read_parquet(uploaded_file, low_memory=False)
        
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
        
        # Processamento do arquivo
        final = processar_arquivo(df, claro)

        # Criar coluna frequência
        final['frequencia'] = round(final['impressions']/final['uniques'], 2)

        # Criar uma lista das colunas preenchidas (não vazias)
        colunas_preenchidas = final.columns.tolist()

        colunas_padrao = ['location_id', 'impressions', 'uniques']

        # Abas para Navegação
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Ponto a Ponto", 
                                                    "Estatísticas Descritivas",
                                                    "Visualização Mapa",
                                                    "Métricas por Data",
                                                    "Gráficos",
                                                    "Tratamento JSON",
                                                    "KeplerGL"])

        with tab1:
            st.header("Ponto a Ponto")
            st.write("Seleção de Colunas para Download:")
            colunas_selecionadas = st.multiselect(
                "Escolha as colunas que deseja incluir no download:",
                options=colunas_preenchidas,
                default=colunas_padrao
            )

            # Filtrar o DataFrame com base nas colunas selecionadas
            final_filtrado = final[colunas_selecionadas]
            st.dataframe(final_filtrado)

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

            st.download_button(
                label="📁 Baixar CSV Processado",
                data=output_csv,
                file_name=processed_filename_csv,
                mime="text/csv"
            )

            st.download_button(
                label="📁 Baixar Excel Processado",
                data=output_excel,
                file_name=processed_filename_xlsx,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with tab2:
            st.header("Estatísticas Descritivas")
            col1, col2 = st.columns(2)
            col3, col4 = st.columns(2)

            with col1:
                st.write(f"Quantidade de location_id: {final['location_id'].nunique()}")
                st.write(periodo_info)

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
                # Cálculo do total de alcance
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

            with col2:
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

                total_por_genero = df_genero[(df_genero['gender_group'].isin(lista_genero))].groupby('gender_group')['uniques'].sum().to_dict()

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

                total_por_idade = df_idade[(df_idade['age_group'].isin(lista_idade))].groupby('age_group')['uniques'].sum().to_dict()

                # Cálculo da porcentagem por faixa etária
                porcentagem_por_idade = {idade: (total / total_alcance) * 100 
                                        for idade, total in total_por_idade.items()}
            with col3:
                if 'impressions' in final.columns:
                    st.subheader("Estatísticas de 'impressions'")
                    impressions_describe = round(final['impressions'].describe(),2)
                    st.write(f"Contagem: {impressions_describe['count']}")
                    st.write(f"Média: {impressions_describe['mean']:.2f}")
                    st.write(f"Desvio Padrão: {impressions_describe['std']:.2f}")
                    st.write(f"Mínimo: {impressions_describe['min']}")
                    st.write(f"25º Percentil: {impressions_describe['25%']}")
                    st.write(f"Mediana (50º Percentil): {impressions_describe['50%']}")
                    st.write(f"75º Percentil: {impressions_describe['75%']}")
                    st.write(f"Máximo: {impressions_describe['max']}")

                if 'uniques' in final.columns:
                    st.subheader("Estatísticas de 'uniques'")
                    uniques_describe = round(final['uniques'].describe(), 2)
                    st.write(f"Contagem: {uniques_describe['count']}")
                    st.write(f"Média: {uniques_describe['mean']:.2f}")
                    st.write(f"Desvio Padrão: {uniques_describe['std']:.2f}")
                    st.write(f"Mínimo: {uniques_describe['min']}")
                    st.write(f"25º Percentil: {uniques_describe['25%']}")
                    st.write(f"Mediana (50º Percentil): {uniques_describe['50%']}")
                    st.write(f"75º Percentil: {uniques_describe['75%']}")
                    st.write(f"Máximo: {uniques_describe['max']}")
            with col4:
                st.subheader('Alcance')
                st.write(f'{total_alcance}')
                st.subheader('Impactos')
                st.write(f'{total_impactos}')
            
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
                    faixa_genero = genero_dict.get(genero, genero)
                    st.write(f"{faixa_genero}: {porcentagem:.2f}%")

                # Exibir porcentagens por faixa etária
                st.subheader("Porcentagem por Faixa Etária")
                faixas_etarias = {
                    20: '20-29',
                    30: '30-39',
                    40: '40-49',
                    50: '50-59',
                    60: '60-69',
                    70: '70-79',
                    80: '80+'
                }
                for idade, porcentagem in porcentagem_por_idade.items():
                    faixa = faixas_etarias.get(idade, idade)
                    st.write(f"{faixa}: {porcentagem:.2f}%")
        with tab3:
            st.header('Visualização dos pontos em um Mapa')
            st.write('Para visualizar no mapa, necessita das colunas "Latitude" e "Longitude"')
            st.map(final[['latitude', 'longitude']])
        with tab4:
                st.header('Métricas por cada dia')
                st.write(periodo_info)
                df_data = df[((df['class'].isnull()) & 
                                ~(df['location_id'].isnull()) & 
                                (df['gender_group'].isnull()) & 
                                (df['country'].isnull()) & 
                                ~(df['date'].isnull()) & 
                                (df['age_group'].isnull()) & 
                                (df['impression_hour'].isnull()) & 
                                (df['num_total_impressions'].isnull()) & 
                                (df['home'].isnull()))]
                
                # Tratar o dataframe de data
                df_data_filtrado = df_data[['location_id', 'impressions', 'uniques', 'date']]

                # Transformar em data
                df_data_filtrado['date'] = pd.to_datetime(df_data_filtrado['date'])
                df_data_filtrado = df_data_filtrado.sort_values('date')

                # Aplica a função na coluna 'location_id'
                df_data_filtrado['location_id'] = df_data_filtrado['location_id'].apply(process_location_id)

                # Mostra o dataframe
                st.dataframe(df_data_filtrado)

                # Criar buffers para arquivos
                output_csv = BytesIO()
                output_excel = BytesIO()

                # Definir o nome do arquivo processado CSV
                processed_filename_csv = f"{original_filename}_processado_{datetime.now().strftime('%Y-%m-%d')} por data.csv"

                # Definir o nome do arquivo processado EXCEL
                processed_filename_xlsx = f"{original_filename}_processado_{datetime.now().strftime('%Y-%m-%d')} por data.xlsx"

                # Criar o CSV
                df_data_filtrado.to_csv(output_csv, index=False)
                output_csv.seek(0)

                # Criar o Excel
                with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                    df_data_filtrado.to_excel(writer, index=False, sheet_name='Dados Processados')
                output_excel.seek(0)

                st.download_button(
                    label="📁 Baixar CSV Processado",
                    data=output_csv,
                    file_name=processed_filename_csv,
                    mime="text/csv"
                )

                st.download_button(
                    label="📁 Baixar Excel Processado",
                    data=output_excel,
                    file_name=processed_filename_xlsx,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )                       
        with tab5:
            # Supondo que os dados já estejam carregados e processados, como mostrado anteriormente.
            st.header("Gráficos")

            # Criação de colunas para exibir gráficos lado a lado
            col1, col2 = st.columns(2)

            # Gráfico de Classe Social
            with col1:
                st.subheader("Distribuição por Classe Social")
                classe_df = pd.DataFrame(list(porcentagem_por_classe.items()), columns=['Classe Social', 'Porcentagem'])
                fig_classe = px.bar(classe_df, x='Classe Social', y='Porcentagem',
                                labels={'Porcentagem': 'Porcentagem (%)'},
                                title="Distribuição de Porcentagem por Classe Social")
                fig_classe.update_layout(height=300, width=400)  # Ajusta o tamanho do gráfico
                st.plotly_chart(fig_classe, use_container_width=True)

            # Gráfico de Faixa Etária
            with col1:
                st.subheader("Distribuição por Faixa Etária")
                idade_df = pd.DataFrame(list(porcentagem_por_idade.items()), columns=['Faixa Etária', 'Porcentagem'])
                idade_df['Faixa Etária'] = idade_df['Faixa Etária'].map(faixas_etarias)
                fig_idade = px.bar(idade_df, x='Faixa Etária', y='Porcentagem',
                                labels={'Porcentagem': 'Porcentagem (%)'},
                                title="Distribuição de Porcentagem por Faixa Etária")
                fig_idade.update_layout(height=300, width=400)  # Ajusta o tamanho do gráfico
                st.plotly_chart(fig_idade, use_container_width=True)

            # Gráfico de Gênero como pizza
            with col2:
                st.subheader("Distribuição por Gênero")
                genero_df = pd.DataFrame(list(porcentagem_por_genero.items()), columns=['Gênero', 'Porcentagem'])
                genero_df['Gênero'] = genero_df['Gênero'].map({'F': 'Feminino', 'M': 'Masculino'})
                fig_genero = px.pie(genero_df, names='Gênero', values='Porcentagem',
                                title="Distribuição de Porcentagem por Gênero",
                                labels={'Porcentagem': 'Porcentagem (%)'})
                fig_genero.update_layout(height=300, width=400)  # Ajusta o tamanho do gráfico
                st.plotly_chart(fig_genero, use_container_width=True)

            # Gráfico da Distribuição de 'uniques' por Frequência
            with col2:
                st.subheader("Distribuição de 'uniques' por Frequência")
                fig_uniques = px.histogram(df, x='uniques', nbins=30, title="Distribuição de 'uniques'",
                                        labels={'uniques': "Número de 'uniques'"})
                fig_uniques.update_layout(height=300, width=400)  # Ajusta o tamanho do gráfico
                st.plotly_chart(fig_uniques, use_container_width=True)

            # Gráfico combinado de Impressions e Uniques por Data com marcadores
            st.subheader("Impressions e Uniques por Data")
            df_impressions = df_data_filtrado.groupby('date')['impressions'].sum().reset_index()
            df_uniques = df_data_filtrado.groupby('date')['uniques'].sum().reset_index()
            
            fig_combined = go.Figure()

            # Linha para Impressions
            fig_combined.add_trace(go.Scatter(x=df_impressions['date'], y=df_impressions['impressions'],
                                            mode='lines+markers',
                                            name='Impressions',
                                            line=dict(color='blue'),
                                            marker=dict(symbol='circle', color='blue')))

            # Linha para Uniques
            fig_combined.add_trace(go.Scatter(x=df_uniques['date'], y=df_uniques['uniques'],
                                            mode='lines+markers',
                                            name='Uniques',
                                            line=dict(color='red'),
                                            marker=dict(symbol='circle', color='red')))
            
            fig_combined.update_layout(title="Impressions e Uniques por Data",
                                    xaxis_title="Data",
                                    yaxis_title="Valores",
                                    legend_title="Legenda",
                                    template='plotly_white',
                                    height=400, width=800)  # Ajusta o tamanho do gráfico

            st.plotly_chart(fig_combined, use_container_width=True)
        with tab6:
            # Função principal
            def main():
                st.title("Processador de Dicionário para Impactos e Alcance")

                # Instruções
                st.write("Insira o dicionário com os dados de `impressions`, `unique_devices`, `uniques_by_age_and_gender` e `uniques_by_social_class`.")

                # Entrada de dicionário
                st.subheader("Cole o dicionário Python:")
                dict_input = st.text_area("Cole aqui o dicionário", height=150)

                # Verifica se o dicionário foi fornecido
                if dict_input:
                    try:
                        # Tenta converter a entrada para um dicionário Python
                        response = eval(dict_input)

                        # Validação básica do dicionário
                        if 'data' not in response or \
                        'impressions' not in response['data'] or \
                        'unique_devices' not in response['data'] or \
                        'uniques_by_age_and_gender' not in response['data'] or \
                        'uniques_by_social_class' not in response['data']:
                            st.error("O dicionário fornecido não possui as chaves esperadas. Verifique a estrutura do dicionário.")
                        else:
                            # Extração de dados do dicionário
                            try:
                                impactos = response['data']['impressions']['data'][0]['total_trips']
                                alcance_geral = response['data']['unique_devices']['data'][0]['uniques']
                                data = response['data']['uniques_by_age_and_gender']['data']
                                df = pd.DataFrame(data)

                                # Exibir os dados extraídos
                                st.subheader("Dados Extraídos:")
                                st.write(f"Impactos: {round(impactos)}")
                                st.write(f"Alcance Geral: {round(alcance_geral)}")

                                # Opções de filtros
                                todas_idades = ['Todos', '18-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+']
                                todos_generos = ['AS', 'F', 'M']
                                todas_classes = ['A', 'B1', 'B2', 'C1', 'C2', 'DE']

                                # Filtros dinâmicos com a opção de "Selecionar Todos"
                                st.subheader("Filtros")
                                
                                # Filtro por idade
                                age_filter = st.multiselect("Selecione as idades", options=todas_idades)
                                if 'Todos' in age_filter:
                                    age_filter = todas_idades[1:]  # Exclui o 'Todos' da lista

                                # Filtro por gênero
                                gender_filter = st.multiselect("Selecione o gênero", options=todos_generos)
                                if 'AS' in gender_filter:
                                    gender_filter = todos_generos[1:]  # Exclui o 'Todos' da lista

                                # Filtro por classe social
                                class_filter = st.multiselect("Selecione as classes sociais", options=todas_classes)
                                if 'Todos' in class_filter:
                                    class_filter = todas_classes[1:]  # Exclui o 'Todos' da lista

                                # Aplicando os filtros
                                df_filtered = df[(df['age'].isin(age_filter)) & (df['gender'].isin(gender_filter))]

                                total_idades = df_filtered.uniques.sum()
                                total_genero = df[~(df['gender'] == 'U') & (df['age'] != 'Unknown')].uniques.sum()
                                total_generoidade = df[(df['gender'] != 'U') & (df['age'] != 'Unknown')].uniques.sum()

                                # Calculando métricas de gênero, idade e classes
                                final_genero = total_genero / total_generoidade
                                final_idade = total_idades / total_generoidade

                                # Classe social
                                data_class = response['data']['uniques_by_social_class']['data']
                                df_classe = pd.DataFrame(data_class)
                                total_classes = df_classe[df_classe['social_class'].isin(todas_classes[1:])].uniques.sum()  # Exclui 'Todos'
                                total_filtro_classes = df_classe[df_classe['social_class'].isin(class_filter)].uniques.sum()
                                final_classes = total_filtro_classes / total_classes

                                # Cálculo final
                                comp = final_genero * final_idade * final_classes
                                alcance_target = comp * alcance_geral
                                impactos_target = comp * impactos

                                # Cálculo final
                                comp = final_genero * final_idade * final_classes
                                alcance_target = comp * alcance_geral
                                impactos_target = comp * impactos

                                # Exibir resultados finais
                                st.subheader("Resultados Finais")
                                st.write(f"Composicao: {round(comp, 2)}")
                                st.write(f"Alcance Target: {round(alcance_target)}")
                                st.write(f"Impactos Target: {round(impactos_target)}")

                            except KeyError as e:
                                st.error(f"Erro ao processar o dicionário: chave ausente {e}")

                    except SyntaxError:
                        st.error("O texto fornecido não é um dicionário Python válido. Verifique a formatação.")
                    except Exception as e:
                        st.error(f"Erro inesperado: {e}")
                        
            # Rodando o aplicativo Streamlit
            if __name__ == "__main__":
                main()
        with tab7:
            # Gerar o mapa no Kepler.gl
            mapa = KeplerGl()
            mapa.add_data(data=final, name="Cidades Brasileiras")

            # Salvar o mapa em um arquivo HTML
            html_file = 'mapa_kepler.html'
            mapa.save_to_html(file_name=html_file)

            # Exibir um link clicável para abrir o mapa
            st.title("Mapa Interativo com Kepler.gl")
            st.write("Clique no link abaixo para abrir o mapa interativo gerado com Kepler.gl:")
            map_url = f"./{html_file}"

            # Criar um link clicável no Streamlit
            if os.path.exists(html_file):
                st.markdown(html_file)
            else:
                st.error("Erro: O arquivo do mapa não foi encontrado.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")