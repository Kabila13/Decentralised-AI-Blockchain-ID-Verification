import streamlit as st
import os
import requests
import warnings
from deepface import DeepFace
from web3 import Web3
import json
import pandas as pd

# --- 0. SYSTEM SETUP ---
warnings.filterwarnings("ignore", category=UserWarning)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# --- 1. BLOCKCHAIN CONNECTION ---
GANACHE_URL = "https://ethereum-sepolia-rpc.publicnode.com"
CONTRACT_ADDRESS = "0xe19d48797873AC54BCdc48A66fE2fa3b84E1e29d"

w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
contract = None
account = None

try:
    truffle_file = os.path.join('build', 'contracts', 'Verification.json')
    with open(truffle_file) as f:
        abi = json.load(f)['abi']
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
    account = w3.eth.accounts[0]
except Exception as e:
    pass

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

# --- 3. BIOMETRIC VERIFICATION ---
def verify_biometrics(id_path, selfie_path):
    try:
        result = DeepFace.verify(
            img1_path=id_path,
            img2_path=selfie_path,
            model_name="VGG-Face",
            detector_backend="opencv",
            enforce_detection=False
        )
        return result['verified'], result['distance']
    except Exception as e:
        st.error(f"DeepFace Error: {e}")
        return False, 1.0

# --- 4. USER INTERFACE ---
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

        st.write("🧠 Phase 1: DeepFace Neural Analysis...")
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
