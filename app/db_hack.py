import streamlit as st
import openai
from db_chat import get_api_key, user_message, bot_message
from my_pdf_lib import load_index_from_db, get_index_for_pdf, store_index_in_db
import json


def get_json(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data


def store_data_as_json(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file)


def store_api_key(api_key):
    with open('api_key.txt', 'w') as file:
        file.write(api_key)


def chat_page():
    openai.api_key = get_api_key()

    st.title("Chat your PDFs")
    st.write(
        """This template allows you to add PDFs to a knowledge base (vectordb) and chat with it. 
                To insert your PDFs, go to the *Configure Knowledge Base* page."""
    )

    try:
        config = get_json("config.json")
        index_name = config["index"]
    except:
        st.info("No knowledge base found. Please configure one!")
        st.stop()

    index = load_index_from_db(index_name)

    prompt = st.session_state.get("prompt", None)
    if prompt is None:
        prompt = [{"role": "system", "content": 'You are a helpful assistant.'}]
        bot_message("Hi there, how can I help?", bot_name="pdfGPT")

    for message in prompt:
        if message["role"] == "user":
            user_message(message["content"])
        elif message["role"] == "assistant":
            bot_message(message["content"], bot_name="pdfGPT")

    messages_container = st.container()
    question = st.text_input(
        "Type your a question",
        placeholder="What is drug repurposing?",
        key="text_input_widget",
    )
    st.session_state['dummy_text'] = question

    # Add clear chat button
    if st.button("Clear Chat"):
        st.session_state["prompt"] = [{"role": "system", "content": 'You are a helpful assistant.'}]
        st.experimental_rerun()

    if st.session_state.dummy_text:
        # rest of the function...
        docs = index.similarity_search(st.session_state.dummy_text)
        doc = docs[0].page_content

        prompt_template = 'The given information is: {document_data}'
        prompt_template = prompt_template.format(document_data=doc)
        prompt[0] = {"role": "system", "content": prompt_template}

        prompt.append({"role": "user", "content": st.session_state.dummy_text})

        with messages_container:
            user_message(st.session_state.dummy_text)
            botmsg = bot_message("...", bot_name="pdfGPT")

        response = []
        result = ""
        if openai.api_key:
            for chunk in openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", messages=prompt, stream=True
            ):
                text = chunk.choices[0].get("delta", {}).get("content")
                if text is not None:
                    response.append(text)
                    result = "".join(response).strip()

                    botmsg.update(result)

            prompt.append({"role": "assistant", "content": result})

        else:
            botmsg.update(
                """
            Hi there. You haven't provided me with an OpenAI API key that I can use. 
            Please provide a key in the box below so we can start chatting:
            """
            )
            api_key = st.text_input("Please type inn your API key", type="password")
            if api_key:
                store_api_key(api_key)
                st.experimental_rerun()

        st.session_state["prompt"] = prompt


def config_page():
    openai_api_key = "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"

    st.title("Configure knowledge base")

    try:
        indices = get_json("index-list.json")
        if indices == None:
            indices = []
    except:
        indices = []

    dip = indices + ["Create New"]
    select_index = st.selectbox("Select knowledge base", options=dip)

    if select_index == "Create New":
        with st.form(key="index"):
            st.write("##### Create a new knowledge base")
            files = st.file_uploader(
                "Step 1 - Upload files", type="pdf", accept_multiple_files=True
            )

            name = st.text_input("Step 2 - Choose a name for your index")
            button = st.form_submit_button("Create Index")

            if button:
                with st.spinner("Indexing"):
                    index = get_index_for_pdf(files, openai_api_key=openai_api_key)
                    index_name = "index_" + name
                    store_index_in_db(index, name=index_name)
                    indices = indices + [index_name]
                    store_data_as_json("index-list.json", indices)
                st.success("Finished creating new index")
                st.experimental_rerun()
    else:
        delete = st.button("Delete")

        config = {}
        config["index"] = select_index
        store_data_as_json("config.json", config)

        if delete:
            indices.remove(select_index)
            store_data_as_json("index-list.json", indices)
            st.experimental_rerun()


def main():
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Chatbot", "Configure knowledge base"],
    )

    if page == "Chatbot":
        chat_page()
    elif page == "Configure knowledge base":
        config_page()


if __name__ == "__main__":
    main()
