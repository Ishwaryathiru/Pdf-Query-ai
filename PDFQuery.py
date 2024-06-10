import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def get_pdf_text(pdf):
    text = ""
    pr = PdfReader(pdf)
    for pg in pr.pages:
        text += pg.extract_text()
    return text

def get_text_chunks(text):
    ts = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)
    chunks = ts.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    emb = GoogleGenerativeAIEmbeddings(model='models/embedding-001')
    vs = FAISS.from_texts(text_chunks, embedding=emb)
    vs.save_local('uploaded_pdf')

def get_conversational_chain():
    prmt_temp = """
    Answer the question as detailed as possible from the provided context. 
    If the answer is not found in the context, just say "Unable to find the answer", don't provide a wrong answer.

    context:\n{context}\n
    Question:\n{question}\n
    Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
    prompt = PromptTemplate(template=prmt_temp, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def user_input(ques):
    emb = GoogleGenerativeAIEmbeddings(model='models/embedding-001')
    new_db = FAISS.load_local('uploaded_pdf', emb, allow_dangerous_deserialization=True)
    dox = new_db.similarity_search(ques)
    chain = get_conversational_chain()
    res = chain.invoke(
        {"input_documents": dox, "question": ques},
    )
    print("Answer:", res["output_text"])
text = get_pdf_text('cursor and trigger.pdf')
chunks = get_text_chunks(text)
get_vector_store(chunks)
ques = input('Enter question: ')
user_input(ques)
