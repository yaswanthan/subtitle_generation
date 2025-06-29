from pathlib import Path
import whisper

def format_timestamp(seconds):
    """Converts seconds (float) to SRT timestamp format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def translate_chunks_to_srt(session_id: str, model_size: str = "large"):
    """
    Translates all video chunks in uploads/<session_id>/chunks/
    and generates English .srt subtitle files for each chunk.

    Args:
        session_id (str): UUID of the session
        model_size (str): Whisper model size ("tiny", "base", "small", "medium", "large")
    """
    base_dir = Path("uploads") / session_id
    chunk_dir = base_dir / "chunk"
    srt_dir = base_dir / "srt"
    srt_dir.mkdir(parents=True, exist_ok=True)

    model = whisper.load_model(model_size)

    video_chunks = sorted(chunk_dir.glob("*.mp4"))
    if not video_chunks:
        raise FileNotFoundError(f"No video chunks found in {chunk_dir}")

    for chunk_file in video_chunks:
        print(f"Translating: {chunk_file.name}")
        result = model.transcribe(
            str(chunk_file),
            task="translate",  # Translate to English
            language=None,     # Auto-detect
            fp16=False         # Set True if using GPU
        )

        # Write to SRT
        srt_path = srt_dir / f"{chunk_file.stem}.srt"
        with open(srt_path, "w", encoding="utf-8") as srt_file:
            for i, segment in enumerate(result["segments"], start=1):
                srt_file.write(f"{i}\n")
                srt_file.write(f"{format_timestamp(segment['start'])} --> {format_timestamp(segment['end'])}\n")
                srt_file.write(segment['text'].strip() + "\n\n")

    print(f"Subtitles saved in: {srt_dir}")
    return srt_dir


def merge_srt_chunks(session_id: str, chunk_duration_sec: int = 30, output_filename: str = "full.srt"):
    """
    Merges all SRT files in uploads/<session_id>/srt into one, adjusting the timestamps.

    Args:
        session_id (str): UUID of the session
        chunk_duration_sec (int): Length of each chunk in seconds
        output_filename (str): Output merged SRT filename (default: full.srt)
    """
    srt_dir = Path("uploads") / session_id / "srt"
    output_path = srt_dir / output_filename
    srt_files = sorted(srt_dir.glob("*.srt"), key=lambda p: int(p.stem))

    if not srt_files:
        raise FileNotFoundError(f"No SRT files found in {srt_dir}")

    merged_lines = []
    global_index = 1

    for idx, srt_file in enumerate(srt_files):
        offset_sec = idx * chunk_duration_sec

        with open(srt_file, "r", encoding="utf-8") as f:
            block = []
            for line in f:
                if line.strip().isdigit():
                    block = [str(global_index)]  # reset block ID
                elif "-->" in line:
                    start, end = [l.strip() for l in line.strip().split("-->")]
                    start_shifted = shift_timestamp(start, offset_sec)
                    end_shifted = shift_timestamp(end, offset_sec)
                    block.append(f"{start_shifted} --> {end_shifted}")
                elif line.strip() == "":
                    block.append("")
                    merged_lines.extend(block)
                    global_index += 1
                else:
                    block.append(line.strip())

    with open(output_path, "w", encoding="utf-8") as out:
        out.write("\n".join(merged_lines))

    print(f" Merged SRT saved to: {output_path}")
    return output_path


def shift_timestamp(timestamp: str, offset_sec: int) -> str:
    """Shift a timestamp (e.g. 00:00:28,000) by offset seconds."""
    hours, minutes, rest = timestamp.split(":")
    seconds, millis = rest.split(",")

    total_ms = (
        int(hours) * 3600000 +
        int(minutes) * 60000 +
        int(seconds) * 1000 +
        int(millis)
    ) + (offset_sec * 1000)

    new_hours = total_ms // 3600000
    total_ms %= 3600000
    new_minutes = total_ms // 60000
    total_ms %= 60000
    new_seconds = total_ms // 1000
    new_millis = total_ms % 1000

    return f"{new_hours:02}:{new_minutes:02}:{new_seconds:02},{new_millis:03}"


