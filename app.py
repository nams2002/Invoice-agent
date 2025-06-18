import streamlit as st
import os
from config.settings import settings
from src.drive_handler import DriveHandler
from src.invoice_processor import InvoiceProcessor
from src.llm_handler import LLMHandler
from src.data_extractor import DataExtractor
from src.utils import cleanup_temp_files
from components.sidebar import render_sidebar
from components.chat_interface import render_chat_interface
from components.data_viewer import render_data_viewer

# Page configuration
st.set_page_config(
    page_title=settings.PAGE_TITLE,
    page_icon=settings.PAGE_ICON,
    layout=settings.LAYOUT
)

# Initialize session state
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = []
if 'structured_data' not in st.session_state:
    st.session_state.structured_data = []
if 'llm_handler' not in st.session_state:
    st.session_state.llm_handler = LLMHandler()
if 'files_to_process' not in st.session_state:
    st.session_state.files_to_process = []

def main():
    # Title and description
    st.title("🧾 Smart Invoice Extractor System")
    st.markdown("""
    Extract structured data from invoices, ask questions about your documents, 
    and export data in various formats. Supports PDF and image files from Google Drive or local uploads.
    """)
    
    # Render sidebar and get options
    sidebar_options = render_sidebar()
    
    # Main content area
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.markdown("### 📤 Process Invoices")
        
        if st.button("🚀 Process Files", type="primary", disabled=not st.session_state.files_to_process):
            process_invoices(sidebar_options)
        
        if st.session_state.processed_data:
            st.success(f"✅ Processed {len(st.session_state.processed_data)} invoice(s)")
            
            # Show processing summary
            with st.expander("Processing Summary"):
                for doc in st.session_state.processed_data:
                    if "error" in doc:
                        st.error(f"❌ {doc['file_name']}: {doc['error']}")
                    else:
                        st.success(f"✅ {doc['file_name']}")
    
    with col2:
        if st.session_state.processed_data:
            # Chat interface
            render_chat_interface(st.session_state.llm_handler)
    
    # Data viewer section
    if st.session_state.structured_data:
        st.markdown("---")
        aggregated_data = DataExtractor().aggregate_data(st.session_state.structured_data)
        render_data_viewer(st.session_state.structured_data, aggregated_data)

def process_invoices(options):
    """Process uploaded invoices"""
    with st.spinner("Processing invoices..."):
        try:
            # Initialize processors
            processor = InvoiceProcessor()
            
            # Process files
            processed_docs = processor.process_multiple_files(st.session_state.files_to_process)
            st.session_state.processed_data = processed_docs
            
            # Extract structured data if enabled
            if options['extract_data']:
                structured_data = []
                progress_bar = st.progress(0)
                
                for i, doc in enumerate(processed_docs):
                    if "error" not in doc and "raw_text" in doc:
                        # Extract structured data using LLM
                        extracted = st.session_state.llm_handler.extract_structured_data(
                            doc["raw_text"],
                            doc["file_name"]
                        )
                        structured_data.append(extracted)
                    
                    progress_bar.progress((i + 1) / len(processed_docs))
                
                st.session_state.structured_data = structured_data
                progress_bar.empty()
            
            # Create knowledge base if enabled
            if options['create_kb'] and st.session_state.processed_data:
                with st.spinner("Creating knowledge base..."):
                    st.session_state.llm_handler.create_vector_store(st.session_state.processed_data)
                    st.success("✅ Knowledge base created successfully!")
            
            # Clean up temporary files
            cleanup_temp_files()
            st.session_state.files_to_process = []
            
        except Exception as e:
            st.error(f"Error processing invoices: {str(e)}")

def check_api_key():
    """Check if OpenAI API key is configured"""
    if not settings.OPENAI_API_KEY:
        st.error("⚠️ OpenAI API key not found! Please add it to your .env file.")
        st.code("OPENAI_API_KEY=your_api_key_here", language="bash")
        st.stop()

if __name__ == "__main__":
    # Check API key
    check_api_key()
    
    # Create necessary directories
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    os.makedirs(settings.EXPORT_DIR, exist_ok=True)
    
    # Run main app
    main()