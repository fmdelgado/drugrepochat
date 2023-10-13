import time

import streamlit as st
import openai
import sys

import extra_streamlit_components as stx
from my_pdf_lib import load_index_from_db, store_index_in_db, get_index_for_pdf

sys.path.append('/Users/fernando/Documents/Research/drugrepochat/app')
from db_management import *
from db_chat import user_message, bot_message
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


def get_api_key_if_missing():
    # when no user logged in: application can be used by only giving an API key
    if api_key_missing():
        st.session_state["key"] = st.text_input(
            "Please, type in your OpenAI API key to continue", type="password", help="at least 10 characters required"
        )
        if len(st.session_state.key) > 10:
            openai.api_key = st.session_state["key"]
        else:
            st.warning("At least 10 characters are required!")
            st.stop()


def is_user_logged_in():
    return "user" in st.session_state.keys() and len(st.session_state["user"]) > 0


def api_key_missing():
    return "key" not in st.session_state.keys() or len(st.session_state["key"]) == 0


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


def get_available_models():
    # try to get available models to see if API key is valid
    try:
        available_models = get_openai_models()
    except Exception as e:
        # st.write(e)
        st.error("Your provided OpenAI API key is not valid.")
        available_models = []
    return available_models


def chat_page_styling():
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


def reproduce_chat_if_user_logged_in(typeOfMessage):
    # reproduce chat if user is logged in from DB
    if is_user_logged_in():
        if typeOfMessage == "messages":
            messages = get_chatdata(st.session_state["user"])
            st.session_state[typeOfMessage] = []
        elif typeOfMessage == "messagesqanda":
            messages = get_qandadata(st.session_state["user"])
            st.session_state[typeOfMessage] = []
        for message in messages:
            st.session_state[typeOfMessage].append({"role": message[3], "content": message[2]})


def is_chat_empty(typeOfChat):
    return typeOfChat not in st.session_state.keys() or len(st.session_state[typeOfChat]) == 0


def start_new_chat_if_empty(typeOfChat):
    # start a new chat
    if is_chat_empty(typeOfChat):
        message = {"role": "assistant", "content": "Hi there, how can I help?"}
        st.session_state[typeOfChat] = [message]
        if is_user_logged_in():
            save_message_in_db(typeOfChat, message)


def print_current_chat(typeOfChat):
    for message in st.session_state[typeOfChat]:
        if message["role"] == "user":
            user_message(message["content"])
        elif message["role"] == "assistant":
            bot_message(message["content"], bot_name="Academate")


def clear_chat(typeOfChat):
    # clear chat data
    st.session_state[typeOfChat] = []
    # delete chat in DB as well
    if typeOfChat == "messages":
        delete_chat(st.session_state["user"])
    elif typeOfChat == "messagesqanda":
        delete_qanda(st.session_state["user"])
    st.experimental_rerun()


def save_message_in_db(typeOfChat, message):
    if typeOfChat == "messages":
        add_chatdata(st.session_state["user"], message["content"], message["role"])
    elif typeOfChat == "messagesqanda":
        add_qandadata(st.session_state["user"], message["content"], message["role"])


def get_user_message(typeOfChat):
    if prompt := st.chat_input():
        message = {"role": "user", "content": prompt}
        st.session_state[typeOfChat].append(message)
        if is_user_logged_in():
            save_message_in_db(typeOfChat, message)
    return prompt


def chat_page():
    get_api_key_if_missing()

    available_models = get_available_models()

    selected_model = st.selectbox("Please select a model", options=available_models)
    chat_page_styling()

    reproduce_chat_if_user_logged_in("messages")

    start_new_chat_if_empty("messages")

    print_current_chat("messages")

    index = load_index_from_db(st.session_state["knowledgebase"])

    prompt = get_user_message("messages")

    # produce response
    if prompt:
        with st.container():
            user_message(prompt)
            botmsg = bot_message("...", bot_name="Academate")

        try:
            # add context of the knowledge base to the messages
            docs = index.similarity_search(prompt)
            doc = docs[0].page_content
            prompt_template = 'The given information is: {document_data}'
            prompt_template = prompt_template.format(document_data=doc)
            context = {"role": "system", "content": prompt_template}
            save_message_in_db("messages", context)
            st.session_state["messages"].append(context)
        except Exception as e:
            # st.write(e)
            st.error(
                "An error occured with the chosen knowledge base. The knowledge base could not be used in the following response.")

        response = []
        result = ""
        # response possible because the API key was valid
        if openai.api_key and len(available_models) > 0:
            try:

                for chunk in openai.ChatCompletion.create(
                        model=selected_model, messages=st.session_state["messages"], temperature=0, stream=True
                ):
                    text = chunk.choices[0].get("delta", {}).get("content")
                    if text is not None:
                        response.append(text)
                        result = "".join(response).strip()

                        botmsg.update(result)
                message = {"role": "assistant", "content": result}
                st.session_state["messages"].append(message)
                if is_user_logged_in():
                    save_message_in_db("messages", message)
            except Exception as e:
                # st.write(e)
                st.error("Something went wrong while producing a response.")
        # no response possible because the API key was not valid -> failure message
        else:
            failure_message = """
            Hi there. You haven't provided me with an OpenAI API key that I can use. 
            Please provide a key, so we can start chatting!
            """
            message = {"role": "assistant", "content": failure_message}
            st.session_state["messages"].append(message)
            botmsg.update(failure_message)
            if is_user_logged_in():
                save_message_in_db("messages", message)

    if len(st.session_state["messages"]) != 0 and st.button("Clear Chat"):
        clear_chat("messages")


def config_page():
    get_api_key_if_missing()

    get_available_models()

    st.title("Configure knowledge base")
    if not is_user_logged_in():
        st.warning("You are not logged in. Newly created knowledge bases will be available for everyone.")

    try:
        indices = []
        indices_unfiltered = get_json("index-list.json")
        for index in indices_unfiltered:
            if index.startswith("index_") or index == "repo4euD21":
                indices.append(index)
        if is_user_logged_in():
            data = get_knowledgebases_per_user(st.session_state["user"])
            for base in data:
                indices.append(st.session_state["user"] + "_" + base[1])
    except Exception as e:
        # st.write(e)
        indices = []

    dip = indices + ["Create New"]
    if not st.session_state["knowledgebase"] == "Create New":
        chosen_base = dip.index(st.session_state["knowledgebase"])
    else:
        # default
        chosen_base = 0

    st.session_state["knowledgebase"] = st.selectbox("Select knowledge base", options=dip, index=chosen_base)

    # List of protected index names
    protected_indices = ["repo4euD21"]

    if st.session_state["knowledgebase"] == "Create New":
        with st.form(key="index"):
            st.write("##### Create a new knowledge base")
            files = st.file_uploader(
                "Step 1 - Upload files", type="pdf", accept_multiple_files=True
            )

            name = st.text_input("Step 2 - Choose a name for your index")
            index_name = "index_" + name
            user_name = st.session_state["user"] + "_" + name
            button = st.form_submit_button("Create Index")
            if index_name in indices or user_name in indices:
                st.warning("Please use an unique name!")
                st.stop()
            if button:
                try:
                    with st.spinner("Indexing"):
                        index = get_index_for_pdf(files, openai_api_key=st.session_state["key"])
                        if is_user_logged_in():
                            user_index = st.session_state["user"] + "_" + name
                            store_index_in_db(index, name=user_index)
                            indices = indices + [user_index]
                            store_data_as_json("index-list.json", indices)
                            add_knowledgebase(st.session_state["user"], name)
                        else:
                            index_name = "index_" + name
                            store_index_in_db(index, name=index_name)
                            indices = indices + [index_name]
                            store_data_as_json("index-list.json", indices)
                    st.success("Finished creating new index")
                    time.sleep(1)
                    st.experimental_rerun()
                except Exception as e:
                    # st.write(e)
                    st.error("Could not create new index. Check your OpenAI API key.")
    else:
        delete = st.button("Delete")

        if delete:
            # Only delete the files if the index is not protected
            if st.session_state["knowledgebase"] not in protected_indices:
                # Delete the files
                pkl_file = f"indexes/{st.session_state['knowledgebase']}.pkl"
                index_file = f"indexes/{st.session_state['knowledgebase']}.index"
                if os.path.exists(pkl_file):
                    os.remove(pkl_file)
                if os.path.exists(index_file):
                    os.remove(index_file)

                indices.remove(st.session_state["knowledgebase"])
                store_data_as_json("index-list.json", indices)
                data = st.session_state["knowledgebase"].split("_")
                base_name = st.session_state["knowledgebase"][len(data[0]) + 1:]
                delete_knowledgebase(data[0], base_name)
                st.success("Knowledgebase has been deleted successfully.")
                time.sleep(1)
            else:
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
    get_api_key_if_missing()

    available_models = get_available_models()
    selected_model = st.selectbox("Please select a model", options=available_models)

    chaintype = st.selectbox("Please select chain type", options=['stuff', "map_reduce", "refine"], index=0)
    default_k = 4
    selected_k = st.slider("k", min_value=1, max_value=50, value=default_k, step=1)
    default_fetch_k = 20
    selected_fetch_k = st.slider("fetch_k", min_value=1, max_value=50, value=default_fetch_k, step=1)
    show_sources = st.checkbox("Show texts in original docs", False)

    st.title("Academate")
    st.header("Questions and Answering with sources")

    if "knowledgebase" in st.session_state.keys() and len(st.session_state["knowledgebase"]) > 0:
        index = load_index_from_db(st.session_state["knowledgebase"])
    else:
        st.info("No knowledge base found. Please configure one!")
        st.stop()

    reproduce_chat_if_user_logged_in("messagesqanda")
    start_new_chat_if_empty("messagesqanda")
    print_current_chat("messagesqanda")

    prompt = get_user_message("messagesqanda")
    if prompt:
        with st.container():
            user_message(prompt)
            botmsg = bot_message("...", bot_name="Academate")

        # response possible because the API key was valid
        if openai.api_key and len(available_models) > 0:
            try:

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
                if is_user_logged_in():
                    save_message_in_db("messagesqanda", message)
            except Exception as e:
                # st.write(e)
                st.error("Something went wrong while producing a response.")
        # no response possible because the API key was not valid -> failure message
        else:
            failure_message = """
                        Hi there. You haven't provided me with an OpenAI API key that I can use. 
                        Please provide a key, so we can start chatting!
                        """
            message = {"role": "assistant", "content": failure_message}
            st.session_state["messagesqanda"].append(message)
            botmsg.update(failure_message)
            if is_user_logged_in():
                save_message_in_db("messagesqanda", message)
    if len(st.session_state["messagesqanda"]) != 0 and st.button("Clear Chat"):
        clear_chat("messagesqanda")


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
        st.warning("At least 10 characters are required for the API key!")
        st.stop()
    if "_" in st.session_state["user"] or len(st.session_state["user"]) < 4 or len(st.session_state["password"]) < 4:
        st.warning("You cannot use \"_\" in the username. Username and password need at least 4 digits.")
        st.stop()
    # signup possible if api key at least 10 characters long
    if st.button('SignUp'):
        # user does not exist yet and can be created
        if check_if_user_already_exists(st.session_state["user"]):
            add_userdata(st.session_state["user"], st.session_state["password"], st.session_state["key"])
            cookie_manager.set("user", st.session_state["user"])  # Expires in a day by default
            cookie_manager.get_all()
            st.success("You have successfully created an account. You are already logged in.")
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
        openai.api_key = data[0][2]
    if not is_user_logged_in():
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
    elif "user" in st.session_state.keys() and  "password" in st.session_state.keys() and len(st.session_state["user"]) > 0 and len(st.session_state["password"]) > 0:
        st.error("Incorrect login!")


def logout():
    cookie_manager.delete("user")
    cookie_manager.get_all()
    st.session_state["user"] = ""
    st.session_state["password"] = ""
    st.session_state["key"] = ""
    st.session_state["messages"] = []


def main():
    if "messages" not in st.session_state.keys() and "messagesqanda" not in st.session_state.keys():
        st.session_state["user"] = ""
        st.session_state["password"] = ""
        st.session_state["key"] = ""
        st.session_state["messages"] = []
        st.session_state["messagesqanda"] = []

        create_usertable()
        create_chattable()
        create_qandatable()
        create_knowledgebase()
    if "knowledgebase" not in st.session_state.keys():
        # default knowledge base
        st.session_state["knowledgebase"] = "repo4euD21"

    page = st.sidebar.selectbox(
        "Choose a page",
        ["Login", "Sign up", "Chatbot", "Q&A", "Configure knowledge base", "About"],
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
