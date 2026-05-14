FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && \
    pip install streamlit \
    opencv-python-headless==4.8.1.78 \
    deepface==0.0.79 \
    easyocr \
    web3==5.31.3 \
    mediapipe \
    requests \
    pandas \
    protobuf==3.20.3

CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.address=0.0.0.0"]
