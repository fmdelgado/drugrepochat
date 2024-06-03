#!/Users/fernando/opt/anaconda3/envs/drugrepochat/bin/python
"""
Example LangChain Server that runs a local LLM.

**Attention** This is OK for prototyping/dev usage, but should not be used
for production cases when there might be concurrent requests from different
users. As of the time of writing, Ollama is designed for single users and cannot
handle concurrent requests. See this issue:
https://github.com/ollama/ollama/issues/358

When deploying local models, make sure you understand whether the model can
handle concurrent requests or not. If concurrent requests are not handled
properly, the server will either crash or just not handle more than one user at a time.
"""
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Union
from langserve import add_routes
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, AIMessage, SystemMessage
import requests, json
from langchain_community.vectorstores import FAISS
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
import os
from os.path import join, dirname

from dotenv import load_dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = FastAPI(
    title="DrugRepoChatter Server",
    version="1.0",
    description="Spin up a simple API server using DrugRepoChatter",
)

# Root route to handle requests to "/"
@app.get("/")
async def root():
    return {"message": "Welcome to DrugRepoChatter Server!"}

# Define the playground route
@app.get("/ollama/playground/")
async def playground():
    return {"message": "Welcome to the Ollama Playground!"}

PROMPT_TEMPLATE = """Answer the question based only on the following context:
                    {context}
                    You are allowed to rephrase the answer based on the context.
                    Do not answer any questions using your pre-trained knowledge, only use the information provided in the context.
                    Do not answer any questions that do not relate to drug repurposing, omics data, bioinformatics, and data analysis.
                    Question: {question}
                  """
PROMPT = PromptTemplate.from_template(PROMPT_TEMPLATE)
protocol = os.getenv('protocol_ollama')
hostname = os.getenv('hostname_ollama')
host = f"{protocol}://{hostname}"
suffix = os.getenv('auth_url_suffix_ollama')
auth_url = f"{host}/{suffix}"
suffix = os.getenv('api_url_suffix_ollama')
api_url = f"{host}/{suffix}"
account = {'email': os.getenv('ollama_user'), 'password': os.getenv('ollama_pw')}
auth_response = requests.post(auth_url, json=account)
jwt = json.loads(auth_response.text)["token"]

modelname = os.getenv('ollama_model')
selected_fetch_k = 20
selected_k = 3
path_name = "/Users/fernando/Documents/Research/drugrepochat/app/indexes/repo4euD21openaccess"

ollama_embeddings = OllamaEmbeddings(base_url=api_url, model="nomic-embed-text", headers={"Authorization": "Bearer " + jwt})
ollama_llm = Ollama(base_url=api_url, model=modelname, temperature=0.0, headers={"Authorization": "Bearer " + jwt})

# Check if the LLM is working
# response = ollama_llm.invoke("hello")
# print(response)

index = FAISS.load_local(path_name, ollama_embeddings, allow_dangerous_deserialization=True)

qa_chain = RetrievalQA.from_chain_type(
    llm=ollama_llm,
    chain_type="stuff",
    chain_type_kwargs={"prompt": PROMPT},
    retriever=index.as_retriever(search_type="mmr",
                                 search_kwargs={'fetch_k': selected_fetch_k, 'k': selected_k}),
    return_source_documents=True
)

class InputChat(BaseModel):
    """Input for the chat endpoint."""
    query: str = Field(..., description="The query to retrieve relevant documents.")
    messages: List[Union[HumanMessage, AIMessage, SystemMessage]] = Field(
        ...,
        description="The chat messages representing the current conversation.",
    )


add_routes(
    app,
    qa_chain.with_types(input_type=InputChat),
    enable_feedback_endpoint=True,
    enable_public_trace_link_endpoint=True,
    playground_type="default",
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)

# To run the server, execute the following command in the terminal:
# python drugrepochatter_langserve.py
# The server will be running at http://localhost:8000
# You can access the playground at http://localhost:8000/ollama/playground/
# To stop the server, press Ctrl+C in the terminal where the server is running.
# You can also run the server in the background by adding an ampersand (&) at the end of the command:
# python drugrepochatter_langserve.py &
# To stop the server running in the background, you can use the following command:
# killall python
# This will stop all Python processes running in the background.
# If you have multiple Python processes running, you can stop a specific process by using the following command:
# ps aux | grep drugrepochatter_langserve.py
# This command will show the process ID (PID) of the Python process running the server.
# You can then use the following command to stop the specific process:
# kill -9 PID
