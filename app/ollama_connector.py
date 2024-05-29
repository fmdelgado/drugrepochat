import requests, json
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings

protocol = "https"
hostname = "chat.cosy.bio"
host = f"{protocol}://{hostname}"
auth_url = f"{host}/api/v1/auths/signin"
api_url = f"{host}/ollama"

account = {'email': "drugrepochatter@mailinator.com", 'password': "DrugRepoChatter"}
auth_response = requests.post(auth_url, json=account)
jwt = json.loads(auth_response.text)["token"]


ollama_embeddings = OllamaEmbeddings(base_url=api_url, model="nomic-embed-text", headers={"Authorization": "Bearer " + jwt})
ollama_llm = Ollama(base_url=api_url, model= 'llama3', temperature=0.0, headers={"Authorization": "Bearer " + jwt})