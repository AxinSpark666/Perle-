import json
import urllib.request
import urllib.error

RPC_URL = "https://mainnet.helius-rpc.com/?api-key=236b88d9-ac4e-4da5-9361-c17b6b9661a4"
TARGET_ADDRESS = "7oXuyGZAUzmij4c76uz9TvM2seDcsRWP1zhfLMJfRdyk"

def make_das_request(method, params):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    try:
        req = urllib.request.Request(
            RPC_URL, 
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"[Error] {e}")
        return None

def diagnose():
    print(f"Diagnosing address: {TARGET_ADDRESS}")

    # 1. Check getAsset to see what this address represents
    print("\n--- 1. getAsset Info ---")
    data = make_das_request("getAsset", {"id": TARGET_ADDRESS})
    if data and 'result' in data:
        asset = data['result']
        print(json.dumps(asset, indent=2))
        
        # Check if it has creators
        creators = asset.get('creators', [])
        if creators:
            print("\nCreators found:")
            for c in creators:
                print(f"  - {c.get('address')} (share: {c.get('share')}%, verified: {c.get('verified')})")
        
        # Check grouping
        grouping = asset.get('grouping', [])
        if grouping:
             print("\nGrouping found:")
             print(json.dumps(grouping, indent=2))
             
    else:
        print("Failed to get asset info.")

    # 2. Try getAssetsByGroup (Collection) again
    print("\n--- 2. getAssetsByGroup (Collection) ---")
    params = {
        "groupKey": "collection",
        "groupValue": TARGET_ADDRESS,
        "page": 1,
        "limit": 1
    }
    data = make_das_request("getAssetsByGroup", params)
    if data and 'result' in data:
        print(f"Total Assets: {data['result'].get('total')}")
        if data['result'].get('items'):
            print(f"First Item: {data['result']['items'][0].get('id')}")
    else:
        print("Failed.")

    # 3. Try getAssetsByCreator (using the target address as creator)
    print("\n--- 3. getAssetsByCreator ---")
    params = {
        "creatorAddress": TARGET_ADDRESS,
        "onlyVerified": True,
        "page": 1,
        "limit": 1
    }
    data = make_das_request("getAssetsByCreator", params)
    if data and 'result' in data:
        print(f"Total Assets (Verified Creator): {data['result'].get('total')}")
    else:
        print("Failed.")

    # 4. Try getAssetsByOwner (if this address holds the assets itself? unlikely for 30k holders)
    # Skip

if __name__ == "__main__":
    diagnose()
