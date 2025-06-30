import whisper
from pathlib import Path

def format_timestamp(seconds):
    """
    Convert seconds to SRT timestamp format: HH:MM:SS,mmm

    Args:
        seconds (float): The time in seconds.

    Returns:
        str: The formatted timestamp as a string in SRT format.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def transcribe_and_save_srt(video_path: str, model_size: str = "small"):
    """
    Transcribes the audio from a video file, translates it to English, and saves the result as an SRT subtitle file.
    Args:
        video_path (str): The path to the video file to be transcribed.
        model_size (str, optional): The size of the Whisper model to use for transcription (e.g., "small", "medium", "large"). Defaults to "small".
    Returns:
        Path: The path to the generated SRT subtitle file.
    Raises:
        FileNotFoundError: If the specified video file does not exist.
        Exception: If transcription or file writing fails.
    Note:
        This function uses the OpenAI Whisper model for transcription and translation. The output SRT file will be saved in the same directory as the input video, with the same base name.
    """


    model = whisper.load_model(model_size)
    result = model.transcribe(video_path, task="translate",)

    # Prepare output path
    video_file = Path(video_path)
    srt_path = video_file.with_suffix(".srt")

    # Write SRT file
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result["segments"], start=1):
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            text = segment["text"].strip()

            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")

    print(f"✅ Subtitle saved to: {srt_path}")
    return srt_path

# Example usage
# transcribe_and_save_srt("uploads/7f11a2b6-e7cb-46fa-8729-9d0b67e18d9d/original_file/SSYouTube.online_F1 _ Official Trailer_720p.mp4")
