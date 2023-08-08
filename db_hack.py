import streamlit as st
import openai
from db_chat import user_message, bot_message, check_for_openai_key
from my_pdf_lib import load_index_from_db, get_index_for_pdf, store_index_in_db
import json
import os


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


def get_openai_models():
    models = openai.Model.list()
    dict_list = [elem for elem in models.data if elem["object"] == "model"]
    contains_gpt_4 = any(d['id'] == "gpt-4" for d in dict_list)
    if contains_gpt_4:
        available_models = ["gpt-3.5-turbo", 'gpt-4']
    else:
        available_models = ["gpt-3.5-turbo"]
    return available_models


def chat_page():
    api_key = check_for_openai_key()
    openai.api_key = api_key

    available_models = get_openai_models()
    selected_model = st.selectbox("Please select a model", options=available_models)
    st.title("Drug Repurposing Chatbot 💊")
    st.write(
        """👩‍🔬 This chatbot is your expert assistant in the field of drug repurposing. 
           Leveraging a knowledge base derived from a variety of scientific documents related to drug repurposing, 
           it can provide detailed insights and answers to your queries! 📚
           To customize the knowledge base, please navigate to the *Configure Knowledge Base* page."""
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
        bot_message("Hi there, how can I help?", bot_name="drGPT")

    for message in prompt:
        if message["role"] == "user":
            user_message(message["content"])
        elif message["role"] == "assistant":
            bot_message(message["content"], bot_name="drGPT")

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
                    model="gpt-3.5-turbo", messages=prompt, temperature=0, stream=True
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

        st.session_state["prompt"] = prompt


def config_page():
    openai_api_key = check_for_openai_key()
    openai.api_key = openai_api_key

    st.title("Configure knowledge base")

    try:
        indices = get_json("index-list.json")
        if indices == None:
            indices = []
    except:
        indices = []

    dip = indices + ["Create New"]
    select_index = st.selectbox("Select knowledge base", options=dip)

    # List of protected index names
    protected_indices = ["repo4euD21"]

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
            # Only delete the files if the index is not protected
            if select_index not in protected_indices:
                # Delete the files
                pkl_file = f"{select_index}.pkl"
                index_file = f"{select_index}.index"
                if os.path.exists(pkl_file):
                    os.remove(pkl_file)
                if os.path.exists(index_file):
                    os.remove(index_file)

                indices.remove(select_index)
                store_data_as_json("index-list.json", indices)
            else:
                st.warning("Database is protected and cannot be deleted.")
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
