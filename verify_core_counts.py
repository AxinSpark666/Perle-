import json
import urllib.request
import urllib.error

RPC_URL = "https://mainnet.helius-rpc.com/?api-key=236b88d9-ac4e-4da5-9361-c17b6b9661a4"

BADGES = [
    {"name": "Newcomer", "address": "Cpy7V4GKHVbJaVchR5qKPANtccjVC5bBbtabZJX6E2gT"},
    {"name": "Researcher", "address": "7oXuyGZAUzmij4c76uz9TvM2seDcsRWP1zhfLMJfRdyk"},
    {"name": "Scholar", "address": "7AEpoq5eKoSRUN36CTFFPQESDXepcSby7CfQZs44wgds"}
]

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

def verify_all():
    print("Verifying mpl_core_info for all badges...")
    results = {}
    
    for badge in BADGES:
        print(f"\nQuerying {badge['name']} ({badge['address']})...")
        data = make_das_request("getAsset", {"id": badge['address']})
        
        count = None
        if data and 'result' in data:
            asset = data['result']
            # Check for mpl_core_info
            if 'mpl_core_info' in asset:
                info = asset['mpl_core_info']
                print(f"  -> Found mpl_core_info: {info}")
                count = info.get('num_minted') # or current_size
                print(f"  -> Count (num_minted): {count}")
            else:
                print("  -> No mpl_core_info found")
        else:
            print("  -> Request failed")
            
        results[badge['address']] = count

    print("\n--- Summary ---")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    verify_all()
