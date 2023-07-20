import streamlit as st
from chatbot import ChatBot
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
import os
import openai

openai.api_key = "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"
os.environ["OPENAI_API_KEY"] = openai.api_key
my_embedding_model = OpenAIEmbeddings()

persist_directory = '/Users/fernando/Documents/Research/drugrepochat/data/faiss_index'
vectordb = FAISS.load_local(persist_directory, my_embedding_model)

chatbot = ChatBot(vectordb)

def app():
    st.title("Drug repurposing Chatbot 💊♻️")
    user_input = st.text_input("You:")

    # If the chat_history session variable is not set, initialize it as an empty list
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if st.button("Send"):
        # Get the chatbot response
        response = chatbot.generate_contextual_response(user_input)

        # Add the user input and chatbot response to the chat history
        st.session_state.chat_history.append(('You', user_input))
        st.session_state.chat_history.append(('Chatbot', response))

    # Display the chat history
    chat_history_md = ""
    for speaker, text in st.session_state.chat_history:
        if speaker == 'You':
            chat_history_md += f"> {speaker}: {text}\n\n"  # User texts are aligned to the right
        else:
            chat_history_md += f"{speaker}: {text}\n\n"  # Chatbot responses are aligned to the left

    st.markdown(chat_history_md)


if __name__ == "__main__":
    app()
