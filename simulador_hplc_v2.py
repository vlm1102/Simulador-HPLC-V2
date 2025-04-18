# simulador_hplc.py

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simulador de HPLC - Dorflex", layout="centered")

st.title("🧪 Simulador de HPLC - Análise de Dorflex")
st.write("Ajuste os parâmetros cromatográficos e observe a separação dos componentes: dipirona, cafeína e orfenadrina.")

# Parâmetros controláveis pelo usuário
fluxo = st.slider("Fluxo da fase móvel (mL/min)", 0.5, 2.0, 1.0, 0.1)
temperatura = st.slider("Temperatura da coluna (°C)", 25, 40, 35, 1)  # Faixa ajustada para 25 a 40°C
fase_movel = st.slider("Porcentagem de metanol na fase móvel (%)", 10, 90, 50, 5)

# Simulação de tempos de retenção (didático)
def calcular_tempo_ret(composto, base_tr):
    fator_fluxo = 1 / fluxo
    fator_temp = 1 - ((temperatura - 35) * 0.01)
    fator_fase = 1 + ((fase_movel - 50) * 0.02 if composto != "dipirona" else (fase_movel - 50) * -0.015)
    return base_tr * fator_fluxo * fator_temp * fator_fase

tempos_ret = {
    "Dipirona": calcular_tempo_ret("dipirona", 2.0),
    "Cafeína": calcular_tempo_ret("cafeina", 4.0),
    "Orfenadrina": calcular_tempo_ret("orfenadrina", 6.0)
}

# Criar cromatograma com picos gaussianos
tempo = np.linspace(0, 20, 2000)  # Intervalo de 0 a 20 minutos, com mais pontos para suavidade
sinal_total = np.zeros_like(tempo)

cores = {'Dipirona': 'blue', 'Cafeína': 'green', 'Orfenadrina': 'red'}

for composto, tr in tempos_ret.items():
    altura = 1.0
    largura = 0.3 + (fluxo * 0.1)
    pico = altura * np.exp(-((tempo - tr) ** 2) / (2 * largura ** 2))
    sinal_total += pico
    plt.plot(tempo, pico, label=f'{composto} (tR={tr:.2f} min)', color=cores[composto])

plt.plot(tempo, sinal_total, 'k--', alpha=0.4, label='Sinal combinado')
plt.xlabel("Tempo (min)")
plt.ylabel("Intensidade")
plt.title("Cromatograma Simulado")
plt.xlim(0, 20)  # Garante que o eixo X vai até 20 minutos
plt.legend()

st.pyplot(plt)
