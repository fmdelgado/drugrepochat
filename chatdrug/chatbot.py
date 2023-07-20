import openai
import os
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

openai.api_key = "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"
os.environ["OPENAI_API_KEY"] = openai.api_key


def generate_response(prompt):
    try:
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=prompt,
            max_tokens=150
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return str(e)


class ChatBot:
    def __init__(self, vectordb):
        self.vectordb = vectordb
        self.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key
        self.qa_chain = RetrievalQA.from_chain_type(llm=ChatOpenAI(temperature=0.0, model='gpt-3.5-turbo'),
                                                    chain_type="refine",
                                                    retriever=self.vectordb.as_retriever(),
                                                    return_source_documents=True,
                                                    verbose=True)

    # Cite sources
    @staticmethod
    def process_llm_response(llm_response):
        result_str = llm_response['result']
        sources_str = '\n\nSources:\n'
        for source in llm_response["source_documents"]:
            sources_str += source.metadata['DOI'] + '\n'

        return result_str + sources_str

    def generate_contextual_response(self, prompt):
        try:
            llm_response = self.qa_chain(prompt)
            return self.process_llm_response(llm_response)

        except Exception as e:
            return str(e)
