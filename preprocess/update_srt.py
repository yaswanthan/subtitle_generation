from datetime import datetime, timedelta
import re

def parse_srt_timestamp(ts: str) -> datetime:
    return datetime.strptime(ts, "%H:%M:%S,%f")

def format_srt_timestamp(dt: datetime) -> str:
    return dt.strftime("%H:%M:%S,%f")[:-3]

def shift_srt_timestamps(content: str, offset_seconds: float) -> str:
    """Shift all timestamps in an SRT block by offset_seconds."""
    def shift_line(line):
        if " --> " in line:
            start, end = line.split(" --> ")
            new_start = format_srt_timestamp(parse_srt_timestamp(start) + timedelta(seconds=offset_seconds))
            new_end = format_srt_timestamp(parse_srt_timestamp(end) + timedelta(seconds=offset_seconds))
            return f"{new_start} --> {new_end}"
        return line

    lines = content.strip().splitlines()
    return "\n".join([shift_line(line) for line in lines])
