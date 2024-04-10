
<p align="center">
  <img src="https://github.com/fmdelgado/drugrepochat/blob/fix-bugs-db-update/app/img/logo.png" width="200"/>
</p>

# DrugRepoChatter: AI-Powered Assistant for Academic Research in Drug Discovery

## Description

DrugRepoChatter aims to assist researchers in finding relevant information within a large corpus of scientific documents.

## Configuration

To configure the knowledge base, navigate to the "Configure Knowledge Base" page. Here, you can upload PDFs which will be used to form the new knowledge base. You can also select an existing knowledge base or delete one.

**Note**: A few knowledge bases are protected and cannot be deleted.

## Requirements

- OpenAI API key for backend services.
- Streamlit for the frontend interface.

## Installation

1. Clone the repository.
2. Navigate to the app directory.
3. Run ```docker-compose --env-file env_drugrepochat.env up```
