import time
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

from openai import OpenAI

import pdfkit
import tempfile
import base64
from io import BytesIO

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, Spacer
import reportlab.platypus as rlplt
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.platypus import Frame, PageTemplate, KeepInFrame, Paragraph
from reportlab.lib.units import mm, inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT

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

def formatar_texto(texto):
    estilo_texto = ParagraphStyle(name='Breadpointlist_style',
                              alignment=TA_LEFT,
                              parent=getSampleStyleSheet()['Normal'],
                              bulletFontSize=7,
                              bulletIndent=0,
                              endDots=None,
                              firstLineIndent=0,
                              fontSize=8,
                              justifyBreaks=0,
                              justifyLastLine=0,
                              leading=9.2,
                              leftIndent=11,
                              rightIndent=0,
                              spaceAfter=0,
                              spaceBefore=0,
                              textColor=colors.black,
                              wordWrap='LTR',
                              splitLongWords=True,
                              spaceShrinkage=0.05,
                              )
    return Paragraph(texto, estilo_texto) if isinstance(texto, str) else texto

def converter_dataframe_para_lista(df):
    lista_dados = [df.columns.tolist()] + df.values.tolist()
    return lista_dados

def exportar_tabela_para_pdf(dados):
    
    buffer = BytesIO()

    left_margin = 5 * mm
    right_margin = 5 * mm
    top_margin = 5 * mm
    bottom_margin = 5 * mm

    doc = SimpleDocTemplate(buffer, pagesize=(landscape(A4)),
                        leftMargin=left_margin, rightMargin=right_margin,
                        topMargin=top_margin, bottomMargin=bottom_margin)
    elementos = []

    dados2 = [[formatar_texto(cell) for cell in row] for row in dados]

    # Crie a tabela com os dados
    tabela = rlplt.Table(dados2, colWidths=(30*mm, 25*mm, 25*mm, None))

    # Defina o estilo da tabela
    estilo_tabela = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    tabela.setStyle(estilo_tabela)

    #Adição de título
    styles = getSampleStyleSheet()
    titulo_style = styles["Title"]

    titulo = Paragraph("Exportação da conversa do assistente pessoal", titulo_style)

    # Adicione a tabela ao documento
    elementos.append(titulo)
    elementos.append(tabela)

    # Adicione um Spacer para criar um espaço entre a tabela e o próximo elemento
    elementos.append(Spacer(1, 0.25 * inch))

    doc.build(elementos)

    buffer.seek(0)
    return buffer

# Função para converter DataFrame para HTML com quebra de linha nas colunas de texto
def dataframe_to_html(df):
    return df.to_html(escape=False, formatters=dict(text=lambda x: x.replace('\n', '<br>')), index=False)

# Função para converter HTML para PDF
def html_to_pdf(html, pdf_buffer):
    pdfkit.from_string(html, pdf_buffer)

def finalizar_conversa():
    data_list = []

    #https://stackoverflow.com/a/56746204
    for message, export_data_item in zip(st.session_state.mensagens, st.session_state.export_data):
        data_list.append([export_data_item['datetime'], export_data_item['tokens'], message['role'], message['content']])

    df = pd.DataFrame(data_list,columns=['Data/Hora', 'Tokens', 'Papéis','Histórico'])

    st.dataframe(df)

    data_list.insert(0,['Data/Hora', 'Tokens', 'Papéis','Histórico'])
    pdf_buffer = exportar_tabela_para_pdf(data_list)

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
        "content": f'''
        Você é um assistente pessoal com objetivo de responder as 
        perguntas do usuário com um estilo de escrita {opcao_estilo_resposta}. 
        Limite o tamanho da resposta para {opcao_tamanho_resposta} palavras no máximo.
        '''
        }]
    st.session_state.export_data = [{
        "datetime": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "tokens" : "P 0"
    }]

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
        st.session_state.mensagens.append({"role": "user", 
                                           "content": prompt
                                           })

        chamada = client.chat.completions.create(
            model = 'gpt-3.5-turbo',
            temperature = opcao_criatividade,
            messages = st.session_state.mensagens
        )

        st.session_state.export_data.append({"datetime": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                           "tokens": f'P {chamada.usage.prompt_tokens}'
                                           })

        contador_tokens['prompt_tokens'] += chamada.usage.prompt_tokens
        contador_tokens['completion_tokens'] += chamada.usage.completion_tokens

        resposta = chamada.choices[0].message.content

        # Display assistant response in chat message container
        with st.chat_message("system"):
            st.markdown(f"Completion Tokens: {contador_tokens['completion_tokens']}\nPrompt Tokens: {contador_tokens['prompt_tokens']}")
            st.markdown(resposta)

        # Add assistant response to chat history
        st.session_state.mensagens.append({"role": "system", 
            "content": resposta            
            })
        st.session_state.export_data.append({"datetime": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                           "tokens": f'C {chamada.usage.completion_tokens}'
                                           })



