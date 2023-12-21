import streamlit as st 
from pycaret.regression import load_model, predict_model
import pandas as pd
import numpy as np

# carregando o modelo
modelo = load_model('resources/modelo_diabetes')

# apresentando o formulário para obtenção dos valores
st.title("Previsão de diabetes")

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    numero_gestacoes = st.slider(
        label="Número de gestações",
        min_value=0,
        max_value=17,
        value=3,
        step=1
    )

    pressao_arterial = st.slider(
        label="Pressão arterial diastólica (mm Hg)",
        min_value=0,
        max_value=122,
        value=19,
        step=1
    )
    concentracao_glucose = st.slider(
        label="Concentração plasmática de glicose após 2 horas em um teste oral de tolerância à glicose",
        min_value=0,
        max_value=199,
        value=32,
        step=1
    )


with col2:
    espessura_triceps = st.slider(
        label="Espessura da dobra cutânea do tríceps (mm)",
        min_value=0,
        max_value=99,
        value=16,
        step=1
    )

    insulina = st.slider(
        label="Insulina sérica de 2 horas (mu U/ml)",
        min_value=0,
        max_value=846,
        value=115,
        step=1
    )

    bmi = st.slider(
        label="Índice de massa corporal (peso em kg/(altura em m)^2)",
        min_value=0,
        max_value=67,
        value=8,
        step=1
    )

with col3:

    pedigree_diabetes = st.slider(
        label="Função de pedigree do diabetes",
        min_value=0.07,
        max_value=2.42,
        value=0.33,
        step=0.01
    )

    idade = st.slider(
        label="Idade (anos)",
        min_value=21,
        max_value=81,
        value=29,
        step=1
    )


# criando dataset para previsão
valores_formulario = {
    'Number of times pregnant': [numero_gestacoes],
    'Plasma glucose concentration a 2 hours in an oral glucose tolerance test': [concentracao_glucose],
    'Diastolic blood pressure (mm Hg)': [pressao_arterial],
    'Triceps skin fold thickness (mm)': [espessura_triceps],
    '2-Hour serum insulin (mu U/ml)': [insulina],
    'Body mass index (weight in kg/(height in m)^2)': [bmi],
    'Diabetes pedigree function': [pedigree_diabetes],
    'Age (years)': [idade]
}

df_predict = pd.DataFrame(valores_formulario)
st.dataframe(df_predict)

# usando o modelo salvo para fazer a previsão 
botao = st.button('Prever se tem diabetes')
if botao:
    previsao = predict_model(modelo, data=df_predict)
    if previsao.loc[0,'prediction_label']:
        valor = 'Essa pessoa tem diabetes'
    else:
        valor = 'Essa pessoa não tem diabetes'
    st.write(f'### {valor}')