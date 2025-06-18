from typing import Dict, List
import openai
import json

# 1) Use ChatOpenAI and OpenAIEmbeddings from langchain_openai
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

# 2) Chroma still comes from langchain_community.vectorstores
from langchain_community.vectorstores import Chroma

# 3) Text splitting remains in langchain.text_splitter
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 4) ConversationalRetrievalChain still comes from langchain.chains
from langchain.chains import ConversationalRetrievalChain

from config.settings import settings


class LLMHandler:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

        # 1) Initialize the Chat model
        self.llm = ChatOpenAI(
            model_name=settings.OPENAI_MODEL,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
        )

        # 2) Initialize embeddings
        self.embeddings = OpenAIEmbeddings()

        # 3) Placeholders for vectorstore + QA chain (built later)
        self.vectorstore = None
        self.qa_chain = None

    def extract_structured_data(self, text: str, file_name: str) -> Dict:
        """Extract structured data from invoice text."""
        prompt = f"""
        Extract the following information from the invoice text below.
        Return the data in valid JSON format following this schema:
        {json.dumps(settings.INVOICE_SCHEMA, indent=2)}

        If a field is not found, use null.
        For dates, convert to YYYY-MM-DD format.
        For numbers, use numeric values without currency symbols.

        Invoice Text:
        {text}

        JSON Output:
        """

        try:
            response = openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert invoice data extractor. Always return valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.TEMPERATURE,
                max_tokens=settings.MAX_TOKENS
            )

            json_str = response.choices[0].message.content.strip()

            # Clean out triple-backticks if present
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]

            structured_data = json.loads(json_str)
            structured_data["source_file"] = file_name
            return structured_data

        except Exception as e:
            # If no JSON was ever produced, avoid referencing an undefined variable
            return {
                "error": str(e),
                "source_file": file_name,
                "raw_response": None
            }

    def create_vector_store(self, documents: List[Dict]):
        """Create vector store from processed invoices and build a QA chain."""
        texts: List[str] = []
        metadatas: List[Dict] = []

        for doc in documents:
            if "raw_text" in doc and doc["raw_text"]:
                # Split long text into chunks
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )
                chunks = splitter.split_text(doc["raw_text"])

                for chunk in chunks:
                    texts.append(chunk)
                    metadatas.append({
                        "source": doc["file_name"],
                        "file_path": doc.get("file_path", "")
                    })

        # Build Chroma vector store if we have any text chunks
        if texts:
            self.vectorstore = Chroma.from_texts(
                texts=texts,
                metadatas=metadatas,
                embedding=self.embeddings
            )

            # Build the ConversationalRetrievalChain now that vectorstore exists
            # Note: no `memory` argument → chain is stateless
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
                return_source_documents=True,
                output_key="answer"  # we'll still return 'answer' and 'source_documents'
            )

    def query_invoices(self, question: str) -> Dict:
        """Query the invoice knowledge base."""
        if not self.qa_chain:
            return {
                "answer": "No invoices have been processed yet. Please upload and process invoices first.",
                "sources": []
            }

        try:
            # Supply an empty list for chat_history with each invocation
            result = self.qa_chain.invoke({
                "question": question,
                "chat_history": []
            })

            # Extract unique source filenames
            sources: List[str] = []
            for doc in result.get("source_documents", []):
                src = doc.metadata.get("source")
                if src and src not in sources:
                    sources.append(src)

            return {
                "answer": result.get("answer", "No answer found."),
                "sources": sources
            }

        except Exception as e:
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": []
            }

    def analyze_invoices(self, structured_data: List[Dict]) -> Dict:
        """Analyze multiple invoices for insights."""
        if not structured_data:
            return {"error": "No structured data available"}

        prompt = f"""
        Analyze the following invoice data and provide insights:
        1. Total number of invoices
        2. Total amount across all invoices
        3. Average invoice amount
        4. Most frequent vendors
        5. Date range of invoices
        6. Any patterns or anomalies

        Invoice Data:
        {json.dumps(structured_data, indent=2)}

        Provide a comprehensive analysis:
        """

        try:
            response = openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a financial analyst expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.TEMPERATURE
            )

            return {
                "analysis": response.choices[0].message.content,
                "invoice_count": len(structured_data)
            }

        except Exception as e:
            return {"error": str(e)}
