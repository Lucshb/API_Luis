import streamlit as st
import folium
from streamlit_folium import st_folium
import time
import pandas as pd
import random
from datetime import datetime, timedelta

# Função para adicionar CSS personalizado
def adicionar_estilo():
    st.markdown("""
        <style>
        .stApp {
            background-color: #1E1E1E;
        }
        .stMarkdown h1, h2, h3, h4, h5, h6 {
            color: #F39C12;
        }
        .stMarkdown p {
            color: #ECF0F1;
        }
        .stButton button {
            background-color: #27AE60;
            color: white;
            border-radius: 12px;
        }
        .stButton button:hover {
            background-color: #1ABC9C;
        }
        iframe {
            height: 85vh;
            width: 100%;
        }
        .dataframe-container {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

# Função para gerar dados simulados
def gerar_dados_simulados():
    veiculos = ["ABC-1234", "XYZ-5678", "DEF-9012", "GHI-3456", "JKL-7890"]
    pontos_venda = [
        {"razaoSocial": "Posto Alpha", "endereco": {"municipio": "São Paulo", "uf": "SP", "latitude": -23.55052, "longitude": -46.633308}},
        {"razaoSocial": "Posto Beta", "endereco": {"municipio": "Rio de Janeiro", "uf": "RJ", "latitude": -22.906847, "longitude": -43.172896}},
        {"razaoSocial": "Posto Gamma", "endereco": {"municipio": "Belo Horizonte", "uf": "MG", "latitude": -19.916681, "longitude": -43.934493}},
        {"razaoSocial": "Posto Delta", "endereco": {"municipio": "Curitiba", "uf": "PR", "latitude": -25.428954, "longitude": -49.267137}},
        {"razaoSocial": "Posto Epsilon", "endereco": {"municipio": "Porto Alegre", "uf": "RS", "latitude": -30.034647, "longitude": -51.217658}}
    ]
    produtos = ["Diesel", "Gasolina", "Álcool"]
    
    registros = []
    for _ in range(10):  # Gerar 10 registros simulados
        veiculo = random.choice(veiculos)
        ponto_venda = random.choice(pontos_venda)
        produto = random.choice(produtos)
        quantidade = random.uniform(50, 200)  # Quantidade entre 50 e 200 litros
        valor_unitario = random.uniform(4.0, 6.0)  # Valor entre R$ 4,00 e R$ 6,00 por litro
        valor_total = quantidade * valor_unitario
        hodometro = random.randint(10000, 50000)  # Hodômetro entre 10.000 e 50.000 km
        
        # Gerar data/hora aleatória nos últimos 15 dias
        data_transacao = (datetime.now() - timedelta(days=random.randint(0, 15))).strftime('%Y-%m-%dT%H:%M:%S')
        
        registros.append({
            "veiculo": {"placa": veiculo},
            "dataTransacao": data_transacao,
            "hodometro": hodometro,
            "pontoVenda": ponto_venda,
            "items": [
                {
                    "nome": produto,
                    "quantidade": quantidade,
                    "valorUnitario": valor_unitario,
                    "valorTotal": valor_total
                }
            ]
        })
    
    return registros

# Função para verificar se já passaram 2 horas desde a última requisição
def horas_passadas_ultima_requisicao():
    ultimo_tempo = st.session_state.get('ultimo_tempo', None)
    if ultimo_tempo:
        tempo_atual = time.time()
        if (tempo_atual - ultimo_tempo) >= 7200:
            return True
        else:
            return False
    else:
        return True

# Função para criar uma tabela de relatório dos veículos com novos campos
def gerar_tabela_relatorio(dados):
    relatorio = []
    for registro in dados:
        veiculo = registro.get("veiculo", {}).get("placa", "Desconhecido")
        data_hora = registro.get("dataTransacao", "N/A")
        hodometro = registro.get("hodometro", "N/A")
        ponto_venda = registro.get("pontoVenda", {}).get("razaoSocial", "Desconhecido")
        endereco = registro.get("pontoVenda", {}).get("endereco", {})
        localizacao = f"{endereco.get('municipio', 'N/A')}, {endereco.get('uf', 'N/A')}"
        
        if "items" in registro:
            for item in registro["items"]:
                produto = item.get("nome", "N/A")
                quantidade = item.get("quantidade", "N/A")
                valor_unitario = item.get("valorUnitario", "N/A")
                valor_total = item.get("valorTotal", "N/A")

                relatorio.append({
                    "Placa": veiculo,
                    "Data/Hora": data_hora,
                    "Hodômetro": hodometro,
                    "Ponto de Venda": ponto_venda,
                    "Localização": localizacao,
                    "Produto": produto,
                    "Quantidade Abastecida": quantidade,
                    "Valor Unitário (R$)": valor_unitario,
                    "Faturamento Total (R$)": valor_total
                })
    
    df = pd.DataFrame(relatorio)
    df['Valor Unitário (R$)'] = df['Valor Unitário (R$)'].apply(lambda x: f'R${x:.2f}')
    df['Faturamento Total (R$)'] = df['Faturamento Total (R$)'].apply(lambda x: f'R${x:.2f}')
    
    return df

# Função principal do app
def main():
    st.set_page_config(layout="wide")
    adicionar_estilo()
    st.title("Localização dos Caminhões")

    # Debug: Exibir diretamente os dados simulados gerados
    st.subheader("Dados simulados gerados:")
    
    if 'dados' in st.session_state and not horas_passadas_ultima_requisicao():
        dados = st.session_state['dados']
    else:
        if horas_passadas_ultima_requisicao():
            dados = gerar_dados_simulados()
            st.session_state['dados'] = dados
            st.session_state['ultimo_tempo'] = time.time()
        else:
            dados = st.session_state.get('dados', [])

    # Exibindo os dados simulados diretamente no app para fins de debug
    st.write(dados)

    if dados:
        coordenadas = []
        for registro in dados:
            ponto_venda = registro.get("pontoVenda", {})
            endereco = ponto_venda.get("endereco", {})
            latitude = endereco.get("latitude", None)
            longitude = endereco.get("longitude", None)
            
            if latitude and longitude:
                coordenadas.append([latitude, longitude])

        if coordenadas:
            mapa = folium.Map(zoom_start=4, tiles="cartodb dark_matter")
            mapa.fit_bounds(coordenadas)

            for registro in dados:
                ponto_venda = registro.get("pontoVenda", {})
                data_transacao = registro.get("dataTransacao", {})
                endereco = ponto_venda.get("endereco", {})
                latitude = endereco.get("latitude", None)
                longitude = endereco.get("longitude", None)
                
                if latitude and longitude:
                    icon = folium.Icon(color='blue', icon='truck', prefix='fa')
                    popup_content = f"""
                    <div style="width: 300px; font-size: 14px;">
                        <b>Caminhão:</b> {registro.get('veiculo', {}).get('placa', 'Desconhecido')}<br>
                        <b>Data/Hora:</b> {registro.get('dataTransacao')}<br>
                        <b>Local:</b> {ponto_venda.get('razaoSocial', 'Desconhecido')}<br>
                        {endereco.get('municipio', '')}, {endereco.get('uf', '')}
                    </div>
                    """
                    folium.Marker(
                        [latitude, longitude],
                        popup=folium.Popup(popup_content, max_width=400),
                        icon=icon
                    ).add_to(mapa)

            st_folium(mapa, width='100%')

        df_relatorio = gerar_tabela_relatorio(dados)
        st.subheader("Relatório de Veículos e Abastecimentos")
        st.dataframe(df_relatorio, use_container_width=True)

    else:
        st.write("Nenhum dado disponível para exibir.")

if __name__ == "__main__":
    main()
