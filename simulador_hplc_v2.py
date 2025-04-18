import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import io
from fpdf import FPDF
import base64

st.set_page_config(page_title="Simulador de HPLC - Dorflex", layout="centered")

st.title("🧪 Simulador de HPLC - Análise de Dorflex")

modo_quiz = st.checkbox("Ativar modo Quiz (resolva coeluição)")
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
if modo_quiz:
    tr_bases = {"Dipirona": 3.0, "Cafeína": 3.4, "Orfenadrina": 6.0}  # Ajustado para possível separação
else:
    tr_bases = {"Dipirona": 2.0, "Cafeína": 4.0, "Orfenadrina": 6.0}

tempos_ret = {comp: calcular_tempo_ret(comp, tr) for comp, tr in tr_bases.items()}

# Dados para o gráfico
tempo = np.linspace(0, 20, 2000)
sinal_total = np.zeros_like(tempo)

cores = {'Dipirona': 'blue', 'Cafeína': 'green', 'Orfenadrina': 'red'}
resultados = []
resolucoes = []
picos_ordenados = []

fig, ax = plt.subplots()
ax.set_xlim(0, 20)
ax.set_ylim(0, 1.5)
ax.set_xlabel("Tempo (min)")
ax.set_ylabel("Intensidade")
ax.set_title("Cromatograma Simulado")

# Gerar os picos gaussianos
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

    resultados.append([i, composto, tr, start, end, width, int(pratos)])
    estilo_linha = ':' if modo_quiz and composto in ['Dipirona', 'Cafeína'] else '-'
    ax.plot(tempo, pico, estilo_linha, label=f'{composto}', color=cores[composto])
    picos_ordenados.append((composto, tr, width))

# Cálculo da resolução entre picos consecutivos (Farmacopeia Brasileira)
for i in range(len(picos_ordenados) - 1):
    comp1, tr1, w1 = picos_ordenados[i]
    comp2, tr2, w2 = picos_ordenados[i+1]
    Rs = (2 * abs(tr2 - tr1)) / (w1 + w2)
    resolucoes.append([f"{comp1} / {comp2}", Rs])

# Mostrar gráfico
st.pyplot(fig)

# Legenda de cores abaixo do gráfico
with st.container():
    st.markdown("### 🟦 Legenda do Cromatograma")
    for comp, cor in cores.items():
        estilo = "pontilhada" if modo_quiz and comp in ['Dipirona', 'Cafeína'] else "sólida"
        st.markdown(f"<span style='color:{cor}'>●</span> {comp} - Linha {estilo}", unsafe_allow_html=True)

# Tabela de resultados
st.subheader("📊 Tabela de parâmetros cromatográficos")
df = pd.DataFrame(resultados, columns=["Nº", "Composto", "Rt (min)", "Início do pico (min)", "Fim do pico (min)", "Largura da base do pico / width (min)", "Pratos teóricos"])
st.dataframe(df.style.format({"Rt (min)": "{:.2f}", "Início do pico (min)": "{:.2f}", "Fim do pico (min)": "{:.2f}", "Largura da base do pico / width (min)": "{:.2f}"}))

# Tabela de resoluções
if resolucoes:
    st.subheader("📏 Resolução entre picos")
    df_rs = pd.DataFrame(resolucoes, columns=["Pares de Compostos", "Resolução (Rs)"])
    st.dataframe(df_rs.style.format({"Resolução (Rs)": "{:.2f}"}))

# Modo Quiz - Feedback
if modo_quiz:
    rs_valores = [rs for _, rs in resolucoes]
    if all(rs > 2.0 for rs in rs_valores):
        st.success("✅ Boa! Você conseguiu separar os picos coeluídos.")
    else:
        st.warning("❌ Os compostos ainda estão coeluindo. Tente ajustar os parâmetros.")

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
        texto = f"{linha['Nº']}. {linha['Composto']}: Rt={linha['Rt (min)']:.2f} min, Início={linha['Início do pico (min)']:.2f}, Fim={linha['Fim do pico (min)']:.2f}, Width={linha['Largura da base do pico / width (min)']:.2f}, Pratos={linha['Pratos teóricos']}"
        pdf.cell(200, 10, txt=texto, ln=1)

    if resolucoes:
        pdf.ln(5)
        pdf.cell(200, 10, txt="Resoluções entre picos:", ln=1)
        for par, rs in resolucoes:
            pdf.cell(200, 10, txt=f"{par}: Rs = {rs:.2f}", ln=1)

    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    pdf.image(buf, x=10, y=None, w=180)

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    b64 = base64.b64encode(pdf_output.getvalue()).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="relatorio_hplc.pdf">📥 Baixar PDF</a>'
    st.markdown(href, unsafe_allow_html=True)

if st.button("Exportar como PDF"):
    exportar_pdf()
