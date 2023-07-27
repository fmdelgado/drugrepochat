# Drug Repurposing Chatbot

The Drug Repurposing Chatbot is an application powered by OpenAI's GPT-3.5-turbo model. It uses a knowledge base derived from various scientific documents related to drug repurposing to provide users with detailed insights and answers to their questions.

## Key Features

- **User-friendly Interface**: Users can communicate with the chatbot by typing their questions and receive answers instantly.
- **Customizable Knowledge Base**: Users have the ability to configure the knowledge base by uploading their own set of documents in the "Configure Knowledge Base" page.
- **OpenAI GPT-3.5-turbo**: Leveraging the power of OpenAI's GPT-3.5-turbo model, the chatbot can provide more relevant and detailed responses.

## Usage

1. Run the Python script.
2. Enter your OpenAI API key when prompted.
3. Use the sidebar to navigate between the Chatbot and Configure Knowledge Base pages.
4. On the Chatbot page, type your question and hit Enter.
5. The chatbot will provide a response based on the knowledge base.
6. On the Configure Knowledge Base page, you can upload your own documents (PDFs only) and choose a name for your knowledge base.

## Configuration

To configure the knowledge base, navigate to the "Configure Knowledge Base" page. Here, you can upload PDFs which will be used to form the new knowledge base. You can also select an existing knowledge base or delete one.

Please note: A few knowledge bases are protected and cannot be deleted.

This application requires your OpenAI API key. Please ensure that you have it ready before using the chatbot.

## Note

This project uses Streamlit for the frontend and OpenAI for the backend. Please make sure you have both installed and properly configured.