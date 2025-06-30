import uuid
import shutil
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException,Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from preprocess.functions import split_video
from preprocess.subtitle import translate_chunks_to_srt,merge_srt_chunks
from preprocess.mail import send_subtitle_completion_email
from preprocess.update_srt import format_srt_timestamp,shift_srt_timestamps,parse_srt_timestamp
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="uploads"), name="static")

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


@app.post("/save-subtitle/")
def save_subtitle(
    session_id: str = Form(...),
    file_name: str = Form(...),
    content: str = Form(...)
):
    try:
        srt_path = UPLOAD_DIR / session_id / "srt" / file_name
        srt_path.parent.mkdir(parents=True, exist_ok=True)
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"message": "Subtitle saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/finalize-subtitles/")
def finalize_subtitles(session_id: str = Form(...)):
    try:
        srt_dir = UPLOAD_DIR / session_id / "srt"
        output_srt = srt_dir / "full.srt"

        if not srt_dir.exists():
            raise HTTPException(status_code=404, detail="SRT directory not found")

        chunk_srts = sorted([s for s in srt_dir.glob("*.srt") if s.name != "full.srt"])

        index = 1
        with open(output_srt, "w", encoding="utf-8") as outfile:
            for chunk_index, srt_file in enumerate(chunk_srts):
                with open(srt_file, "r", encoding="utf-8") as infile:
                    blocks = infile.read().strip().split("\n\n")

                offset_seconds = chunk_index * 30

                for block in blocks:
                    if not block.strip():
                        continue

                    lines = block.strip().splitlines()
                    if len(lines) < 2:
                        continue

                    # Replace index with global index, shift timestamps
                    shifted_block = [str(index)] + shift_srt_timestamps("\n".join(lines[1:]), offset_seconds).splitlines()
                    outfile.write("\n".join(shifted_block) + "\n\n")
                    index += 1

        return {"message": "Final full.srt generated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))