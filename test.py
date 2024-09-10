import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import time
import pandas as pd

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
        /* Ajusta o mapa para ocupar toda a largura e altura disponíveis */
        iframe {
            height: 85vh;
            width: 100%;
        }
        /* Ajusta a tabela para ocupar toda a largura da página */
        .dataframe-container {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

# Função para buscar os dados da API
def obter_dados():
    url = "http://api-portal.profrotas.com.br/api/frotista/abastecimento/pesquisa"
    headers = {
        "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c3VhcmlvLmZyb3RhIjozNzU0LCJ0b2tlbi50aXBvIjoiQVBJX0ZST1RJU1RBIiwidG9rZW4udmVyc2FvIjoiUC0wMDAyIiwiaXNzIjoiQm9sZWlhIiwidG9rZW4uZGF0YUdlcmFjYW8iOjE3MjM3NjI2MTcsInVzdWFyaW8ucGVybWlzc29lcyI6WyJBUElfRlJPVElTVEEiXSwiZXhwIjoxNzI2MzU0NjE3LCJ1c3VhcmlvLmlkIjotMzk1NDU5MDYxMjg1NzczNzMwOSwidXN1YXJpby5ub21lIjoiVHJhbnNwb3J0YWRvcmEgRGFuZ2xhcmVzIER1YXJ0ZSBMdGRhIiwidXN1YXJpby50aXBvIjoiRlJPVEEiLCJ0b2tlbi5jb250YWRvclJlbm92YWNvZXMiOjB9.Mr0kTwIU3rNmb9eRseZwGGXOezKyUASuzhvu4xQsrqo",
        "Content-Type": "application/json"
    }
    data = {
        "pagina": 1,
        "dataInicial": "2024-08-01T00:00:00Z",
        "dataFinal": "2024-08-15T23:59:59Z"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json().get("registros", [])
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            st.error("Erro 429: Muitas requisições. Aguardando para tentar novamente...")
            time.sleep(60)  # Aguarda 60 segundos antes de tentar novamente
            return obter_dados()  # Tenta novamente
        else:
            st.error(f"Erro ao obter dados: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Erro ao obter dados: {str(e)}")
        return []

# Função para verificar se já passaram 2 horas desde a última requisição
def horas_passadas_ultima_requisicao():
    ultimo_tempo = st.session_state.get('ultimo_tempo', None)
    if ultimo_tempo:
        tempo_atual = time.time()
        # 2 horas = 7200 segundos
        if (tempo_atual - ultimo_tempo) >= 7200:
            return True
        else:
            return False  # Remove o aviso visual duplicado
    else:
        return True

# Função para criar uma tabela de relatório dos veículos
def gerar_tabela_relatorio(dados):
    relatorio = []
    for registro in dados:
        veiculo = registro.get("veiculo", {}).get("placa", "Desconhecido")
        data_hora = registro.get("dataTransacao", "N/A")
        ponto_venda = registro.get("pontoVenda", {}).get("razaoSocial", "Desconhecido")
        endereco = registro.get("pontoVenda", {}).get("endereco", {})
        localizacao = f"{endereco.get('municipio', 'N/A')}, {endereco.get('uf', 'N/A')}"

        relatorio.append({
            "Placa": veiculo,
            "Data/Hora": data_hora,
            "Ponto de Venda": ponto_venda,
            "Localização": localizacao
        })
    
    df = pd.DataFrame(relatorio)
    return df

# Função principal do app
def main():
    # Define o layout para tela cheia
    st.set_page_config(layout="wide")

    # Chama a função para aplicar o estilo
    adicionar_estilo()

    # Título estilizado
    st.title("Localização dos Caminhões")

    # Se ainda não foram passadas 2 horas e já temos dados, usamos os dados anteriores
    if 'dados' in st.session_state and not horas_passadas_ultima_requisicao():
        dados = st.session_state['dados']
    else:
        # Se já passaram 2 horas ou não temos dados armazenados, faz a requisição
        if horas_passadas_ultima_requisicao():
            dados = obter_dados()
            st.session_state['dados'] = dados  # Armazena os dados na sessão
            st.session_state['ultimo_tempo'] = time.time()  # Atualiza o tempo da última requisição
        else:
            dados = st.session_state.get('dados', [])  # Usa os dados existentes, se disponíveis

    if dados:
        # Cria o mapa com tema escuro
        mapa = folium.Map(location=[-15.7934036, -47.8823172], zoom_start=4, tiles="cartodb dark_matter")

        for registro in dados:
            ponto_venda = registro.get("pontoVenda", {})
            data_transacao = registro.get("dataTransacao", {})
            endereco = ponto_venda.get("endereco", {})
            latitude = endereco.get("latitude", None)
            longitude = endereco.get("longitude", None)
            
            if latitude and longitude:
                # Ícone personalizado para o caminhão
                icon = folium.Icon(color='blue', icon='truck', prefix='fa')
                
                # HTML personalizado para o popup com largura aumentada
                popup_content = f"""
                <div style="width: 300px; font-size: 14px;">
                    <b>Caminhão:</b> {registro.get('veiculo', {}).get('placa', 'Desconhecido')}<br>
                    <b>Data/Hora:</b> {registro.get('dataTransacao')}<br>
                    <b>Local:</b> {ponto_venda.get('razaoSocial', 'Desconhecido')}<br>
                    {endereco.get('municipio', '')}, {endereco.get('uf', '')}
                </div>
                """
                
                # Cria o popup com tamanho ajustado
                folium.Marker(
                    [latitude, longitude],
                    popup=folium.Popup(popup_content, max_width=400),  # Aumenta o tamanho do popup
                    icon=icon
                ).add_to(mapa)
        
        # Exibe o mapa com as novas dimensões
        st_folium(mapa, width='100%')

        # Gera a tabela de relatório abaixo do mapa
        df_relatorio = gerar_tabela_relatorio(dados)
        st.subheader("Relatório de Veículos")
        
        # Usar st.dataframe para interatividade e ajuste automático
        st.dataframe(df_relatorio, use_container_width=True)

    else:
        st.write("Nenhum dado disponível para exibir.")

# Executa a função principal
if __name__ == "__main__":
    main()
