# backend/rag_processor.py
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.output_parsers import StrOutputParser

class RAGProcessor:
    def __init__(self, persist_directory="./chroma_db"):
        # embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        self.persist_directory = persist_directory
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len
        )

        # summarizer endpoint (Hugging Face Inference API wrapper via langchain-huggingface)
        self.summarizer = (HuggingFaceEndpoint(
            repo_id="facebook/bart-large-cnn",
            task="summarization",
            max_length=150,
            min_length=50,
            temperature=0.3
        ) | StrOutputParser())

    def process_articles(self, articles):
        documents = []
        for article in articles:
            doc = Document(
                page_content=f"Title: {article.get('title','')}\n\n{article.get('content','')}",
                metadata={
                    'title': article.get('title', ''),
                    'source': article.get('source', ''),
                    'url': article.get('url', ''),
                    'published': article.get('published', ''),
                    'image': article.get('image', '')
                }
            )
            documents.append(doc)

        split_docs = self.text_splitter.split_documents(documents)

        vectorstore = Chroma.from_documents(
    documents=split_docs,
    embedding=self.embeddings,
    persist_directory=self.persist_directory
)
        return vectorstore


    def load_vectorstore(self):
        try:
            return Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        except Exception:
            return None

    def retrieve_relevant_articles(self, query, k=5):
        vectorstore = self.load_vectorstore()
        if vectorstore:
            return vectorstore.similarity_search(query, k=k)
        return []

    def summarize_article(self, text, max_length=150, min_length=50):
        try:
            max_input = 3000
            words = text.split()
            if len(words) > max_input:
                text = " ".join(words[:max_input])

            summary = self.summarizer.invoke({
                "inputs": text,
                "parameters": {
                    "max_length": max_length,
                    "min_length": min_length,
                    "temperature": 0.2
                }
            })
            return summary
        except Exception as e:
            print("Summarize error:", e)
            return text[:200] + "..."
