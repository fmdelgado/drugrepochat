import time

import streamlit as st
import openai
import sys

import extra_streamlit_components as stx

sys.path.append('/Users/fernando/Documents/Research/drugrepochat/app')
from db_management import *
from db_chat import user_message, bot_message
from my_pdf_lib import load_index_from_db, get_index_for_pdf, store_index_in_db
import json
import os
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
import markdown
import hashlib


@st.cache_resource(experimental_allow_widgets=True)
def get_manager():
    return stx.CookieManager()


cookie_manager = get_manager()


def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()


def get_json(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data


def store_data_as_json(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file)


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
    # when no user logged in: application can be used by only giving an API key
    if "key" not in st.session_state.keys():
        st.session_state["key"] = st.text_input(
            "Please, type in your OpenAI API key to continue", type="password", help="at least 10 characters required"
        )
        if len(st.session_state.key) > 10:
            openai.api_key = st.session_state.key
        else:
            st.warning("At least 10 characters are required!")
            st.stop()
    # try to get available models to see if API key is valid
    try:
        available_models = get_openai_models()
    except:
        st.error("Your provided OpenAI API key is not valid.")
        available_models = []
    selected_model = st.selectbox("Please select a model", options=available_models)
    st.title("Academate")
    st.header("Questions and  Answering Chatbot")
    st.write(
        """
        This chatbot is your expert assistant in the field of drug repurposing. 
           Leveraging a knowledge base derived from a variety of scientific documents related to your topic of choice,
           it can provide detailed insights and answers to your queries! 📚

           To customize the knowledge base, please navigate to the *Configure Knowledge Base* page.

            """
    )

    try:
        config = get_json("config.json")
        index_name = config["index"]

    except:
        st.info("No knowledge base found. Please configure one!")
        st.stop()

    index = load_index_from_db(index_name)

    # start a new chat

    # reproduce chat if user is logged in from DB
    if "user" in st.session_state.keys():
        messages = get_chatdata(st.session_state["user"])
        st.session_state["messages"] = []
        for message in messages:
            st.session_state["messages"].append({"role": message[3], "content": message[2]})
    # start a new chat
    if "messages" not in st.session_state.keys() or len(st.session_state["messages"]) == 0:
        message = {"role": "assistant", "content": "Hi there, how can I help?"}
        st.session_state["messages"] = [message]
        if "user" in st.session_state.keys():
            # safe messages in DB
            add_chatdata(st.session_state["user"], message["content"], message["role"])
    for message in st.session_state["messages"]:
        if message["role"] == "user":
            user_message(message["content"])
        elif message["role"] == "assistant":
            bot_message(message["content"], bot_name="Academate")

    # get message from user
    if prompt := st.chat_input():
        message = {"role": "user", "content": prompt}
        st.session_state["messages"].append(message)
        if "user" in st.session_state.keys():
            add_chatdata(st.session_state["user"], message["content"], message["role"])

    # produce response
    if prompt:
        # rest of the function...
        # WHY?
        # docs = index.similarity_search(prompt)
        # doc = docs[0].page_content

        # prompt_template = 'The given information is: {document_data}'
        # prompt_template = prompt_template.format(document_data=doc)
        # prompt[0] = {"role": "system", "content": prompt_template}

        with st.container():
            user_message(prompt)
            botmsg = bot_message("...", bot_name="Academate")

        response = []
        result = ""
        # response possible because the API key was valid
        if openai.api_key and len(available_models) > 0:
            for chunk in openai.ChatCompletion.create(
                    model=selected_model, messages=[{"role": "user", "content": prompt}], temperature=0, stream=True
            ):
                text = chunk.choices[0].get("delta", {}).get("content")
                if text is not None:
                    response.append(text)
                    result = "".join(response).strip()

                    botmsg.update(result)
            message = {"role": "assistant", "content": result}
            st.session_state["messages"].append(message)
            if "user" in st.session_state.keys():
                add_chatdata(st.session_state["user"], message["content"], message["role"])

        # no response possible because the API key was not valid -> failure message
        else:
            failure_message = """
            Hi there. You haven't provided me with an OpenAI API key that I can use. 
            Please provide a key, so we can start chatting!
            """
            message = {"role": "assistant", "content": failure_message}
            st.session_state["messages"].append(message)
            botmsg.update(failure_message)
            if "user" in st.session_state.keys():
                add_chatdata(st.session_state["user"], message["content"], message["role"])
    # Add clear chat button
    if len(st.session_state["messages"]) != 0 and st.button("Clear Chat"):
        st.session_state["messages"] = []
        # delete chat in DB as well
        delete_chat(st.session_state["user"])
        st.experimental_rerun()


def config_page():
    # when no user logged in: application can be used by only giving an API key
    if "key" not in st.session_state.keys():
        st.session_state["key"] = st.text_input(
            "Please, type in your OpenAI API key to continue", type="password", help="at least 10 characters required"
        )
        if len(st.session_state.key) > 10:
            openai.api_key = st.session_state.key
        else:
            st.warning("At least 10 characters are required!")
            st.stop()
    try:
        get_openai_models()
    except:
        st.error("Your provided OpenAI API key is not valid.")

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
                try:
                    with st.spinner("Indexing"):
                        index = get_index_for_pdf(files, openai_api_key=st.session_state["key"])
                        index_name = "index_" + name
                        store_index_in_db(index, name=index_name)
                        indices = indices + [index_name]
                        store_data_as_json("index-list.json", indices)
                    st.success("Finished creating new index")
                    st.experimental_rerun()
                except:
                    st.error("Could not create new index. Check your OpenAI API key.")
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
                # cannot be seen because of the rerun -> time sleep for one second
                st.warning("Database is protected and cannot be deleted.")
                time.sleep(1)
            st.experimental_rerun()


def process_llm_response(llm_response, doc_content=True):
    sources = '<ol style="white-space: pre-wrap;">'  # Changed from <ul> to <ol>
    for source in llm_response["source_documents"]:
        source_info = "<li>"
        if doc_content:
            source_info += f"Content: {source.page_content}, "
        source_info += f"{source.metadata['source'].split('/')[-1].replace('.pdf', '')}, Page: {source.metadata['page']}</li>"
        sources += source_info
    sources += "</ol>"  # Changed from </ul> to </ol>
    return sources


def qanda_page():
    # when no user logged in: application can be used by only giving an API key
    if "key" not in st.session_state.keys():
        st.session_state["key"] = st.text_input(
            "Please, type in your OpenAI API key to continue", type="password", help="at least 10 characters required"
        )
        if len(st.session_state.key) > 10:
            openai.api_key = st.session_state.key
        else:
            st.warning("At least 10 characters are required!")
            st.stop()
    # try to get available models to see if API key is valid
    try:
        available_models = get_openai_models()
    except:
        st.error("Your provided OpenAI API key is not valid.")
        available_models = []
    selected_model = st.selectbox("Please select a model", options=available_models)

    chaintype = st.selectbox("Please select chain type", options=['stuff', "map_reduce", "refine"], index=0)
    default_k = 4
    selected_k = st.slider("k", min_value=1, max_value=50, value=default_k, step=1)
    default_fetch_k = 20
    selected_fetch_k = st.slider("fetch_k", min_value=1, max_value=50, value=default_fetch_k, step=1)
    show_sources = st.checkbox("Show texts in original docs", False)

    st.title("Academate")
    st.header("Questions and Answering with sources")

    try:
        config = get_json("config.json")
        index_name = config["index"]

    except:
        st.info("No knowledge base found. Please configure one!")
        st.stop()

    index = load_index_from_db(index_name)

    # reproduce chat if user is logged in from DB
    if "user" in st.session_state.keys():
        messages = get_qandadata(st.session_state["user"])
        st.session_state["messagesqanda"] = []
        for message in messages:
            st.session_state["messagesqanda"].append({"role": message[3], "content": message[2]})
    # start a new chat
    if "messagesqanda" not in st.session_state.keys() or len(st.session_state["messagesqanda"]) == 0:
        message = {"role": "assistant", "content": "Hi there, how can I help?"}
        st.session_state["messagesqanda"] = [message]
        if "user" in st.session_state.keys():
            # safe messages in DB
            add_qandadata(st.session_state["user"], message["content"], message["role"])
    for message in st.session_state["messagesqanda"]:
        if message["role"] == "user":
            user_message(message["content"])
        elif message["role"] == "assistant":
            bot_message(message["content"], bot_name="Academate")

    # get message from user
    if prompt := st.chat_input():
        message = {"role": "user", "content": prompt}
        st.session_state["messagesqanda"].append(message)
        if "user" in st.session_state.keys():
            add_qandadata(st.session_state["user"], message["content"], message["role"])

    if prompt:
        with st.container():
            user_message(prompt)
            botmsg = bot_message("...", bot_name="Academate")

        # response possible because the API key was valid
        if openai.api_key and len(available_models) > 0:

            formatted_prompt = ChatPromptTemplate(
                messages=[
                    HumanMessagePromptTemplate.from_template("""You are great at answering questions about a given \
                                                                database in a technical but easy to understand manner. 
                                                                If you cannot find a direct answer to the question in \
                                                                the documents I gave you, you must say "In your provided \
                                                                context i don't know the answer to your question". \
                                                                When you don't know the answer to a question you admit \
                                                                that you don't know. Here is a question:\
                                                                {user_prompt}""")
                ],
                input_variables=["user_prompt"])

            # Create the chain to answer questions
            qa_chain = RetrievalQA.from_chain_type(
                llm=ChatOpenAI(temperature=0.0, model=selected_model, openai_api_key=openai.api_key),
                chain_type=chaintype,
                retriever=index.as_retriever(search_type="mmr",
                                             search_kwargs={'fetch_k': selected_fetch_k,
                                                            'k': selected_k}),
                return_source_documents=True,
                verbose=True)
            llm_response = qa_chain(formatted_prompt.format_prompt(user_prompt=prompt).to_string())

            # text = f"{llm_response['result']}\nSources:\n{process_llm_response(llm_response, doc_content=showdocs)}"
            # Convert Markdown to HTML
            html_content = markdown.markdown(llm_response['result'])
            if "In your provided context i don" in llm_response['result']:
                text = f"{html_content}"
            else:
                text = f"{html_content}<br><strong>Sources:</strong><br>{process_llm_response(llm_response, doc_content=show_sources)}"
            result = "".join(text).strip()
            botmsg.update(result)
            message = {"role": "assistant", "content": result}
            st.session_state["messagesqanda"].append(message)
            if "user" in st.session_state.keys():
                add_qandadata(st.session_state["user"], message["content"], message["role"])

        # no response possible because the API key was not valid -> failure message
        else:
            failure_message = """
                        Hi there. You haven't provided me with an OpenAI API key that I can use. 
                        Please provide a key, so we can start chatting!
                        """
            message = {"role": "assistant", "content": failure_message}
            st.session_state["messagesqanda"].append(message)
            botmsg.update(failure_message)
            if "user" in st.session_state.keys():
                add_qandadata(st.session_state["user"], message["content"], message["role"])

    # Add clear chat button
    if len(st.session_state["messagesqanda"]) != 0 and st.button("Clear Chat"):
        st.session_state["messagesqanda"] = []
        # delete chat in DB as well
        delete_qanda(st.session_state["user"])
        st.experimental_rerun()


def visualize_index_page():
    st.markdown(
        f'<p align="center"> <img src="https://github.com/fmdelgado/DRACOONpy/raw/master/img/academate_logo.png" width="300"/> </p>',
        unsafe_allow_html=True,
    )
    st.title("Academate")
    st.header("AI-powered assistant for academic research")

    st.markdown("""
    ### Under Construction 🚧

    This page is currently under construction. We're working hard to provide you with a seamless and efficient experience.

    Stay tuned for updates and thank you for your patience!
    """)


def about_page():
    st.markdown(
        f'<p align="center"> <img src="https://github.com/fmdelgado/DRACOONpy/raw/master/img/academate_logo.png" width="300"/> </p>',
        unsafe_allow_html=True,
    )
    st.title("Academate")
    st.header("AI-powered assistant for academic research")

    st.markdown("""
    Academate is an AI-powered assistant for academic research. It is a tool that helps researchers to find relevant information in a large corpus of scientific documents.
    To begin, just upload your PDF files and Academate will create a knowledge base that you can query using natural language. 
        """)

    st.markdown(
        f'''
         <div style="text-align:center">
             <img src="https://github.com/fmdelgado/DRACOONpy/raw/master/img/logo_cosybio.png" width="100" style="margin:0px 15px 0px 15px;"/>
             <img src="https://github.com/fmdelgado/DRACOONpy/raw/master/img/REPO4EU-logo-main.png" width="120" style="margin:0px 15px 0px 15px;"/>
             <img src="https://github.com/fmdelgado/DRACOONpy/raw/master/img/eu_funded_logo.jpeg" width="120" style="margin:0px 15px 0px 15px;"/>
         </div>
         ''',
        unsafe_allow_html=True,
    )
    # Displaying the funding information
    st.markdown("""
    ---
    **Funding Information:**

    This project is funded by the European Union under grant agreement No. 101057619. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or European Health and Digital Executive Agency (HADEA). Neither the European Union nor the granting authority can be held responsible for them. This work was also partly supported by the Swiss State Secretariat for Education, Research and Innovation (SERI) under contract No. 22.00115.
    """)


def sign_up():
    st.subheader("Create an Account")
    st.session_state["user"] = st.text_input('Username')
    st.session_state["password"] = make_hashes(st.text_input('Password', type='password'))
    st.session_state["key"] = st.text_input(
        "Please, type in your OpenAI API key to continue", type="password", help="at least 10 characters required"
    )
    if len(st.session_state["key"]) > 10:
        openai.api_key = st.session_state["key"]
    else:
        st.warning("At least 10 characters are required!")
        st.stop()
    # signup possible if api key at least 10 characters long
    if st.button('SignUp'):
        # user does not exist yet and can be created
        if check_if_user_already_exists(st.session_state["user"]):
            add_userdata(st.session_state["user"], st.session_state["password"], st.session_state["key"])
            st.success("You have successfully created an account. Please log in.")
            time.sleep(2)
            logout()
        # user already exists
        else:
            st.error("The user already exists. Please create a new user or login.")


def login():
    st.subheader("Login")
    user = cookie_manager.get(cookie="user")
    if user and len(user) > 0:
        st.session_state["user"] = user
        data = get_user_data(user)
        st.session_state["password"] = data[0][1]
        st.session_state["key"] = data[0][2]
    if len(st.session_state["user"]) == 0 or len(st.session_state["password"]) == 0 or len(
            st.session_state["key"]) == 0:
        # new login
        with st.form("login"):
            st.session_state["user"] = st.text_input('Username')
            st.session_state["password"] = make_hashes(st.text_input('Password', type='password'))
            st.form_submit_button("login")
    result = login_user(st.session_state["user"], st.session_state["password"])
    # user could be logged in
    if result:
        st.success("Logged In as {}".format(st.session_state["user"]))
        cookie_manager.set("user", st.session_state["user"])  # Expires in a day by default
        st.session_state["key"] = result[0][2]
        # change OpenAI API key
        if st.checkbox("change provided OpenAI API key"):
            key = st.text_input(
                "Please, type in your OpenAI API key to continue", type="password",
                help="at least 10 characters required"
            )

            if len(key) > 10:
                st.session_state["key"] = key
                openai.api_key = st.session_state["key"]
                update_key(st.session_state["key"], st.session_state["user"])
                st.success("Your OpenAI API key has been changed successfully!")
            else:
                st.warning("At least 10 characters are required!")
                st.stop()
    # Login failed
    elif len(st.session_state["user"]) > 0 and len(st.session_state["password"]) > 0:
        st.error("Incorrect login!")


def logout():
    cookie_manager.delete("user")
    cookies = cookie_manager.get_all()
    st.session_state["user"] = ""
    st.session_state["password"] = ""
    st.session_state["key"] = ""
    st.session_state["messages"] = []


def main():
    st.session_state["user"] = ""
    st.session_state["password"] = ""
    st.session_state["key"] = ""
    st.session_state["messages"] = []
    st.session_state["messagesqanda"] = []

    create_usertable()
    create_chattable()
    create_qandatable()

    page = st.sidebar.selectbox(
        "Choose a page",
        ["Login", "Sign up", "Chatbot", "Configure knowledge base", "Q&A", "About"],
    )
    with st.sidebar:
        if st.button("logout"):
            logout()
    if page == "Chatbot":
        chat_page()
    elif page == "Configure knowledge base":
        config_page()
    elif page == "Q&A":
        qanda_page()
    elif page == "Visualize index":
        visualize_index_page()
    elif page == "About":
        about_page()
    elif page == "Sign up":
        sign_up()
    elif page == "Login":
        login()


if __name__ == "__main__":
    main()
