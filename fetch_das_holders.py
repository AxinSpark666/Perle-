import json
import urllib.request
import urllib.error
import time

# 尝试使用 DAS API 查询 Metaplex Core 资产
# 由于用户提供了一个 Alchemy Key (可能支持 DAS)，我们优先尝试它。
# 如果失败，我们可以尝试一些公共 DAS 节点（如 Helius 的免费层，如果我有 Key 的话...但没有）。
# 公共节点通常不支持 DAS。

ALCHEMY_RPC = "https://solana-mainnet.g.alchemy.com/v2/MSfS3EuDwErM0Ruv46cOO"

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
            ALCHEMY_RPC, 
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"  [Error] {e}")
        return None

def get_asset_count(collection_address):
    print(f"Querying DAS API for collection {collection_address}...")
    # DAS API: getAssetsByGroup
    params = {
        "groupKey": "collection",
        "groupValue": collection_address,
        "page": 1,
        "limit": 1 # 我们只需要 total count，如果 API 返回 total
    }
    
    data = make_das_request("getAssetsByGroup", params)
    
    if data and 'result' in data:
        result = data['result']
        if 'total' in result:
            count = result['total']
            print(f"  -> Total Assets (Holders): {count}")
            return count
        elif 'items' in result:
             # 如果不支持 total 字段，可能需要分页统计... 但这太慢了。
             # 或者尝试用 getAssetProof 等其他方法？
             # 通常 getAssetsByGroup 会返回 total。
             print(f"  -> Items returned: {len(result['items'])}")
             if len(result['items']) == 0:
                 return 0
             return "Unknown (No total field)"
    elif data and 'error' in data:
        print(f"  -> DAS Error: {data['error']['message']}")
    else:
        print("  -> Failed or empty result")
    
    return None

def main():
    results = {}
    for badge in BADGES:
        print(f"\n--- Analyzing {badge['name']} ---")
        count = get_asset_count(badge['address'])
        if count is not None and isinstance(count, int):
            results[badge['address']] = count
        else:
            results[badge['address']] = 0 # 默认为 0
            
        time.sleep(1)

    print("\n---JSON_START---")
    print(json.dumps(results))
    print("---JSON_END---")

if __name__ == "__main__":
    main()
