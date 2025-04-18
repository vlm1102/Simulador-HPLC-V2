import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simulador de HPLC - Dorflex", layout="centered")

st.title("🧪 Simulador de HPLC - Análise de Dorflex")
st.write("Ajuste os parâmetros cromatográficos e observe a separação dos componentes: dipirona, cafeína e orfenadrina.")

# Parâmetros controláveis pelo usuário
fluxo = st.slider("Fluxo da fase móvel (mL/min)", 0.5, 2.0, 1.0, 0.1)
temperatura = st.slider("Temperatura da coluna (°C)", 25, 40, 35, 1)
fase_movel = st.slider("Porcentagem de metanol na fase móvel (%)", 10, 90, 50, 5)

# Função para calcular o tempo de retenção e o width
def calcular_tempo_ret(composto, base_tr):
    fator_fluxo = 1 / fluxo
    fator_temp = 1 - ((temperatura - 35) * 0.01)
    fator_fase = 1 + ((fase_movel - 50) * 0.02 if composto != "dipirona" else (fase_movel - 50) * -0.015)
    return base_tr * fator_fluxo * fator_temp * fator_fase

# Função para calcular o width do pico (largura)
def calcular_width(fluxo):
    # A largura do pico depende do fluxo e pode ser ajustada com base nos dados de literatura
    return 0.3 + (fluxo * 0.1)

tempos_ret = {
    "Dipirona": calcular_tempo_ret("dipirona", 2.0),
    "Cafeína": calcular_tempo_ret("cafeina", 4.0),
    "Orfenadrina": calcular_tempo_ret("orfenadrina", 6.0)
}

# Criar cromatograma com picos gaussianos
tempo = np.linspace(0, 20, 1000)  # Tempo agora vai até 20 minutos
sinal_total = np.zeros_like(tempo)

cores = {'Dipirona': 'blue', 'Cafeína': 'green', 'Orfenadrina': 'red'}
widths = {composto: calcular_width(fluxo) for composto in tempos_ret}

# Calcular picos
for composto, tr in tempos_ret.items():
    largura = widths[composto]  # Largura do pico ajustada para cada substância
    altura = 1.0
    pico = altura * np.exp(-((tempo - tr) ** 2) / (2 * largura ** 2))
    sinal_total += pico

# Gráfico do cromatograma
fig, ax = plt.subplots()

for composto, tr in tempos_ret.items():
    largura = widths[composto]
    ax.plot(tempo, np.exp(-((tempo - tr) ** 2) / (2 * largura ** 2)), label=f'{composto} (tR={tr:.2f} min)', color=cores[composto])

# Adicionar o sinal combinado
ax.plot(tempo, sinal_total, 'k--', alpha=0.4, label='Sinal combinado')

# Informações na legenda
ax.set_xlabel("Tempo (min)")
ax.set_ylabel("Intensidade")
ax.set_title("Cromatograma Simulado")
ax.legend(bbox_to_anchor=(0.5, -0.1), loc='upper center', ncol=3)  # Mover a legenda para baixo

# Tabela de informações sobre os picos
informacoes_picos = []
for composto, tr in tempos_ret.items():
    largura = widths[composto]
    tempo_inicio = tr - 3 * largura  # Tempo onde o pico começa
    tempo_fim = tr + 3 * largura  # Tempo onde o pico termina
    informacoes_picos.append({
        'Composto': composto,
        'Tempo de Retenção (tR)': f'{tr:.2f} min',
        'Largura (Width)': f'{largura:.2f} min',
        'Início do Pico': f'{tempo_inicio:.2f} min',
        'Fim do Pico': f'{tempo_fim:.2f} min'
    })

# Exibir a tabela com as informações dos picos
st.write("### Informações dos Picos:")
st.write("A tabela abaixo mostra os tempos de retenção, largura e tempos de início e fim dos picos.")
st.table(informacoes_picos)

# Mostrar o gráfico no Streamlit
st.pyplot(fig)
