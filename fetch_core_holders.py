import json
import urllib.request
import urllib.error
import time

# 尝试扫描 Metaplex Core Program，过滤 Update Authority 为 Collection Address
RPC_URL = "https://api.mainnet-beta.solana.com"
CORE_PROGRAM_ID = "CoREENxT6tW1HoK8ypY1SxRMZTcVPm7R94rH4PZNhX7d"

BADGES = [
    {"name": "Newcomer", "address": "Cpy7V4GKHVbJaVchR5qKPANtccjVC5bBbtabZJX6E2gT"},
    {"name": "Researcher", "address": "7oXuyGZAUzmij4c76uz9TvM2seDcsRWP1zhfLMJfRdyk"},
    {"name": "Scholar", "address": "7AEpoq5eKoSRUN36CTFFPQESDXepcSby7CfQZs44wgds"}
]

def make_request(method, params):
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
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"  [Error] {e}")
        return None

def get_core_assets(collection_address):
    print(f"Scanning Core Program for assets with update authority {collection_address}...")
    # Metaplex Core Asset V1:
    # Key (1 byte) + Owner (32 bytes) + UpdateAuthority (32 bytes)
    # Offset of Update Authority = 1 + 32 = 33
    params = [
        CORE_PROGRAM_ID,
        {
            "encoding": "base64",
            "filters": [
                {
                    "memcmp": {
                        "offset": 33, # 假设 Update Authority 在 Offset 33
                        "bytes": collection_address
                    }
                }
            ],
            "dataSlice": {"offset": 0, "length": 0} # 只计数
        }
    ]
    
    data = make_request("getProgramAccounts", params)
    if data and 'result' in data:
        count = len(data['result'])
        print(f"  -> Count: {count}")
        return count
    elif data and 'error' in data:
        print(f"  -> Error: {data['error']['message']}")
    else:
        print("  -> Failed or empty result")
    return None

def main():
    results = {}
    for badge in BADGES:
        print(f"\n--- Analyzing {badge['name']} ---")
        count = get_core_assets(badge['address'])
        if count is not None:
            results[badge['address']] = count
        else:
            results[badge['address']] = 0
            
        time.sleep(2)

    print("\n---JSON_START---")
    print(json.dumps(results))
    print("---JSON_END---")

if __name__ == "__main__":
    main()
