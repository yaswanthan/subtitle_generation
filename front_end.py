import streamlit as st
import requests
from pathlib import Path
import os
from typing import Optional

# Configuration
FASTAPI_BASE_URL = "http://localhost:8000"
UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov"}

def init_session_state():
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = None
    if 'uploaded_file_path' not in st.session_state:
        st.session_state.uploaded_file_path = None
    if 'srt_updated' not in st.session_state:
        st.session_state.srt_updated = False

def is_allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

def upload_video_to_api(file) -> Optional[dict]:
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

def save_edited_subtitle(session_id: str, file_name: str, content: str) -> bool:
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/save-subtitle/",
            data={"session_id": session_id, "file_name": file_name, "content": content}
        )
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        st.error(f"Error saving subtitle: {str(e)}")
        return False

def finalize_full_srt(session_id: str) -> bool:
    try:
        response = requests.post(
            f"{FASTAPI_BASE_URL}/finalize-subtitles/",
            data={"session_id": session_id}
        )
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        st.error(f"Error finalizing full.srt: {str(e)}")
        return False

def display_video_player(video_path: str):
    if os.path.exists(video_path):
        with open(video_path, "rb") as video_file:
            video_bytes = video_file.read()
        st.video(video_bytes)
    else:
        st.error("Video file not found")

def main():
    st.set_page_config(page_title="Movie Subtitle Generator", page_icon="🎮", layout="wide")
    init_session_state()

    st.title("🎬 Movie Subtitle Generator")
    st.markdown("Upload your video and generate subtitles automatically!")

    with st.sidebar:
        st.header("Configuration")
        st.text_input("FastAPI Server URL", value=FASTAPI_BASE_URL)
        st.markdown("---")
        st.markdown("### Supported Formats\n• MP4\n• AVI\n• MKV\n• MOV")

    st.header("📤 Upload Video")

    uploaded_file = st.file_uploader("Choose a video file", type=['mp4', 'avi', 'mkv', 'mov'])
    email = st.text_input("Email Address", placeholder="your.email@example.com")

    if uploaded_file and email and st.button("🚀 Upload and Start Processing", type="primary"):
        if not is_allowed_file(uploaded_file.name):
            st.error("Invalid file type.")
        else:
            with st.spinner("Uploading video..."):
                result = upload_video_to_api(uploaded_file)
                if result:
                    st.session_state.session_id = result['uuid']
                    st.session_state.uploaded_file_path = result['file_path']
                    st.success(f"Uploaded! Session ID: {result['uuid']}")
                    with st.spinner("Processing..."):
                        process = process_video_api(result['uuid'], email)
                        if process:
                            st.session_state.processing_status = process
                            st.success("Processing completed!")

    if st.session_state.session_id:
        st.info(f"Session ID: {st.session_state.session_id}")

    if st.session_state.session_id and st.session_state.processing_status:
        st.header("📝 Review Subtitles")

        srt_dir = UPLOAD_DIR / st.session_state.session_id / "srt"
        chunk_dir = UPLOAD_DIR / st.session_state.session_id / "chunk"

        if srt_dir.exists() and chunk_dir.exists():
            srt_files = sorted(srt_dir.glob("*.srt"))
            chunk_files = sorted(chunk_dir.glob("*.mp4"))

            for srt_file, chunk_file in zip(srt_files, chunk_files):
                if srt_file.name == "full.srt":
                    continue

                st.markdown(f"---\n#### 📝 {srt_file.name}")

                col1, col2 = st.columns([1, 1])
                with col1:
                    display_video_player(str(chunk_file))
                with col2:
                    with open(srt_file, "r", encoding="utf-8") as f:
                        srt_text = f.read()
                    edited = st.text_area(
                        f"Edit - {srt_file.name}", value=srt_text, height=250, key=f"edit_{srt_file.name}"
                    )

                    if st.button(f"✅ Save {srt_file.name}", key=f"save_{srt_file.name}"):
                        success = save_edited_subtitle(
                            st.session_state.session_id,
                            srt_file.name,
                            edited
                        )
                        if success:
                            st.session_state.srt_updated = True
                            st.success(f"{srt_file.name} saved.")
                        else:
                            st.error(f"Failed to save {srt_file.name}.")

            if st.button("📂 Accept All & Generate full.srt"):
                if st.session_state.get("srt_updated", False):
                    if finalize_full_srt(st.session_state.session_id):
                        st.success("✅ full.srt generated.")
                        full_srt_path = srt_dir / "full.srt"
                        if full_srt_path.exists():
                            with open(full_srt_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            st.text_area("📄 full.srt Preview", content, height=300)
                            with open(full_srt_path, "rb") as f:
                                st.download_button("📅 Download full.srt", f.read(), "full.srt", mime="text/plain")
                    else:
                        st.error("Failed to generate full.srt.")
                else:
                    st.warning("No changes were made to subtitles. Please edit and save at least one chunk before finalizing.")

    st.markdown("---")
    st.markdown("### How it works:\n1. Upload your video\n2. Generate chunk subtitles\n3. Review & edit\n4. Merge to full.srt")

    if st.button("🔄 Start New Session"):
        for key in ['session_id', 'processing_status', 'uploaded_file_path', 'srt_updated']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()
