import json
import urllib.request
import urllib.error
import time

# 待测试的 Helius RPC 节点
# 第一个通常是标准 RPC/DAS 节点
# 第二个看起来像特定的 Transaction API，可能不支持通用 DAS
RPC_CANDIDATES = [
    "https://mainnet.helius-rpc.com/?api-key=236b88d9-ac4e-4da5-9361-c17b6b9661a4",
    "https://api-mainnet.helius-rpc.com/v0/transactions/?api-key=236b88d9-ac4e-4da5-9361-c17b6b9661a4"
]

BADGES = [
    {"name": "Newcomer", "address": "Cpy7V4GKHVbJaVchR5qKPANtccjVC5bBbtabZJX6E2gT"},
    {"name": "Researcher", "address": "7oXuyGZAUzmij4c76uz9TvM2seDcsRWP1zhfLMJfRdyk"},
    {"name": "Scholar", "address": "7AEpoq5eKoSRUN36CTFFPQESDXepcSby7CfQZs44wgds"}
]

def make_das_request(rpc_url, method, params):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    
    try:
        req = urllib.request.Request(
            rpc_url, 
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"    [Error] {e}")
        return None

def test_rpc(rpc_url):
    print(f"\nTesting RPC: {rpc_url}")
    
    # 测试第一个徽章
    badge = BADGES[0]
    print(f"  Querying {badge['name']} ({badge['address']})...")
    
    # DAS API: getAssetsByGroup
    params = {
        "groupKey": "collection",
        "groupValue": badge['address'],
        "page": 1,
        "limit": 1
    }
    
    data = make_das_request(rpc_url, "getAssetsByGroup", params)
    
    if data and 'result' in data:
        result = data['result']
        if 'total' in result:
            print(f"    -> Success! Total Assets: {result['total']}")
            return True
        elif 'items' in result:
             print(f"    -> Partial Success (No total field). Items: {len(result['items'])}")
             return True
    elif data and 'error' in data:
        print(f"    -> RPC Error: {data['error']['message']}")
    else:
        print("    -> Failed or empty result")
    
    return False

def main():
    print("Testing Helius RPC endpoints for DAS support...")
    
    working_rpc = None
    
    for rpc in RPC_CANDIDATES:
        if test_rpc(rpc):
            working_rpc = rpc
            break
            
    if working_rpc:
        print(f"\n✅ Found working RPC: {working_rpc}")
    else:
        print("\n❌ All RPCs failed.")

if __name__ == "__main__":
    main()
