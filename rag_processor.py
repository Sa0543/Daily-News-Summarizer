from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.output_parsers import StrOutputParser
import os

class RAGProcessor:
    def __init__(self, persist_directory="./chroma_db"):

        # Embeddings
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

        self.summarizer = (
            HuggingFaceEndpoint(
                repo_id="mistralai/Mistral-7B-Instruct",
                task="text-generation",
        )
    )

    # Vector index builder
    def process_articles(self, articles):
        documents = []
        for article in articles:
            documents.append(
                Document(
                    page_content=f"Title: {article.get('title','')}\n\n{article.get('content','')}",
                    metadata={
                        'title': article.get('title', ''),
                        'source': article.get('source', ''),
                        'url': article.get('url', ''),
                        'published': article.get('published', ''),
                        'image': article.get('image', '')
                    }
                )
            )

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

    
    def summarize_article(self, text, max_length=200, min_length=120):
        try:
            # Trim very long text
            max_input = 3000
            words = text.split()
            if len(words) > max_input:
                text = " ".join(words[:max_input])

            # Summarizer ALWAYS expects a STRING — NOT dict
            prompt = (
                "Summarize the following news article in 5–6 detailed sentences. "
                "Include main issue, key facts, people involved, and impact. "
                "Avoid generic or shallow summaries.\n\n"
                f"ARTICLE:\n{text}\n\n"
                "SUMMARY:"
            )

            summary = self.summarizer.invoke(
                prompt,
                 params={
                        "max_new_tokens": 500,
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "repetition_penalty": 1.2
            }
            )
            return summary.strip()

        except Exception as e:
            print("Summarize error:", e)
            return text[:250] + "..."

    def summarize_articles_bulk(self, articles):
        summarized = []

        for art in articles:
            text = art.get("content") or art.get("description")
            if not text:
                continue

            summary = self.summarize_article(text)

            summarized.append({
                "title": art["title"],
                "summary": summary,
                "source": art["source"],
                "url": art["url"],
                "image": art.get("image"),
                "category": art.get("category"),
                "published": art.get("published")
            })

        return summarized
