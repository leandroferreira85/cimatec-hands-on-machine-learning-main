import time
import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

from openai import OpenAI

from io import StringIO
from langchain.document_loaders import BSHTMLLoader


st.title('Assistente pessoal')

# armazenando o total de tokens utilizado no chat
contador_tokens = {
    'prompt_tokens': 0,
    'completion_tokens': 0
}


# Obtendo a chave da openai
chave = st.sidebar.text_input('Chave da API OpenAI', type = 'password')
client = OpenAI(api_key=chave)
modelo = "gpt-3.5-turbo"

# input para a criatividade das respostas
opcao_criatividade = st.sidebar.slider(
    label="Grau de criatividade da resposta",
    min_value=0.0,
    max_value=2.0,
    step=0.01
)



def finalizar_conversa():
    pass


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


uploaded_files = st.file_uploader("Selecione ou arraste os arquivos que irão fazer parte do contexto:",
                                  type="txt",
                                  accept_multiple_files=True)

if uploaded_files:
    text_list = []
    for file in uploaded_files:
        texto = file.getvalue().decode("utf-8")
        text_list.append(texto)

    # criando e inicializando o histório do chat
    contexto = f'''
            Você é um assistente pessoal com objetivo de responder as 
            perguntas do usuário com um estilo de escrita {opcao_estilo_resposta}. 
            Limite o tamanho da resposta para {opcao_tamanho_resposta} palavras no máximo.
            '''
    if text_list and len(text_list) > 0:
        contexto += "Para responder, considere as seguintes informações: \n\n\n\n"
        contexto += f" {texto}\n"

    if "mensagens" not in st.session_state:
        st.session_state.mensagens = [{
            "role": 'system', 
            "content": contexto}]

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
                st.markdown("<ul>", unsafe_allow_html=True)
                for category in df.head(5)['Category']:
                    st.markdown(f'<li>Categoria: {category}</li>', unsafe_allow_html=True)
                st.markdown("</ul>", unsafe_allow_html=True)

                st.markdown("Que tal falarmos sobre outra coisa?")
        else:
            # Display user message in chat message container
            
            # Add user message to chat history
            st.session_state.mensagens.append({"role": "user", "content": prompt})

            chamada = client.chat.completions.create(
                model = modelo,
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



