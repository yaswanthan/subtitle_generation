import os
import subprocess
from pathlib import Path
from pydub import AudioSegment
from moviepy import VideoFileClip

def split_video(session_id: str, chunk_duration: int = 30):

    """
    Splits the video associated with a session_id into 30-second chunks.

    Args:
        session_id (str): Session identifier to locate the video file.
        chunk_duration (int): Duration of each chunk in seconds.
    """


    input_dir = os.path.join("uploads", session_id, "original_file")
    output_dir = os.path.join("uploads", session_id, "chunk")
    os.makedirs(output_dir, exist_ok=True)

    # Find video file
    video_files = [f for f in os.listdir(input_dir) if f.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))]
    if not video_files:
        raise FileNotFoundError(f"Please enter a valid Session ID {session_id}")

    input_video_path = os.path.join(input_dir, video_files[0])
    video = VideoFileClip(input_video_path)
    total_duration = int(video.duration)

    # Split into chunks
    for i, start_time in enumerate(range(0, total_duration, chunk_duration)):
        end_time = min(start_time + chunk_duration, total_duration)
        clip = video.subclipped(start_time, end_time)
        clip.write_videofile(os.path.join(output_dir, f"{i+1}.mp4"), codec="libx264", audio_codec="aac", logger=None)

    video.close()
    print(f" Split complete for session: {session_id}")


def extract_and_chunk_audio(session_id: str, chunk_length_sec: int = 30):

    """
    Extracts audio from the uploaded video in:
        uploads/<session_id>/original_file/
    and splits it into fixed-size WAV chunks stored in:
        uploads/<session_id>/audio_chunks/

    Args:
        session_id (str): UUID of the session
        chunk_length_sec (int): Duration of each audio chunk in seconds

    Returns:
        List of audio chunk file paths (as strings)
    """
    
    base_dir = Path("uploads") / session_id
    original_dir = base_dir / "original_file"
    output_dir = base_dir / "audio_chunks"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find video file in original_file/
    video_files = list(original_dir.glob("*"))
    if not video_files:
        raise FileNotFoundError(f"No video file found in {original_dir}")

    input_video = video_files[0]
    audio_path = output_dir / "full_audio.wav"

    # Step 1: Extract audio from video
    print(f" Extracting audio from {input_video}")
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_video),
        "-ac", "1",        # mono
        "-ar", "16000",    # 16kHz
        str(audio_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Step 2: Split audio into chunks
    audio = AudioSegment.from_wav(audio_path)
    chunk_length_ms = chunk_length_sec * 1000
    total_length = len(audio)

    chunk_paths = []
    print(f" Splitting audio into {chunk_length_sec}s chunks...")

    for i in range(0, total_length, chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        chunk_filename = output_dir / f"{(i // chunk_length_ms) + 1}.wav"
        chunk.export(chunk_filename, format="wav")
        chunk_paths.append(str(chunk_filename))

    print(f" Done! Extracted {len(chunk_paths)} audio chunks to {output_dir}")
    return chunk_paths

