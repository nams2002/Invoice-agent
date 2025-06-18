import streamlit as st
from src.drive_handler import DriveHandler
from src.utils import cleanup_temp_files
import os
from config.settings import settings

def render_sidebar():
    """Render the sidebar with input options"""
    st.sidebar.title("📄 Invoice Extractor")
    
    # Input method selection
    input_method = st.sidebar.radio(
        "Choose input method:",
        ["Google Drive Link", "Local Upload"]
    )
    
    files_to_process = []
    
    if input_method == "Google Drive Link":
        st.sidebar.markdown("### Google Drive Input")
        drive_url = st.sidebar.text_input(
            "Enter Google Drive link:",
            placeholder="https://drive.google.com/file/d/..."
        )
        
        if st.sidebar.button("Load from Drive"):
            if drive_url:
                with st.spinner("Downloading from Google Drive..."):
                    try:
                        drive_handler = DriveHandler()
                        
                        # Validate link
                        if not drive_handler.validate_link(drive_url):
                            st.sidebar.error("Invalid Google Drive link!")
                            return []
                        
                        # Extract file ID and type
                        file_id, file_type = drive_handler.extract_file_id(drive_url)
                        
                        if not file_id:
                            st.sidebar.error("Could not extract file ID from the link!")
                            return []
                        
                        if file_type == 'folder':
                            st.sidebar.warning(
                                "Folder downloads are not supported yet. "
                                "Please share individual files instead."
                            )
                            return []
                        
                        # Download file
                        file_path = drive_handler.download_file(file_id)
                        files_to_process = [file_path]
                        st.sidebar.success(f"Downloaded 1 file successfully!")
                        st.session_state['files_to_process'] = files_to_process
                        
                    except Exception as e:
                        st.sidebar.error(f"Error: {str(e)}")
            else:
                st.sidebar.warning("Please enter a Google Drive link")
    
    else:  # Local Upload
        st.sidebar.markdown("### Local File Upload")
        uploaded_files = st.sidebar.file_uploader(
            "Choose invoice files",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            # Save uploaded files temporarily
            cleanup_temp_files()
            temp_paths = []
            
            for uploaded_file in uploaded_files:
                file_path = os.path.join(settings.TEMP_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                temp_paths.append(file_path)
            
            st.session_state['files_to_process'] = temp_paths
            st.sidebar.success(f"Uploaded {len(uploaded_files)} file(s)")
    
    # Processing options
    st.sidebar.markdown("### Processing Options")
    
    extract_data = st.sidebar.checkbox("Extract Structured Data", value=True)
    create_kb = st.sidebar.checkbox("Create Knowledge Base", value=True)
    
    # Export options
    st.sidebar.markdown("### Export Options")
    export_format = st.sidebar.selectbox(
        "Export format:",
        ["JSON", "CSV", "Both"]
    )
    
    return {
        'extract_data': extract_data,
        'create_kb': create_kb,
        'export_format': export_format
    }