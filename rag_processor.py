from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

load_dotenv()

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

        # Configure summarizer with sane defaults
        self.summarizer = HuggingFaceEndpoint(
            repo_id="mistralai/Mistral-7B-Instruct-v0.1",
            task="text-generation",
            max_new_tokens=380,   
            temperature=0.3,
            top_p=0.9,
            repetition_penalty=1.2,
            return_full_text=False,
            huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
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
            # hard cap on input length (in words)
            max_input_words = 1500
            words = text.split()
            if len(words) > max_input_words:
                text = " ".join(words[:max_input_words])

            prompt = (
                "You are a news assistant that writes clear, detailed summaries.\n\n"
                "Task: Read the full article below and write a concise news summary "
                "of 5 to 6 complete sentences (around 150–220 words).\n"
                "- Start with one sentence that states the main event or issue.\n"
                "- Then explain the most important facts, people/organizations involved, "
                "and any numbers, locations, or dates that matter.\n"
                "- End with 1 sentence on the impact, consequence, or what happens next.\n"
                "- Do NOT write bullet points. Do NOT add extra commentary.\n\n"
                f"ARTICLE:\n{text}\n\n"
                "Now write the summary:"
            )

            summary = self.summarizer.invoke(prompt)

            return summary.strip()

        except Exception as e:
            print("Summarize error:", e)
            return text[:250] + "..."

    def summarize_articles_bulk(self, articles):
        summarized = []

        for art in articles:
            # prefer full content, fall back to description
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

    