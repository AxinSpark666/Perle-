import json
import urllib.request
import urllib.error
import datetime
import os
import time
import re

# 配置
RPC_ENDPOINT = "https://mainnet.helius-rpc.com/?api-key=236b88d9-ac4e-4da5-9361-c17b6b9661a4"
DATA_FILE = "badge_stats.json"
INDEX_FILE = "index.html"

# 徽章配置
BADGES = [
    {"id": "newcomer", "address": "Cpy7V4GKHVbJaVchR5qKPANtccjVC5bBbtabZJX6E2gT"},
    {"id": "researcher", "address": "7oXuyGZAUzmij4c76uz9TvM2seDcsRWP1zhfLMJfRdyk"},
    {"id": "scholar", "address": "7AEpoq5eKoSRUN36CTFFPQESDXepcSby7CfQZs44wgds"},
    {"id": "speed_demon", "address": "5RgA8Vo6FnnAzre12JsLicoc66B7h8cwG99RRPFGTAgj"}
]

HUMAN_CAPTCHA_CREATOR = "DB1HvGZNTyRjQvoQfBLFVojpnSBzEwNKrFH4bMZD3uZb"

def get_beijing_date():
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    beijing_now = utc_now + datetime.timedelta(hours=8)
    return beijing_now.strftime("%Y-%m-%d")

def fetch_count(address):
    try:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getAsset", "params": {"id": address}}
        req = urllib.request.Request(RPC_ENDPOINT, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if 'result' in data and 'mpl_core_info' in data['result']:
                return data['result']['mpl_core_info']['current_size']
    except Exception as e:
        print(f"Strategy 1 failed for {address}: {e}")

    try:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getAssetsByGroup", "params": {"groupKey": "collection", "groupValue": address, "page": 1, "limit": 1}}
        req = urllib.request.Request(RPC_ENDPOINT, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if 'result' in data and 'total' in data['result']:
                return data['result']['total']
    except Exception as e:
        print(f"Strategy 2 failed for {address}: {e}")
    return None

def fetch_creator_assets_count(creator_address):
    page = 1
    limit = 1000
    all_owners = set()
    total_items = 0
    print(f"Fetching assets for creator: {creator_address}...")
    
    while True:
        try:
            payload = {"jsonrpc": "2.0", "id": "my-id", "method": "getAssetsByCreator", "params": {"creatorAddress": creator_address, "onlyVerified": True, "page": page, "limit": limit}}
            req = urllib.request.Request(RPC_ENDPOINT, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                if 'error' in data:
                    print(f"Error fetching creator assets: {data['error']}")
                    break
                result = data.get('result', {})
                items = result.get('items', [])
                if not items:
                    break
                total_items += len(items)
                for item in items:
                    owner = item.get('ownership', {}).get('owner')
                    if owner:
                        all_owners.add(owner)
                print(f"  Page {page}: Found {len(items)} items. Total unique owners: {len(all_owners)}")
                if len(items) < limit:
                    break
                page += 1
                time.sleep(0.1)
        except Exception as e:
            print(f"Exception fetching creator assets: {e}")
            break
    return len(all_owners)

def update_stats():
    print(f"Starting update at {datetime.datetime.now()}")
    
    history = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []

    today_date = get_beijing_date()
    existing_index = next((i for i, entry in enumerate(history) if entry.get("date") == today_date), -1)
    
    if existing_index != -1:
        new_entry = history[existing_index]
        new_entry["timestamp"] = int(time.time() * 1000)
    else:
        new_entry = {"date": today_date, "timestamp": int(time.time() * 1000)}
        history.append(new_entry)

    for badge in BADGES:
        count = fetch_count(badge['address'])
        if count is not None:
            new_entry[badge['id']] = count
            print(f"  -> {badge['id']}: {count}")

    human_captcha_count = fetch_creator_assets_count(HUMAN_CAPTCHA_CREATOR)
    if human_captcha_count > 0:
        new_entry["human_captcha"] = human_captcha_count
        print(f"  -> human_captcha: {human_captcha_count}")
            
    history.sort(key=lambda x: x["date"])
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)
        
    js_content = f"window.BADGE_HISTORY = {json.dumps(history, indent=2)};"
    with open('js/badge_data.js', 'w', encoding='utf-8') as f:
        f.write(js_content)

    # 移除了修改 js/script.js 的危险操作

    try:
        if os.path.exists(INDEX_FILE):
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            timestamp = int(time.time())
            new_content = re.sub(r'src="js/badge_data\.js(\?v=\d+)?"', f'src="js/badge_data.js?v={timestamp}"', content)
            if new_content != content:
                with open(INDEX_FILE, 'w', encoding='utf-8') as f:
                    f.write(new_content)
    except Exception as e:
        print(f"Failed to update {INDEX_FILE}: {e}")

if __name__ == "__main__":
    update_stats()
