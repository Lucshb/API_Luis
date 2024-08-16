import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import time

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
            st.warning("Aguarde até 2 horas desde a última requisição.")
            return False
    else:
        return True

# Função principal do app
def main():
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
        mapa = folium.Map(location=[-15.7934036, -47.8823172], zoom_start=4)

        for registro in dados:
            ponto_venda = registro.get("pontoVenda", {})
            data_transacao = registro.get("dataTransacao", {})
            endereco = ponto_venda.get("endereco", {})
            latitude = endereco.get("latitude", None)
            longitude = endereco.get("longitude", None)
            
            if latitude and longitude:
                folium.Marker(
                    [latitude, longitude],
                    popup=f"Caminhão: {registro.get('veiculo', {}).get('placa', 'Desconhecido')}<br>"
                          f"Data/Hora: {registro.get('dataTransacao')}<br>"
                          f"Local: {ponto_venda.get('razaoSocial', 'Desconhecido')}<br>"
                          f"{endereco.get('municipio', '')}, {endereco.get('uf', '')}"
                ).add_to(mapa)
        
        st_folium(mapa, width=700, height=500)
    else:
        st.write("Nenhum dado disponível para exibir.")

# Executa a função principal
if __name__ == "__main__":
    main()
