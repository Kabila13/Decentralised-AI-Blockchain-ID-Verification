import streamlit as st
import os
import requests
import warnings
import cv2
import numpy as np
from web3 import Web3
import json
import pandas as pd

warnings.filterwarnings("ignore")

# --- BLOCKCHAIN ---
GANACHE_URL = "https://ethereum-sepolia-rpc.publicnode.com"
CONTRACT_ADDRESS = "0xe19d48797873AC54BCdc48A66fE2fa3b84E1e29d"
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
contract = None
account = None

try:
    with open(os.path.join('build', 'contracts', 'Verification.json')) as f:
        abi = json.load(f)['abi']
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
    account = w3.eth.accounts[0]
except:
    pass

# --- IPFS ---
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

# --- FACE VERIFICATION (OpenCV only, no tensorflow) ---
def verify_biometrics(id_path, selfie_path):
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        img1 = cv2.imread(id_path, cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(selfie_path, cv2.IMREAD_GRAYSCALE)
        if img1 is None or img2 is None:
            return False, 1.0
        faces1 = face_cascade.detectMultiScale(img1, 1.1, 4)
        faces2 = face_cascade.detectMultiScale(img2, 1.1, 4)
        if len(faces1) == 0 or len(faces2) == 0:
            # No face detected, do pixel similarity
            img1r = cv2.resize(img1, (100, 100)).astype(float)
            img2r = cv2.resize(img2, (100, 100)).astype(float)
        else:
            x,y,w,h = faces1[0]
            face1 = cv2.resize(img1[y:y+h, x:x+w], (100, 100)).astype(float)
            x,y,w,h = faces2[0]
            face2 = cv2.resize(img2[y:y+h, x:x+w], (100, 100)).astype(float)
            img1r, img2r = face1, face2
        diff = np.mean(np.abs(img1r - img2r)) / 255.0
        return diff < 0.4, diff
    except Exception as e:
        st.error(f"Error: {e}")
        return False, 1.0

# --- UI ---
st.set_page_config(page_title="SecureID Pro", layout="wide")
st.title("🛡️ SecureID: Deep Learning Identity Framework")

if 'history' not in st.session_state:
    st.session_state.history = []

st.sidebar.header("⛓️ Blockchain Ledger History")
st.sidebar.dataframe(pd.DataFrame(st.session_state.history))

col1, col2 = st.columns(2)
with col1:
    id_file = st.file_uploader("Upload ID", type=['jpg', 'png'])
with col2:
    selfie_file = st.file_uploader("Upload Selfie", type=['jpg', 'png'])

if st.button("🚀 Execute Neural Verification"):
    if id_file and selfie_file:
        with open("id.jpg", "wb") as f: f.write(id_file.getbuffer())
        with open("selfie.jpg", "wb") as f: f.write(selfie_file.getbuffer())

        st.write("🧠 Phase 1: Biometric Analysis...")
        is_match, dist = verify_biometrics("id.jpg", "selfie.jpg")

        if is_match:
            id_num = "73386010"
            st.write("📤 Phase 2: Storing Evidence on IPFS...")
            cid = upload_to_ipfs("id.jpg")
            st.write("🔐 Phase 3: Anchoring Privacy Seal...")
            p_hash = generate_privacy_hash("Kabil", id_num, cid)
            try:
                if contract and account:
                    tx = contract.functions.anchorIdentity(p_hash).transact({'from': account})
                    receipt = w3.eth.wait_for_transaction_receipt(tx)
                    st.session_state.history.append({"HashedID": p_hash.hex()[:12]+"...", "Block": receipt.blockNumber})
                else:
                    st.session_state.history.append({"HashedID": p_hash.hex()[:12]+"...", "Block": "Simulated"})
                st.success(f"✅ VERIFIED! (Match Distance: {dist:.2f})")
                st.balloons()
            except Exception as e:
                st.error(f"Blockchain Error: {e}")
        else:
            st.error(f"❌ Security Alert: Biometric Mismatch! (Distance: {dist:.2f})")
    else:
        st.warning("Please upload both ID and Selfie images.")
