#!/bin/bash

# Start FastAPI on 0.0.0.0 so it's accessible outside the container
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &

# Start Streamlit on 0.0.0.0 so it's accessible outside the container
streamlit run front_end.py --server.port=8501 --server.address=0.0.0.0
