import uuid
import shutil
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from preprocess.functions import split_video
from preprocess.subtitle import translate_chunks_to_srt,merge_srt_chunks
from preprocess.mail import send_subtitle_completion_email

app = FastAPI()

# Base upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed video formats
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov"}

def is_allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

@app.post("/upload/")
async def upload_video(file: UploadFile = File(...)):
    # Validate file extension
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Allowed: .mp4, .avi, .mkv, .mov"
        )

    # Generate a unique session ID and create its folder
    unique_id = str(uuid.uuid4())
    session_dir = UPLOAD_DIR / unique_id / "original_file"
    session_dir.mkdir(parents=True, exist_ok=True)

    # Define full path where the file will be saved
    file_path = session_dir / file.filename

    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return JSONResponse(content={
        "message": "Upload successful",
        "file_path": str(file_path),
        "uuid": unique_id
    })

@app.post("/process")
async def process_movie(session_id: str, mail:str):
    """
    Process the uploaded video:
    1. Split the video into 30s chunks
    2. Transcribe the video by whisper
    """
    session_path = Path("uploads") / session_id

    if not session_path.exists():
        raise HTTPException(status_code=404, detail="Session ID not found")

    try:
        # Step 1: Split video

        split_video(session_id)

        # # Step 2: Extract and chunk audio
        # audio_chunks = extract_and_chunk_audio(session_id)

        #step 2:
        translate_chunks_to_srt(session_id)

        #step 3:
        file_srt_path = merge_srt_chunks(session_id)

        #step 4:
        send_subtitle_completion_email(mail,file_srt_path)

        return JSONResponse(content={
            "message": "Subtitle is Ready to use",
            "session_id": session_id,
            "Total_video_chunk": len(list((session_path / "chunk").glob("*.mp4"))),
            "Total_subtitle_chunk" : (len(list((session_path / "srt").glob("*.srt"))) -1)

        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

