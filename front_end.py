import streamlit as st
import requests
import uuid
import shutil
from pathlib import Path
import time
import os
from typing import Optional
import subprocess

# Configuration
FASTAPI_BASE_URL = "http://localhost:8000"  # Adjust this to your FastAPI server URL
UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov"}

def init_session_state():
    """Initialize session state variables"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = None
    if 'uploaded_file_path' not in st.session_state:
        st.session_state.uploaded_file_path = None

def is_allowed_file(filename: str) -> bool:
    """Check if uploaded file has allowed extension"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

def upload_video_to_api(file) -> Optional[dict]:
    """Upload video file to FastAPI backend"""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        response = requests.post(f"{FASTAPI_BASE_URL}/upload/", files=files)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Upload failed: {response.json().get('detail', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return None

def process_video_api(session_id: str, email: str) -> Optional[dict]:
    """Process video through FastAPI backend"""
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/process",
            params={"session_id": session_id, "mail": email}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Processing failed: {response.json().get('detail', 'Unknown error')}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return None

def display_video_player(video_path: str):
    """Display video player"""
    if os.path.exists(video_path):
        with open(video_path, "rb") as video_file:
            video_bytes = video_file.read()
        st.video(video_bytes)
    else:
        st.error("Video file not found")

def display_subtitle_content(srt_path: str):
    """Display subtitle content"""
    if os.path.exists(srt_path):
        with open(srt_path, "r", encoding="utf-8") as srt_file:
            content = srt_file.read()
        st.text_area("Subtitle Content:", content, height=300)
        
        # Download button for subtitle file
        with open(srt_path, "rb") as file:
            st.download_button(
                label="Download Subtitle File",
                data=file.read(),
                file_name=os.path.basename(srt_path),
                mime="text/plain"
            )
    else:
        st.error("Subtitle file not found")

def main():
    st.set_page_config(
        page_title="Video Subtitle Generator",
        page_icon="🎬",
        layout="wide"
    )
    
    # Initialize session state
    init_session_state()
    
    # Header
    st.title("🎬 Video Subtitle Generator")
    st.markdown("Upload your video and generate subtitles automatically!")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        fastapi_url = st.text_input("FastAPI Server URL", value=FASTAPI_BASE_URL)
        st.markdown("---")
        st.markdown("### Supported Formats")
        st.markdown("• MP4\n• AVI\n• MKV\n• MOV")
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📤 Upload Video")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a video file",
            type=['mp4', 'avi', 'mkv', 'mov'],
            help="Upload a video file to generate subtitles"
        )
        
        # Email input
        email = st.text_input(
            "Email Address",
            placeholder="your.email@example.com",
            help="Email to receive subtitle completion notification"
        )
        
        # Upload button
        if uploaded_file is not None and email:
            if st.button("🚀 Upload and Start Processing", type="primary"):
                if not is_allowed_file(uploaded_file.name):
                    st.error("Invalid file type. Please upload MP4, AVI, MKV, or MOV files.")
                else:
                    with st.spinner("Uploading video..."):
                        upload_result = upload_video_to_api(uploaded_file)
                        
                        if upload_result:
                            st.session_state.session_id = upload_result['uuid']
                            st.session_state.uploaded_file_path = upload_result['file_path']
                            st.success(f"✅ Upload successful! Session ID: {upload_result['uuid']}")
                            
                            # Start processing
                            with st.spinner("Processing video... This may take a while."):
                                process_result = process_video_api(
                                    st.session_state.session_id, 
                                    email
                                )
                                
                                if process_result:
                                    st.session_state.processing_status = process_result
                                    st.success("✅ Processing completed!")
                                    st.balloons()
                                else:
                                    st.error("❌ Processing failed")
        
        # Session info
        if st.session_state.session_id:
            st.info(f"Current Session ID: {st.session_state.session_id}")
    
    with col2:
        st.header("📊 Processing Status")
        
        if st.session_state.processing_status:
            status = st.session_state.processing_status
            
            # Display processing statistics
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                st.metric("Video Chunks", status.get('Total_video_chunk', 0))
            with col2_2:
                st.metric("Subtitle Chunks", status.get('Total_subtitle_chunk', 0))
            
            st.success(status.get('message', 'Processing completed'))
        else:
            st.info("Upload a video to see processing status")
    
    # Results section
    if st.session_state.session_id and st.session_state.processing_status:
        st.header("🎥 Results")
        
        # Tabs for video and subtitles
        tab1, tab2 = st.tabs(["📹 Video Player", "📝 Subtitles"])
        
        with tab1:
            if st.session_state.uploaded_file_path:
                st.subheader("Original Video")
                display_video_player(st.session_state.uploaded_file_path)
                
                # Show video chunks if available
                session_path = UPLOAD_DIR / st.session_state.session_id
                chunk_dir = session_path / "chunk"
                if chunk_dir.exists():
                    chunks = list(chunk_dir.glob("*.mp4"))
                    if chunks:
                        st.subheader("Video Chunks")
                        chunk_names = [chunk.name for chunk in chunks]
                        selected_chunk = st.selectbox("Select a chunk to view:", chunk_names)
                        if selected_chunk:
                            selected_chunk_path = chunk_dir / selected_chunk
                            display_video_player(str(selected_chunk_path))
        
        with tab2:
            session_path = UPLOAD_DIR / st.session_state.session_id
            
            # Look for merged SRT file
            merged_srt = session_path / "merged_subtitles.srt"
            if merged_srt.exists():
                st.subheader("Complete Subtitles")
                display_subtitle_content(str(merged_srt))
            else:
                # Show individual SRT chunks
                srt_dir = session_path / "srt"
                if srt_dir.exists():
                    srt_files = list(srt_dir.glob("*.srt"))
                    if srt_files:
                        st.subheader("Subtitle Chunks")
                        srt_names = [srt.name for srt in srt_files]
                        selected_srt = st.selectbox("Select a subtitle chunk:", srt_names)
                        if selected_srt:
                            selected_srt_path = srt_dir / selected_srt
                            display_subtitle_content(str(selected_srt_path))
                    else:
                        st.info("No subtitle files found yet.")
    
    # Footer
    st.markdown("---")
    st.markdown("### How it works:")
    st.markdown("""
    1. **Upload**: Select your video file and provide your email
    2. **Processing**: The video is split into chunks and processed with Whisper for transcription
    3. **Results**: View your video with generated subtitles and download the SRT file
    4. **Notification**: Receive an email when processing is complete
    """)
    
    # Clear session button
    if st.button("🔄 Start New Session"):
        for key in ['session_id', 'processing_status', 'uploaded_file_path']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()