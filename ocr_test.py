import easyocr
import cv2
import os

# 1. Load the image
image_path = 'id.jpg'

# Check if file exists before trying to read it
if not os.path.exists(image_path):
    print(f"ERROR: The file '{image_path}' was not found in: {os.getcwd()}")
    print("Please make sure your image is named 'id.jpg' and is in this folder.")
else:
    image = cv2.imread(image_path)
    
    # 2. Pre-processing (From the Base Paper Methodology)
    # Convert to Grayscale [cite: 95]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) 

    # 3. Initialize OCR [cite: 53]
    print("Initializing OCR (this might take a minute the first time)...")
    reader = easyocr.Reader(['en']) 

    # 4. Extract Text [cite: 102, 112]
    print("Scanning document...")
    results = reader.readtext(gray)

    # 5. Show results
    if not results:
        print("No text detected. Try a clearer image.")
    for (bbox, text, prob) in results:
        print(f"Detected Text: {text} (Confidence: {prob:.2f})")