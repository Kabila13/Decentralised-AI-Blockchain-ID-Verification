import cv2
import os
import json
import warnings
from web3 import Web3
from deepface import DeepFace  # Our new Deep Learning Engine

# --- 0. SYSTEM OPTIMIZATION ---
# This hides heavy background logs from the AI libraries
warnings.filterwarnings("ignore", category=UserWarning)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3" 
os.environ["CUDA_VISIBLE_DEVICES"] = "-1" # Forces CPU mode for stability

# --- 1. CONFIGURATION ---
ID_IMAGE = 'id.jpg'
SELFIE_IMAGE = 'selfie.jpg'
GANACHE_URL = "http://127.0.0.1:7545"
CONTRACT_ADDRESS = "0xe66B8438dF44b071217572a0aA54C6AcdA963701"

# Connect to the Blockchain Ledger
try:
    web3 = Web3(Web3.HTTPProvider(GANACHE_URL))
    truffle_file = os.path.join('build', 'contracts', 'Verification.json')
    with open(truffle_file) as f:
        abi = json.load(f)['abi']
    contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
    account = web3.eth.accounts[0]
except Exception as e:
    print(f"❌ Ledger Connection Error: {e}")

# --- 2. PRIVACY LOGIC (GDPR Compliance) ---
def generate_privacy_hash(name, id_num, ipfs_link):
    """
    Creates a 'Security Seal'. The actual ID number is never 
    visible on the public blockchain.
    """
    SECRET_SALT = "SecureID_Internal_2026" 
    combined_data = f"{name}{id_num}{ipfs_link}{SECRET_SALT}"
    # Returns the Keccak256 hash
    return web3.solidity_keccak(['string'], [combined_data])

# --- 3. NEURAL BIOMETRIC VERIFICATION ---
def verify_identity(id_p, selfie_p):
    """
    DeepFace automatically handles detection, alignment, and 
    mathematical identity verification.
    """
    print("\n🧠 Step 1: Running Deep Learning Neural Analysis...")
    try:
        # DeepFace.verify compares the 'identity' not just pixels
        result = DeepFace.verify(
            img1_path = id_p, 
            img2_path = selfie_p,
            model_name = "VGG-Face", 
            detector_backend = "opencv", 
            enforce_detection = False
        )
        
        is_verified = result['verified']
        dist = result['distance'] # Mathematical 'gap' between faces
        
        print(f"Result: {'✅ MATCH FOUND' if is_verified else '❌ MISMATCH'}")
        print(f"Neural Distance: {dist:.4f}")
        return is_verified
    except Exception as e:
        print(f"AI Error: {e}")
        return False

# --- 4. EXECUTION FLOW ---
if __name__ == "__main__":
    print("--- SECURE-ID CORE ENGINE v3.0 ---")
    
    # 1. Start Neural Verification
    if verify_identity(ID_IMAGE, SELFIE_IMAGE):
        
        # 2. Simulate ID Number (In the full app, OCR would do this)
        found_id = "733860102026" 
        print(f"Step 2: ID Number Identified: {found_id}")
        
        # 3. Create Privacy Seal
        print("Step 3: Generating Salted Privacy Hash...")
        p_hash = generate_privacy_hash("Kabil", found_id, "ipfs://Qm_Decentralized_ID")
        
        # 4. Anchor to Blockchain
        print(f"Step 4: Anchoring Proof {p_hash.hex()[:10]}... to Blockchain...")
        try:
            tx_hash = contract.functions.anchorIdentity(p_hash).transact({'from': account})
            web3.eth.wait_for_transaction_receipt(tx_hash)
            
            print("\n" + "="*40)
            print("🚀 VERIFICATION ANCHORED SUCCESSFULLY!")
            print(f"Transaction Hash: {tx_hash.hex()}")
            print("="*40)
        except Exception as e:
            print(f"❌ Blockchain Transaction Failed: {e}")
    else:
        print("\n❌ SECURITY ALERT: Biometric Verification Failed.")
        print("Blockchain anchoring aborted for security.")

SECRET_SALT = "SecureID_Internal_2026"
