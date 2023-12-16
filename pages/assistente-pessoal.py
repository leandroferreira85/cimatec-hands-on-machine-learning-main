import time
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

from openai import OpenAI

import pdfkit
import tempfile
import base64
from io import BytesIO


st.title('Assistente pessoal')

# armazenando o total de tokens utilizado no chat
contador_tokens = {
    'prompt_tokens': 0,
    'completion_tokens': 0
}


# Obtendo a chave da openai
chave = st.sidebar.text_input('Chave da API OpenAI', type = 'password')
client = OpenAI(api_key=chave)

# input para a criatividade das respostas
opcao_criatividade = st.sidebar.slider(
    label="Grau de criatividade da resposta",
    min_value=0.0,
    max_value=2.0,
    step=0.01
)


# Função para converter DataFrame para HTML com quebra de linha nas colunas de texto
def dataframe_to_html(df):
    return df.to_html(escape=False, formatters=dict(text=lambda x: x.replace('\n', '<br>')), index=False)

# Função para converter HTML para PDF
def html_to_pdf(html, pdf_buffer):
    pdfkit.from_string(html, pdf_buffer)

def finalizar_conversa():
    df = pd.DataFrame(columns=['Data/Hora','Completion Tokens','Prompt Tokens','Historico'])

    conteudo_historico = ""
    for message in st.session_state.mensagens:
        conteudo_historico += f"[{message['role']}] {message['content']}\n"


    conversa = {
        'Data/Hora' : date.today(),
        'Completion Tokens' : contador_tokens["completion_tokens"],
        'Prompt Tokens' : contador_tokens["prompt_tokens"],
        'Historico': conteudo_historico
    }
    df = df.append(conversa, ignore_index=True)
    st.dataframe(df)

    # Converter DataFrame para HTML
    html_data = dataframe_to_html(df)

    # Criar buffer de memória para armazenar o PDF
    pdf_buffer = BytesIO()

    # Converter HTML para PDF no buffer de memória
    html_to_pdf(html_data, pdf_buffer)
    st.download_button("Baixar PDF", data=pdf_buffer, file_name="dataframe.pdf", mime="application/pdf")


def traduzir_tamanho_resposta(tamanho: int) -> str:
    if tamanho == 300:
        return "pequeno"
    elif tamanho == 600:
        return "médio"
    elif tamanho == 900:
        return "grande"
    else:
        return 0

opcao_tamanho_resposta = st.sidebar.select_slider(
    label="Tamanho da resposta (tokens)",
    options=[300,600,900],
    format_func=traduzir_tamanho_resposta
)

opcao_estilo_resposta = st.sidebar.selectbox(
    label="Estilo da resposta",
    options=["expositivo", "rebuscado", "expositivo","narrativo", "criativo", "objetivo", "pragmático", "sistemático", "debochado","soteropolitano"]
)



# criando e inicializando o histório do chat
if "mensagens" not in st.session_state:
    st.session_state.mensagens = [{
        "role": 'system', 
        "content": '''
        Você é um assistente pessoal com objetivo de responder as 
        perguntas do usuário com um estilo de escrita {opcao_estilo_resposta}. 
        Limite o tamanho da resposta para {opcao_tamanho_resposta} palavras no máximo.
        '''}]

# Aparecer o Historico do Chat na tela
for mensagens in st.session_state.mensagens[1:]:
    with st.chat_message(mensagens["role"]):
        st.markdown(mensagens["content"])

# React to user input
prompt = st.chat_input("Digite alguma coisa")
st.sidebar.button(
    label="Finalizar conversa",
    on_click=finalizar_conversa
)


if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    # TODO: incluir código da moderação do prompt
    response_moderation = client.moderations.create(input=prompt)

    df = pd.DataFrame(dict(response_moderation.results[0].category_scores).items(), columns=['Category', 'Value'])
    df.sort_values(by = 'Value', ascending = False, inplace=True)

    if (df.iloc[0,1] > 0.01):
        with st.chat_message("system"):
            st.markdown("Acho que o que você falou se enquadra em algumas categorias que eu não posso falar sobre:")
            for category in df.head(5)['Category']:
                st.markdown(f'{category}')
            st.markdown("Que tal falarmos sobre outra coisa?")
    else:
        # Display user message in chat message container
        
        # Add user message to chat history
        st.session_state.mensagens.append({"role": "user", "content": prompt})

        chamada = client.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature = opcao_criatividade,
            messages = st.session_state.mensagens
        )

        contador_tokens['prompt_tokens'] += chamada.usage.prompt_tokens
        contador_tokens['completion_tokens'] += chamada.usage.completion_tokens

        resposta = chamada.choices[0].message.content

        

        # Display assistant response in chat message container
        with st.chat_message("system"):
            st.markdown(f"Completion Tokens: {contador_tokens['completion_tokens']}\nPrompt Tokens: {contador_tokens['prompt_tokens']}")
            st.markdown(resposta)
        # Add assistant response to chat history
        st.session_state.mensagens.append({"role": "system", "content": resposta})



