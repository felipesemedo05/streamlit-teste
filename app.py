import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np
import os

# Função para criar o mapa com Folium
def criar_mapa_folium(df, coluna_cor, cor_inicial, cor_final):
    # Cria um mapa centrado na média dos dados
    m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=10)

    # Normaliza os valores da coluna de cor para o intervalo [0, 1]
    valores = df[coluna_cor].fillna(0).astype(float)
    min_val, max_val = valores.min(), valores.max()
    df['normalized_color'] = (valores - min_val) / (max_val - min_val)
    
    # Define a paleta de cores
    cor_inicial_rgb = [int(cor_inicial[i:i+2], 16) for i in (1, 3, 5)]
    cor_final_rgb = [int(cor_final[i:i+2], 16) for i in (1, 3, 5)]
    
    for _, row in df.iterrows():
        cor_normalizada = [int(cor_inicial_rgb[i] + (cor_final_rgb[i] - cor_inicial_rgb[i]) * row['normalized_color']) for i in range(3)]
        cor_hex = '#{:02x}{:02x}{:02x}'.format(*cor_normalizada)
        
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=5,
            color=cor_hex,
            fill=True,
            fill_color=cor_hex,
            fill_opacity=0.8,
            popup=f"ID: {row['location_id']}<br>{coluna_cor}: {row[coluna_cor]}"
        ).add_to(m)

    return m

# Interface do Streamlit
st.set_page_config(page_title='Processamento de Arquivo', layout='wide')

st.title('Processamento de Arquivo CSV e Parquet')

# Upload do arquivo CSV ou Parquet
uploaded_file = st.file_uploader("Escolha um arquivo CSV ou Parquet para o dataset principal", type=["csv", "parquet"])

if uploaded_file is not None:
    try:
        original_filename = os.path.splitext(uploaded_file.name)[0]  # Pega o nome sem a extensão

        claro_path = 'claro.csv'  # Atualize com o caminho do seu arquivo
        claro = pd.read_csv(claro_path, encoding='latin-1')

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

        if 'start_date' in df.columns and 'end_date' in df.columns:
            df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
            df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')
            
            if not df['start_date'].dropna().empty and not df['end_date'].dropna().empty:
                start_date = df['start_date'].dropna().iloc[0]
                end_date = df['end_date'].dropna().iloc[0]
                dias = (end_date - start_date).days + 1
                periodo_info = f"Período do arquivo: {start_date.strftime('%Y-%m-%d')} até {end_date.strftime('%Y-%m-%d')} ({dias} dias)"
            else:
                periodo_info = "Não há datas válidas no arquivo."
        else:
            periodo_info = "Colunas 'start_date' e/ou 'end_date' não encontradas no arquivo."

        final = processar_arquivo(df, claro)

        unique_location_ids = final['location_id'].nunique()

        output_csv = BytesIO()
        output_excel = BytesIO()

        processed_filename_csv = f"{original_filename}_processado_{datetime.now().strftime('%Y-%m-%d')}.csv"
        processed_filename_xlsx = f"{original_filename}_processado_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

        final.to_csv(output_csv, index=False)
        output_csv.seek(0)

        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            final.to_excel(writer, index=False, sheet_name='Dados Processados')
        output_excel.seek(0)

        col1, col2 = st.columns([2, 3])

        with col1:
            st.header("Estatísticas Descritivas")
            st.write(periodo_info)
            st.write(f"Quantidade de location_id: {unique_location_ids}")

            if 'impressions' in df.columns:            
                st.subheader("Estatísticas de 'impressions'")
                impressions_describe = round(final['impressions'].describe(), 2).to_dict()
                st.write(impressions_describe)

            if 'uniques' in df.columns:
                st.subheader("Estatísticas de 'uniques'")
                uniques_describe = round(final['uniques'].describe(), 2).to_dict()
                st.write(uniques_describe)

        with col2:
            st.header("Dados Processados")
            st.dataframe(final.head())

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

        st.header("Mapa Interativo")

        coluna_cor = st.selectbox("Escolha a coluna para colorir", options=[col for col in final.columns if col not in ['location_id', 'latitude', 'longitude']])
        
        cor_inicial = st.color_picker("Escolha a cor inicial da paleta", "#FFFFFF")
        cor_final = st.color_picker("Escolha a cor final da paleta", "#FF0000")

        mapa = criar_mapa_folium(final, coluna_cor, cor_inicial, cor_final)
        st_folium(mapa, width=700, height=500)

        st.write(f"Legenda da cor baseada em: {coluna_cor}")
        st.write(f"Cor inicial: {cor_inicial}, Cor final: {cor_final}")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
