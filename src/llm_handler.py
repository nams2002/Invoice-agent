# src/llm_handler.py

from typing import Dict, List, Optional
import os
import json

import openai
from langchain.llms import OpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain

from config.settings import settings


class LLMHandler:
    def __init__(self):
        # ──── OPENAI KEY & OPTIONAL PROXY ─────────────────────────────────────────
        openai.api_key = settings.OPENAI_API_KEY

        # If you’ve set OPENAI_PROXY in your settings (or secrets),
        # export it so that the underlying HTTP client picks it up.
        # Proxy configuration temporarily disabled for Streamlit Cloud compatibility
        # proxy = getattr(settings, "OPENAI_PROXY", None)
        # if proxy:
        #     os.environ["HTTP_PROXY"]  = proxy
        #     os.environ["HTTPS_PROXY"] = proxy

        # ──── INITIALIZE LLM & EMBEDDINGS ────────────────────────────────────────
        self.llm = OpenAI(
            model_name=settings.OPENAI_MODEL,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY
        )

        # ──── PLACEHOLDERS FOR VECTORSTORE + QA CHAIN ────────────────────────────
        self.vectorstore: Optional[Chroma] = None
        self.qa_chain:   Optional[ConversationalRetrievalChain] = None


    def extract_structured_data(self, text: str, file_name: str) -> Dict:
        """Extract structured JSON from raw invoice text."""
        system = {
            "role":    "system",
            "content": "You are an expert invoice data extractor. Always return valid JSON."
        }
        user = {
            "role":    "user",
            "content": (
                f"Extract the following fields from this invoice, returning _only_ valid JSON "
                f"matching this schema:\n{json.dumps(settings.INVOICE_SCHEMA, indent=2)}\n\n"
                f"Invoice Text:\n{text}\n\n"
                f"JSON Output:"
            )
        }

        resp = self.llm.invoke([system, user])
        json_str = resp.content.strip()

        # strip ```json fences if present
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return {
                "error":        f"JSON parse error: {e}",
                "raw_response": resp.content,
                "source_file":  file_name
            }

        data["source_file"] = file_name
        return data


    def create_vector_store(self, documents: List[Dict]) -> None:
        """Chunk texts, embed with Chroma, and build a QA chain."""
        texts:     List[str] = []
        metadatas: List[Dict] = []
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

        for doc in documents:
            raw = doc.get("raw_text") or ""
            for chunk in splitter.split_text(raw):
                texts.append(chunk)
                metadatas.append({
                    "source":    doc["file_name"],
                    "file_path": doc.get("file_path", "")
                })

        if not texts:
            return

        self.vectorstore = Chroma.from_texts(
            texts=texts,
            metadatas=metadatas,
            embedding=self.embeddings
        )
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True,
            output_key="answer"
        )


    def query_invoices(self, question: str) -> Dict:
        """Run a stateless QA query against the processed invoices."""
        if not self.qa_chain:
            return {
                "answer": "No invoices processed yet. Please upload & process first.",
                "sources": []
            }

        result = self.qa_chain({"question": question, "chat_history": []})
        answer = result.get("answer", "")
        docs   = result.get("source_documents", [])

        sources: List[str] = []
        for d in docs:
            src = d.metadata.get("source")
            if src and src not in sources:
                sources.append(src)

        return {"answer": answer, "sources": sources}


    def analyze_invoices(self, structured_data: List[Dict]) -> Dict:
        """Produce aggregate insights over multiple invoices."""
        if not structured_data:
            return {"error": "No structured data available"}

        prompt = (
            "You are a financial analyst. Given this list of invoices (JSON), please provide:\n"
            "1. Total number of invoices\n"
            "2. Sum of all invoice totals\n"
            "3. Average invoice amount\n"
            "4. Top vendors by frequency\n"
            "5. Date range covered\n"
            "6. Any detected anomalies or patterns\n\n"
            f"Data:\n{json.dumps(structured_data, indent=2)}\n\n"
            "Analysis:"
        )
        resp = self.llm.invoke([
            {"role": "system", "content": "You are a financial analyst."},
            {"role": "user",   "content": prompt}
        ])
        return {
            "analysis":      resp.content,
            "invoice_count": len(structured_data),
        }
