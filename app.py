import streamlit as st
import math
import pandas as pd
import matplotlib.pyplot as plt

# Configurações iniciais da página
st.set_page_config(page_title="Painel de Dimensionamento de Sistema de Agitação", layout="wide")
st.title("🧩 Painel Interativo de Dimensionamento de Sistema de Agitação e Abastecimento")

# Entradas do usuário
st.sidebar.header("Parâmetros de Entrada")
modelo_bomba = st.sidebar.selectbox("Modelo da Bomba", ["ABK50D", "ABK120D", "ABK200D"])
vazao_abastecimento = st.sidebar.number_input("Vazão de Abastecimento (L/min)", value=40)
pontos_agitacao = st.sidebar.number_input("Número de Pontos de Agitação", value=2, min_value=1)

bitola_recalque = st.sidebar.selectbox("Bitola Recalque Principal (pol)", [1.0, 1.5, 2.0])
comp_recalque = st.sidebar.number_input("Comprimento Recalque Principal (m)", value=1.2)

bitola_agit1 = st.sidebar.selectbox("Bitola Agitação 1 (pol)", [1.0, 1.5, 2.0])
comp_agit1 = st.sidebar.number_input("Comprimento Agitação 1 (m)", value=0.5)

bitola_agit2 = st.sidebar.selectbox("Bitola Agitação 2 (pol)", [1.0, 1.5, 2.0])
comp_agit2 = st.sidebar.number_input("Comprimento Agitação 2 (m)", value=0.7)

bitola_abastecimento = st.sidebar.selectbox("Bitola Abastecimento (pol)", [1.0, 1.5, 2.0])
comp_abastecimento = st.sidebar.number_input("Comprimento Abastecimento (m)", value=10.0)

volume_tanque = st.sidebar.number_input("Volume do Tanque (L)", value=220)
taxa_agitacao = st.sidebar.number_input("Taxa de Agitação (vezes por minuto)", value=1.5)

# Constantes
rho = 1000  # kg/m³
nu = 1.004e-6  # m²/s
g = 9.81  # m/s²
k_D = 0.005  # rugosidade relativa estimada para PVC

# Conversão de unidades
pol_to_m = 0.0254

# Definindo vazões
Q_abastecimento = vazao_abastecimento / 1000 / 60  # m³/s
Q_agitacao_total = (volume_tanque * taxa_agitacao) / 1000 / 60  # m³/s
Q_total = Q_abastecimento + Q_agitacao_total
Q_ponto_agitacao = Q_agitacao_total / pontos_agitacao

# Bitolas convertidas para metros
bitolas = {
    "recalque": bitola_recalque * pol_to_m,
    "agit1": bitola_agit1 * pol_to_m,
    "agit2": bitola_agit2 * pol_to_m,
    "abastecimento": bitola_abastecimento * pol_to_m
}

# Função para perda de carga
def perda_carga(D, L, Q, curvas=2, valvulas=1):
    A = math.pi * (D ** 2) / 4
    V = Q / A
    Re = V * D / nu
    if Re < 2000:
        f = 64 / Re  # laminar
    else:
        f = 0.25 / (math.log10((k_D / 3.7) + (5.74 / Re ** 0.9))) ** 2
    hf = f * (L / D) * (V ** 2) / (2 * g)
    K_total = (curvas * 0.9) + (valvulas * 0.2)
    hl = K_total * (V ** 2) / (2 * g)
    return hf + hl, V

# Calculando perdas de carga
perda_recalque, V_recalque = perda_carga(bitolas['recalque'], comp_recalque, Q_total)
perda_agit1, V_agit1 = perda_carga(bitolas['agit1'], comp_agit1, Q_ponto_agitacao)
perda_agit2, V_agit2 = perda_carga(bitolas['agit2'], comp_agit2, Q_ponto_agitacao)
perda_abastecimento, V_abastecimento = perda_carga(bitolas['abastecimento'], comp_abastecimento, Q_abastecimento)

# Perda de carga nos bicos agitadores (considerando 12mm por bico)
D_bico = 0.012
A_bico = math.pi * (D_bico ** 2) / 4
V_bico = (Q_ponto_agitacao / 2) / A_bico  # considerando 2 bicos por ponto
h_bico = (rho * V_bico ** 2) / (2 * rho * g)

# Perda total
perda_total = perda_recalque + perda_agit1 + perda_agit2 + perda_abastecimento + h_bico
pressao_total = perda_total * rho * g

# Exibição dos resultados
st.header("Resultados do Dimensionamento")
resultados = {
    "Perda de Carga Recalque Principal (m)": perda_recalque,
    "Perda de Carga Agitação 1 (m)": perda_agit1,
    "Perda de Carga Agitação 2 (m)": perda_agit2,
    "Perda de Carga Abastecimento (m)": perda_abastecimento,
    "Perda de Carga nos Bicos Agitadores (m)": h_bico,
    "Perda Total do Sistema (m)": perda_total,
    "Pressão Total Necessária (Pa)": pressao_total,
    "Pressão Total Necessária (mca)": perda_total
}

df_resultados = pd.DataFrame(resultados.items(), columns=["Descrição", "Valor"])
st.dataframe(df_resultados, use_container_width=True)

# Sugestão de bomba com base na curva fornecida
sugestao = ""
if pressao_total <= 8 * 1000 * g and Q_total * 60 * 1000 <= 200:
    sugestao = "ABK50D"
elif pressao_total <= 8 * 1000 * g and Q_total * 60 * 1000 <= 500:
    sugestao = "ABK120D"
elif pressao_total <= 8 * 1000 * g and Q_total * 60 * 1000 <= 700:
    sugestao = "ABK200D"
else:
    sugestao = "Sistema fora da capacidade das bombas disponíveis"

st.subheader("Sugestão de Modelo de Bomba")
st.markdown(f"### 🚀 {sugestao}")

# Gráfico opcional da curva da bomba
st.subheader("Curva Teórica da Bomba")
fig, ax = plt.subplots()

q_bomba = [0, 200, 500, 700]  # L/min
h_bomba = [16, 12, 8, 6]      # m
ax.plot(q_bomba, h_bomba, marker='o', label='Curva da Bomba')
ax.axhline(y=perda_total, color='r', linestyle='--', label='Perda Total do Sistema')
ax.set_xlabel("Vazão (L/min)")
ax.set_ylabel("Altura Manométrica Total (m)")
ax.legend()
st.pyplot(fig)

st.success("Simulação concluída! Você pode exportar este painel como aplicação ou PDF!")
