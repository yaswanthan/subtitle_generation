# Subtitle Generation Project

This project provides an end-to-end pipeline for generating subtitles from video files. It includes preprocessing, subtitle extraction, and a web interface for user interaction.

## How to Run

### 1. Using Docker (Recommended)

1. **Build the Docker image:**
   ```bash
   docker build -t subtitle_generation .
   ```
2. **Run the container:**
   ```bash
   docker run -p 8000:8000 -p 8501:8501 subtitle_generation
   ```
   - Port 8000: FastAPI backend
   - Port 8501: Streamlit frontend

### 2. Running Locally (Without Docker)

1. **Install Python 3.10+ and pip**
2. **Install dependencies:**
   ```bash
   pip install torch torchvision torchaudio
   pip install -r requirement.txt
   ```
3. **Start the application:**
   ```bash
   bash start.sh
   ```

---

## File and Folder Structure

### Top-Level Files

- **dockerfile**: Docker configuration to build and run the project in a containerized environment.
- **front_end.py**: Likely contains the Streamlit web interface for user interaction.
- **main.py**: Main entry point for the FastAPI backend server.
- **requirement.txt**: Lists all Python dependencies required for the project.
- **start.sh**: Shell script to start both backend and frontend services.
- **readme.md**: This documentation file.

### Folders

#### preprocess/
Contains core Python scripts for processing videos and generating subtitles:
- **full_movie_sub.py**: Handles subtitle generation for full-length movies.
- **functions.py**: Utility functions used across the project.
- **mail.py**: Handles email notifications or sending results.
- **subtitle.py**: Main logic for subtitle extraction from video/audio.
- **update_srt.py**: Updates or merges SRT subtitle files.

#### uploads/
Stores uploaded video files and generated subtitles, organized by unique session IDs:
- **<session_id>/**: Each session has its own folder.
  - **chunk/**: Contains video chunks (e.g., 1.mp4, 2.mp4, ...).
  - **original_file/**: Stores the original uploaded video file.
  - **srt/**: Contains generated subtitle files (e.g., 1.srt, 2.srt, full.srt).

---

## Notes
- The project exposes two ports: 8000 (FastAPI backend) and 8501 (Streamlit frontend).
- Make sure to have all dependencies installed as specified in `requirement.txt`.
- For any issues, check the logs
