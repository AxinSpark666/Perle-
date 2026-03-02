import json
import urllib.request
import urllib.error
import time

# RPC 节点列表（轮询尝试）
RPC_ENDPOINTS = [
    "https://rpc.ankr.com/solana",
    "https://solana-mainnet.rpc.extrnode.com",
    "https://api.mainnet-beta.solana.com",
    "https://solana-api.projectserum.com"
]

BADGES = [
    {"name": "Newcomer", "address": "Cpy7V4GKHVbJaVchR5qKPANtccjVC5bBbtabZJX6E2gT"},
    {"name": "Researcher", "address": "7oXuyGZAUzmij4c76uz9TvM2seDcsRWP1zhfLMJfRdyk"},
    {"name": "Scholar", "address": "7AEpoq5eKoSRUN36CTFFPQESDXepcSby7CfQZs44wgds"}
]

def get_holder_count(mint_address, rpc_url):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getProgramAccounts",
        "params": [
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
            {
                "encoding": "jsonParsed",
                "filters": [
                    {"dataSize": 165},
                    {
                        "memcmp": {
                            "offset": 0,
                            "bytes": mint_address
                        }
                    }
                ]
            }
        ]
    }
    
    try:
        req = urllib.request.Request(
            rpc_url, 
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if 'error' in data:
                print(f"  [Error] RPC {rpc_url} returned error: {data['error']['message']}")
                return None
            return len(data.get('result', []))
            
    except Exception as e:
        print(f"  [Fail] RPC {rpc_url} failed: {e}")
        return None

def main():
    print("Fetching Solana holder counts...")
    results = {}
    
    for badge in BADGES:
        print(f"\nQuerying {badge['name']} ({badge['address']})...")
        success = False
        
        for rpc in RPC_ENDPOINTS:
            print(f"  Trying {rpc}...")
            count = get_holder_count(badge['address'], rpc)
            
            if count is not None:
                results[badge['address']] = count
                print(f"  -> Success! Count: {count}")
                success = True
                break
            else:
                time.sleep(1) # 失败后稍作等待
        
        if not success:
            print(f"  -> All RPCs failed for {badge['name']}")
    
    # 输出结果供读取
    print("\n---JSON_START---")
    print(json.dumps(results))
    print("---JSON_END---")

if __name__ == "__main__":
    main()
