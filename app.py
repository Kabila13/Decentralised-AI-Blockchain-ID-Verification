import streamlit as st
import cv2
import numpy as np
import easyocr
import os
import requests
import warnings
from deepface import DeepFace # New Deep Learning Engine
from web3 import Web3
import mediapipe as mp
import json
import pandas as pd

if 'history' not in st.session_state:
    st.session_state.history = []

# --- 0. SYSTEM SETUP ---
warnings.filterwarnings("ignore", category=UserWarning)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3" # Hides heavy TensorFlow logs

# --- 1. BLOCKCHAIN (GANACHE) CONNECTION ---
GANACHE_URL = "https://ethereum-sepolia-rpc.publicnode.com"
CONTRACT_ADDRESS = "0xe19d48797873AC54BCdc48A66fE2fa3b84E1e29d"

w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
truffle_file = os.path.join('build', 'contracts', 'Verification.json')

try:
    with open(truffle_file) as f:
        abi = json.load(f)['abi']
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
    account = w3.eth.accounts[0]
except Exception as e:
    st.error(f"Blockchain Connection Error: {e}")

# --- 2. STORAGE & PRIVACY ---
def upload_to_ipfs(file_path):
    API_KEY = "230e03bc79053cc254c93"
    SECRET_KEY = "01dde9bc3eaa3e14f5006be90f91957a25ad047bbf908196bad0eba1d978d113"
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {'pinata_api_key': API_KEY, 'pinata_secret_api_key': SECRET_KEY}
    try:
        with open(file_path, 'rb') as f:
            response = requests.post(url, files={'file': f}, headers=headers)
            return response.json().get('IpfsHash', "Qm_Default_CID")
    except:
        return "Offline"

def generate_privacy_hash(name, id_num, ipfs_link):
    SECRET_SALT = "SecureID_Internal_2026"
    combined_data = f"{name}{id_num}{ipfs_link}{SECRET_SALT}"
    return w3.solidity_keccak(['string'], [combined_data])

# --- 3. THE AI ENGINES ---
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

def verify_biometrics(id_path, selfie_path):
    """
    Uses DeepFace to compare identity.
    It handles face detection and verification in one go.
    """
    try:
        # result contains 'verified' (True/False) and 'distance'
        result = DeepFace.verify(
            img1_path = id_path, 
            img2_path = selfie_path,
            model_name = "VGG-Face", # Fast and reliable
            detector_backend = "opencv", # Best for standard photos
            enforce_detection = False # Prevents crashing if face is blurry
        )
        return result['verified'], result['distance']
    except Exception as e:
        st.error(f"DeepFace Error: {e}")
        return False, 1.0

# --- 4. USER INTERFACE ---
st.set_page_config(page_title="SecureID Pro (DeepFace)", layout="wide")
st.title("🛡️ SecureID: Deep Learning Identity Framework")

st.sidebar.header("⛓️ Blockchain Ledger History")
if 'history' not in st.session_state: st.session_state.history = []
st.sidebar.dataframe(pd.DataFrame(st.session_state.history))

col1, col2 = st.columns(2)
with col1: id_file = st.file_uploader("Upload ID", type=['jpg', 'png'])
with col2: selfie_file = st.file_uploader("Upload Selfie", type=['jpg', 'png'])

if st.button("🚀 Execute Neural Verification"):
    if id_file and selfie_file:
        # Save temp files
        with open("id.jpg", "wb") as f: f.write(id_file.getbuffer())
        with open("selfie.jpg", "wb") as f: f.write(selfie_file.getbuffer())

        # Phase 1: Deep Learning Biometrics
        st.write("🧠 Phase 1: DeepFace Neural Analysis...")
        is_match, dist = verify_biometrics("id.jpg", "selfie.jpg")
        if is_match == "NO_FACE":
            st.error("❌ ERROR: No human face detected in one or both images. Please upload a clear photo.")
        if is_match:
            # Phase 2: OCR Extraction
            st.write("📄 Phase 2: AI OCR Reading...")
            reader = load_ocr()
            res = reader.readtext("id.jpg")
            id_num = "".join(filter(str.isdigit, res[0][1])) if res else "73386010"

            # Phase 3: IPFS Storage
            st.write("📤 Phase 3: Storing Evidence on IPFS...")
            cid = upload_to_ipfs("id.jpg")
            
            # Phase 4: Privacy Hashing & Blockchain
            st.write("🔐 Phase 4: Anchoring Privacy Seal...")
            p_hash = generate_privacy_hash("Kabil", id_num, cid)
            
            try:
                tx = contract.functions.anchorIdentity(p_hash).transact({'from': account})
                receipt = w3.eth.wait_for_transaction_receipt(tx)
                
                st.session_state.history.append({"HashedID": p_hash.hex()[:12]+"...", "Block": receipt.blockNumber})
                st.success(f"✅ VERIFIED! (Match: {dist:.2f})")
                st.balloons()
            except Exception as e:
                st.error(f"Blockchain Error: {e}")
        else:
            st.error(f"❌ Security Alert: Biometric Mismatch! (Distance: {dist:.2f})")
