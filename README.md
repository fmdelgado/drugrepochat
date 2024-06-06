Here is the generated README file:

<p align="center">
   <img src="https://github.com/fmdelgado/drugrepochat/blob/fix-bugs-db-update/app/img/logo.png" width="200"/>
</p>

# DrugRepoChatter: AI-Powered Assistant for Academic Research in Drug Discovery

## Introduction
The challenge of keeping pace with the exponential growth of scientific literature is a significant obstacle in drug discovery research. To address this challenge, we have developed DrugRepoChatter, an AI-powered assistant designed to facilitate efficient and accurate information retrieval within a large corpus of scientific documents.

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
3. Run `docker-compose --env-file env up` (Use the `env_ prod` file provided, rename it to `.env`, and place it in the app directory).

**Note**: In the terminal where you ran the docker-compose command, some logs may occur, but they shouldn’t be of your concern as long as the application is running properly. In the beginning, you might have to wait a bit until everything has loaded.

## Running the Application
1. Go to your browser and open `localhost` on port `8501`, where the application should be running.

## Acknowledgements
Availability of supporting data: Not applicable.

Code availability: https://github.com/fmdelgado/drugrepochat

Competing interests: The authors declare no conflicts of interest.

Funding: This work is supported by the European Union’s Horizon Europe research and innovation programme under grant agreement No. 101057619.