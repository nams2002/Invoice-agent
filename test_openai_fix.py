"""
Test script to verify OpenAI and LangChain compatibility
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from langchain.llms import OpenAI
    from langchain.embeddings import OpenAIEmbeddings
    print("✅ Successfully imported langchain components")

    # Test OpenAI initialization
    if os.getenv("OPENAI_API_KEY"):
        llm = OpenAI(
            model_name="gpt-3.5-turbo-instruct",
            temperature=0.1,
            max_tokens=1000,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        print("✅ Successfully initialized OpenAI LLM")

        embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        print("✅ Successfully initialized OpenAIEmbeddings")
    else:
        print("⚠️ OPENAI_API_KEY not found in environment")

except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e)}")
