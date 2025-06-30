from datetime import datetime, timedelta
import re

def parse_srt_timestamp(ts: str) -> datetime:

    """
    Parses an SRT (SubRip Subtitle) timestamp string into a datetime object.
    Args:
        ts (str): The timestamp string in the format "HH:MM:SS,fff".
    Returns:
        datetime: A datetime object representing the parsed timestamp.
    Raises:
        ValueError: If the input string does not match the expected SRT timestamp format.
    """

    return datetime.strptime(ts, "%H:%M:%S,%f")

def format_srt_timestamp(dt: datetime) -> str:
    return dt.strftime("%H:%M:%S,%f")[:-3]

def shift_srt_timestamps(content: str, offset_seconds: float) -> str:

    """
    Shift all timestamps in an SRT (SubRip Subtitle) content block by a specified number of seconds.

    Args:
        content (str): The full SRT file content as a string.
        offset_seconds (float): The number of seconds to shift each timestamp. Can be positive or negative.

    Returns:
        str: The SRT content with all timestamps shifted by the given offset.
    """
    
    def shift_line(line):
        if " --> " in line:
            start, end = line.split(" --> ")
            new_start = format_srt_timestamp(parse_srt_timestamp(start) + timedelta(seconds=offset_seconds))
            new_end = format_srt_timestamp(parse_srt_timestamp(end) + timedelta(seconds=offset_seconds))
            return f"{new_start} --> {new_end}"
        return line

    lines = content.strip().splitlines()
    return "\n".join([shift_line(line) for line in lines])
