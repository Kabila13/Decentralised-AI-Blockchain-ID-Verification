FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN apt-get update -y && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean

RUN pip install --upgrade pip && \
    pip install streamlit && \
    pip install opencv-python-headless==4.8.1.78 && \
    pip install deepface==0.0.79 && \
    pip install easyocr && \
    pip install web3==5.31.3 && \
    pip install mediapipe && \
    pip install requests pandas && \
    pip install protobuf==3.20.3

CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.address=0.0.0.0"]
