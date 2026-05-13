FROM serengil/deepface:latest

WORKDIR /app
COPY . .

RUN pip install web3==5.31.3

ENTRYPOINT []
CMD ["python", "app.py"]
