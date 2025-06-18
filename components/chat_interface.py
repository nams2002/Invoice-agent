import streamlit as st
from datetime import datetime

def render_chat_interface(llm_handler):
    """Render the chat interface"""
    st.markdown("### 💬 Invoice Assistant")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                st.caption(f"Sources: {', '.join(message['sources'])}")
    
    # Chat input
    if prompt := st.chat_input("Ask anything about your invoices..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = llm_handler.query_invoices(prompt)
                
                st.markdown(response["answer"])
                if response["sources"]:
                    st.caption(f"Sources: {', '.join(response['sources'])}")
                
                # Add assistant message to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response["answer"],
                    "sources": response["sources"]
                })
    
    # Quick actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Summarize All"):
            question = "Please provide a summary of all invoices including total count, total amount, and key vendors."
            process_quick_query(question, llm_handler)
    
    with col2:
        if st.button("💰 Total Amount"):
            question = "What is the total amount across all invoices?"
            process_quick_query(question, llm_handler)
    
    with col3:
        if st.button("📅 Date Range"):
            question = "What is the date range of all invoices?"
            process_quick_query(question, llm_handler)

def process_quick_query(question: str, llm_handler):
    """Process a quick query button click"""
    # Add to messages
    st.session_state.messages.append({"role": "user", "content": question})
    
    # Get response
    response = llm_handler.query_invoices(question)
    
    # Add response to messages
    st.session_state.messages.append({
        "role": "assistant",
        "content": response["answer"],
        "sources": response.get("sources", [])
    })
    
    # Rerun to update chat
    st.rerun()