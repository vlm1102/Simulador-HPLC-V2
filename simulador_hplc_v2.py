import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.animation import FuncAnimation
import io
from fpdf import FPDF
import base64

st.set_page_config(page_title="Simulador de HPLC - Dorflex", layout="centered")

st.title("🧪 Simulador de HPLC - Análise de Dorflex")

st.write("Ajuste os parâmetros cromatográficos e observe a separação dos componentes: dipirona, cafeína e orfenadrina.")

fluxo = st.slider("Fluxo da fase móvel (mL/min)", 0.5, 2.0, 1.0, 0.1)
temperatura = st.slider("Temperatura da coluna (°C)", 25, 40, 35, 1)
fase_movel = st.slider("Porcentagem de metanol na fase móvel (%)", 10, 90, 50, 5)

# Função para calcular o tempo de retenção
def calcular_tempo_ret(composto, base_tr):
    fator_fluxo = 1 / fluxo
    fator_temp = 1 - ((temperatura - 35) * 0.01)
    fator_fase = 1 + ((fase_movel - 50) * 0.02 if composto != "dipirona" else (fase_movel - 50) * -0.015)
    return base_tr * fator_fluxo * fator_temp * fator_fase

# Configuração base
tr_bases = {"Dipirona": 2.0, "Cafeína": 4.0, "Orfenadrina": 6.0}

tempos_ret = {comp: calcular_tempo_ret(comp, tr) for comp, tr in tr_bases.items()}

# Dados para o gráfico
tempo = np.linspace(0, 20, 2000)
sinal_total = np.zeros_like(tempo)

cores = {'Dipirona': 'blue', 'Cafeína': 'green', 'Orfenadrina': 'red'}
resultados = []

# Preparar figura e eixos
temp_fig, temp_ax = plt.subplots()
temp_ax.set_xlim(0, 20)
temp_ax.set_ylim(0, 1.5)
temp_ax.set_xlabel("Tempo (min)")
temp_ax.set_ylabel("Intensidade")
temp_ax.set_title("Cromatograma Simulado")

# Para cálculo de resolução
resolucoes = []
picos_ordenados = []
linha_coeluicao = None  # Variável para a linha de coeluição

for i, (composto, tr) in enumerate(sorted(tempos_ret.items(), key=lambda x: x[1]), start=1):
    altura = 1.0
    largura = 0.15 + (fluxo * 0.05) + (abs(temperatura - 35) * 0.005)
    largura *= 1 + abs(fase_movel - 50) / 200
    start = tr - 2 * largura
    end = tr + 2 * largura
    width = end - start
    pratos = 16 * (tr / width) ** 2
    pico = altura * np.exp(-((tempo - tr) ** 2) / (2 * (width / 4) ** 2))
    sinal_total += pico

    resultados.append([composto, tr, start, end, width, int(pratos)])
    temp_ax.plot(tempo, pico, label=f'{composto}', color=cores[composto])
    picos_ordenados.append((composto, tr, width))

# Verificando coeluição e desenhando a linha cinza de coeluição
for i in range(len(picos_ordenados) - 1):
    comp1, tr1, w1 = picos_ordenados[i]
    comp2, tr2, w2 = picos_ordenados[i+1]
    Rs = (2 * abs(tr2 - tr1)) / (w1 + w2)
    if Rs < 2:  # Coeluindo
        start_coel = min(tr1 - w1, tr2 - w2)
        end_coel = max(tr1 + w1, tr2 + w2)
        linha_coeluicao = temp_ax.plot(tempo, sinal_total, 'k--', label='Região de Coeluição')

    resolucoes.append([f"{comp1} / {comp2}", Rs])

# Exibindo o gráfico
st.pyplot(temp_fig)

# Tabela de parâmetros cromatográficos
st.subheader("📊 Tabela de parâmetros cromatográficos")
df = pd.DataFrame(resultados, columns=["Composto", "Rt (min)", "Início do pico (min)", "Fim do pico (min)", "Largura da base do pico / width (min)", "Pratos teóricos"])
df['Composto'] = df['Composto'].replace({"Dipirona": 1, "Cafeína": 2, "Orfenadrina": 3})
st.dataframe(df.style.format({"Rt (min)": "{:.2f}", "Início do pico (min)": "{:.2f}", "Fim do pico (min)": "{:.2f}", "Largura da base do pico / width (min)": "{:.2f}"}))

# Tabela de resolução
if resolucoes:
    st.subheader("📏 Resolução entre picos")
    df_rs = pd.DataFrame(resolucoes, columns=["Pares de Compostos", "Resolução (Rs)"])
    st.dataframe(df_rs.style.format({"Resolução (Rs)": "{:.2f}"}))

# Exportar como PDF
st.subheader("📄 Exportar resultados")

def exportar_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Relatório do Cromatograma HPLC", ln=1, align='C')
    pdf.ln(10)

    for i in range(len(df)):
        linha = df.iloc[i]
        texto = f"{linha['Composto']}: Rt={linha['Rt (min)']:.2f} min, Início={linha['Início do pico (min)']:.2f}, Fim={linha['Fim do pico (min)']:.2f}, Width={linha['Largura da base do pico / width (min)']:.2f}, Pratos={linha['Pratos teóricos']}"
        pdf.cell(200, 10, txt=texto, ln=1)

    buf = io.BytesIO()
    temp_fig.savefig(buf, format='png')
    buf.seek(0)
    pdf.image(buf, x=10, y=None, w=180)

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    b64 = base64.b64encode(pdf_output.getvalue()).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="relatorio_hplc.pdf">📥 Baixar PDF</a>'
    st.markdown(href, unsafe_allow_html=True)

if st.button("Exportar como PDF"):
    exportar_pdf()
