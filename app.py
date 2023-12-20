import streamlit as st 
from st_pages import Page, Section, add_page_title, show_pages

st.header('🤖 CIMATEC - Hands On Machine Learning')



show_pages([
    #Section(name="Section1", icon=":books:"),
    Page("pages/assistente-pessoal.py", "Assistente Pessoal", ":speech_balloon:"),
    Page("pages/modelo.py", "Modelo", ":computer:"),
    Page("pages/sobre.py", "Sobre", ":briefcase:") #:tophat:
])