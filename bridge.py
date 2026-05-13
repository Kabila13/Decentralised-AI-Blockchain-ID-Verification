from web3 import Web3
import json
import os

# 1. Connect to Ganache
ganache_url = "http://127.0.0.1:7545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

# 2. Automatically load the ABI from the Truffle build folder
# This avoids the JSONDecodeError entirely!
truffle_file = os.path.join('build', 'contracts', 'Verification.json')

with open(truffle_file) as f:
    info_json = json.load(f)
    abi = info_json['abi']

# 3. SET YOUR CONTRACT ADDRESS HERE (Copy from your terminal or Ganache)
contract_address = "0xe66B8438dF44b071217572a0aA54C6AcdA963701"

contract = web3.eth.contract(address=contract_address, abi=abi)

# 4. Choose an account from Ganache
account = web3.eth.accounts[0]

def save_to_blockchain(name, id_num, ipfs_hash):
    print(f"Sending data to Blockchain for {name}...")
    # Use the account to sign the transaction
    tx_hash = contract.functions.saveVerification(
        account, name, id_num, ipfs_hash
    ).transact({'from': account})
    
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Success! Transaction Hash: {tx_hash.hex()}")

# Run a test
if __name__ == "__main__":
    # We use the ID number your OCR found earlier!
    save_to_blockchain("Kabil", "7338 6010", "Qm_Decentralized_ID")     