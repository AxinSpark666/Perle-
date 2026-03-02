import json
import urllib.request
import urllib.error
import time

RPC_URL = "https://api.mainnet-beta.solana.com" # 官方节点，虽然慢但最准确

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
        
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"  [Error] {e}")
        return None

def check_account_info(address):
    print(f"Checking account info for {address}...")
    data = make_request("getAccountInfo", [address, {"encoding": "jsonParsed"}])
    if data and 'result' in data:
        value = data['result']['value']
        if value:
            print(f"  Owner: {value.get('owner')}")
            print(f"  Lamports: {value.get('lamports')}")
            if 'data' in value and isinstance(value['data'], dict):
                parsed = value['data'].get('parsed')
                if parsed:
                    print(f"  Type: {parsed.get('type')}")
                    info = parsed.get('info', {})
                    if info:
                        print(f"  Decimals: {info.get('decimals')}")
                        print(f"  Supply: {info.get('supply')}")
        else:
            print("  Account not found!")
    else:
        print("  Failed to get account info")

def get_holders(mint_address):
    print(f"Getting holders for {mint_address}...")
    # 尝试不加 dataSize 过滤，只用 memcmp
    # 并且只获取 pubkey，减少数据传输
    params = [
        "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
        {
            "encoding": "jsonParsed",
            "filters": [
                {
                    "memcmp": {
                        "offset": 0,
                        "bytes": mint_address
                    }
                }
            ],
            "dataSlice": {"offset": 0, "length": 0} # 不获取数据内容，只统计数量
        }
    ]
    
    data = make_request("getProgramAccounts", params)
    if data and 'result' in data:
        count = len(data['result'])
        print(f"  -> Count: {count}")
        return count
    else:
        print("  -> Failed or empty result")
        return None

def main():
    results = {}
    for badge in BADGES:
        print(f"\n--- Analyzing {badge['name']} ---")
        check_account_info(badge['address'])
        
        # 尝试获取持有者
        count = get_holders(badge['address'])
        if count is not None:
            results[badge['address']] = count
        else:
            results[badge['address']] = 0 # 默认为 0
        
        time.sleep(1) # 避免限流

    print("\n---JSON_START---")
    print(json.dumps(results))
    print("---JSON_END---")

if __name__ == "__main__":
    main()
