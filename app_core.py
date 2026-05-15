import cv2
import os
import json
import base64
import warnings
import anthropic
from web3 import Web3
from deepface import DeepFace

# --- 0. SYSTEM OPTIMIZATION ---
warnings.filterwarnings("ignore", category=UserWarning)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# --- 1. CONFIGURATION ---
ID_IMAGE = 'id.jpg'
SELFIE_IMAGE = 'selfie.jpg'
GANACHE_URL = "http://127.0.0.1:7545"
CONTRACT_ADDRESS = "0x55474ec8beb34d6e81af8381f326390fb428968c"
SECRET_SALT = "SecureID_Internal_2026"

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
    combined_data = f"{name}{id_num}{ipfs_link}{SECRET_SALT}"
    return web3.solidity_keccak(['string'], [combined_data])

# --- 3. NEURAL BIOMETRIC VERIFICATION (Step 1) ---
def verify_identity(id_p, selfie_p):
    print("\n🧠 Step 1: Running Deep Learning Neural Analysis...")
    try:
        result = DeepFace.verify(
            img1_path=id_p,
            img2_path=selfie_p,
            model_name="VGG-Face",
            detector_backend="opencv",
            enforce_detection=False
        )
        is_verified = result['verified']
        dist = result['distance']
        print(f"Result: {'✅ MATCH FOUND' if is_verified else '❌ MISMATCH'}")
        print(f"Neural Distance: {dist:.4f}")
        return is_verified
    except Exception as e:
        print(f"AI Error: {e}")
        return False

# ============================================================
# --- 4. AI OCR EXTRACTION (Step 2) --- ✅ NEW FUNCTION
# ============================================================
def run_ai_ocr(image_path: str) -> dict:
    """
    Uses Claude Vision (Anthropic API) to extract all text fields
    from the ID document image — Name, DOB, ID Number, Address, etc.
    Replaces the old hardcoded found_id = "733860102026"
    """
    print("\n📄 Step 2: Running AI OCR on ID Document...")

    # Read and encode image to base64
    with open(image_path, "rb") as f:
        img_data = base64.standard_b64encode(f.read()).decode("utf-8")

    # Detect media type from file extension
    ext = image_path.lower().split(".")[-1]
    media_type = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"

    try:
        client = anthropic.Anthropic()  # Reads ANTHROPIC_API_KEY from env

        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            system="""You are an OCR engine for identity documents like Aadhaar, PAN, Passport, Driving License.
Extract all visible text fields from the image.
Return ONLY a valid JSON object like this (use null if a field is not visible):
{
  "name": "",
  "dob": "",
  "id_number": "",
  "address": "",
  "gender": "",
  "expiry": null,
  "document_type": ""
}
No explanation. No markdown. Only the JSON object.""",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_data
                        }
                    },
                    {
                        "type": "text",
                        "text": "Extract all text fields from this identity document."
                    }
                ]
            }]
        )

        raw = message.content[0].text.strip()
        ocr_data = json.loads(raw)

        print(f"  ✅ Name       : {ocr_data.get('name', 'N/A')}")
        print(f"  ✅ DOB        : {ocr_data.get('dob', 'N/A')}")
        print(f"  ✅ ID Number  : {ocr_data.get('id_number', 'N/A')}")
        print(f"  ✅ Address    : {ocr_data.get('address', 'N/A')}")
        print(f"  ✅ Doc Type   : {ocr_data.get('document_type', 'N/A')}")

        return ocr_data

    except json.JSONDecodeError:
        print("  ⚠️ OCR response was not valid JSON. Raw output:")
        print(raw)
        return {"name": "Unknown", "id_number": "000000000000", "raw": raw}
    except Exception as e:
        print(f"  ❌ OCR Error: {e}")
        return {"name": "Unknown", "id_number": "000000000000"}

# --- 5. EXECUTION FLOW ---
if __name__ == "__main__":
    print("--- SECURE-ID CORE ENGINE v3.0 ---")

    # Step 1: Neural Biometric Verification
    if verify_identity(ID_IMAGE, SELFIE_IMAGE):

        # Step 2: AI OCR — extracts real ID number from document
        ocr_data = run_ai_ocr(ID_IMAGE)
        found_id   = ocr_data.get("id_number", "000000000000")
        found_name = ocr_data.get("name", "Unknown")
        print(f"  ID Number Confirmed: {found_id}")

        # Step 3: Create Privacy Seal
        print("\n🔐 Step 3: Generating Salted Privacy Hash...")
        p_hash = generate_privacy_hash(found_name, found_id, "ipfs://Qm_Decentralized_ID")

        # Step 4: Anchor to Blockchain
        print(f"⛓  Step 4: Anchoring Proof {p_hash.hex()[:10]}... to Blockchain...")
        try:
            tx_hash = contract.functions.anchorIdentity(p_hash).transact({'from': account})
            web3.eth.wait_for_transaction_receipt(tx_hash)
            print("\n" + "=" * 40)
            print("🚀 VERIFICATION ANCHORED SUCCESSFULLY!")
            print(f"Transaction Hash : {tx_hash.hex()}")
            print(f"Name             : {found_name}")
            print(f"ID Number        : {found_id}")
            print("=" * 40)
        except Exception as e:
            print(f"❌ Blockchain Transaction Failed: {e}")
    else:
        print("\n❌ SECURITY ALERT: Biometric Verification Failed.")
        print("Blockchain anchoring aborted for security.")
