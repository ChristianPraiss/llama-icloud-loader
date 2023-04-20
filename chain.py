import os
import streamlit as st
from langchain.chat_models import ChatOpenAI

from llama_index import GPTSimpleVectorIndex, SimpleDirectoryReader, LLMPredictor, PromptHelper, ServiceContext
from langchain import OpenAI

# set service context
llm_predictor_gpt4 = LLMPredictor(
    llm=ChatOpenAI(temperature=0, model_name="gpt-4"))
service_context = ServiceContext.from_defaults(
    llm_predictor=llm_predictor_gpt4, chunk_size_limit=1024
)
# Load documents from the 'data' directory
documents = SimpleDirectoryReader('downloaded_pdfs').load_data()

index = GPTSimpleVectorIndex.from_documents(
    documents, service_context=service_context)
# Define a simple Streamlit app
st.title("Ask Llama")

query = st.text_input("What would you like to ask?", "")

if st.button("Submit"):
    response = index.query(query)
    st.write(response)
