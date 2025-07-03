# Use an official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR ./

# Install dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean


# Copy requirement and install
COPY requirement.txt .
RUN pip install torch torchvision torchaudio
RUN pip install --no-cache-dir -r requirement.txt


# Copy the rest of the code
COPY . .

RUN chmod +x start.sh


# Expose both FastAPI and Streamlit ports
EXPOSE 8000
EXPOSE 8501


# Start both apps
CMD ["./start.sh"]
