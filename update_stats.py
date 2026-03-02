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
    {"id": "scholar", "address": "7AEpoq5eKoSRUN36CTFFPQESDXepcSby7CfQZs44wgds"}
]

def get_beijing_date():
    """获取当前北京时间的日期 (YYYY-MM-DD)"""
    # 使用 timezone-aware datetime 对象，避免 DeprecationWarning
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    beijing_now = utc_now + datetime.timedelta(hours=8)
    return beijing_now.strftime("%Y-%m-%d")

def fetch_count(address):
    """从 RPC 获取持有数量"""
    # 策略1: getAsset (优先)
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAsset",
            "params": {"id": address}
        }
        req = urllib.request.Request(
            RPC_ENDPOINT,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if 'result' in data and 'mpl_core_info' in data['result']:
                return data['result']['mpl_core_info']['current_size']
    except Exception as e:
        print(f"Strategy 1 failed for {address}: {e}")

    # 策略2: getAssetsByGroup (回退)
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAssetsByGroup",
            "params": {
                "groupKey": "collection",
                "groupValue": address,
                "page": 1,
                "limit": 1
            }
        }
        req = urllib.request.Request(
            RPC_ENDPOINT,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if 'result' in data and 'total' in data['result']:
                return data['result']['total']
    except Exception as e:
        print(f"Strategy 2 failed for {address}: {e}")
    
    return None

def update_stats():
    print(f"Starting update at {datetime.datetime.now()}")
    
    # 1. 读取现有数据
    history = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            print("Error reading existing file, starting fresh.")
            history = []

    # 2. 获取今日数据
    today_date = get_beijing_date()
    print(f"Target Date (Beijing): {today_date}")

    # 查找今天是否已存在
    existing_index = -1
    for i, entry in enumerate(history):
        if entry.get("date") == today_date:
            existing_index = i
            break
    
    if existing_index != -1:
        print("Update existing entry for today.")
        new_entry = history[existing_index]
        # 更新时间戳
        new_entry["timestamp"] = int(time.time() * 1000)
    else:
        print("Create new entry for today.")
        new_entry = {
            "date": today_date,
            "timestamp": int(time.time() * 1000)
        }
        history.append(new_entry)

    for badge in BADGES:
        print(f"Fetching {badge['id']}...")
        count = fetch_count(badge['address'])
        if count is not None:
            new_entry[badge['id']] = count
            
    # 3. 保存 (保持按日期排序)
    # 简单的按日期字符串排序
    history.sort(key=lambda x: x["date"])
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)
        
    # 同时保存为 JS 文件，供前端直接读取 (解决 file:// 协议跨域问题)
    js_content = f"window.BADGE_HISTORY = {json.dumps(history, indent=2)};"
    with open('js/badge_data.js', 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print(f"Successfully updated {DATA_FILE} and js/badge_data.js")

    # 更新 index.html 中的引用，增加版本号以防止缓存
    try:
        if os.path.exists(INDEX_FILE):
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用正则替换 script 引用，添加时间戳作为版本号
            timestamp = int(time.time())
            new_content = re.sub(
                r'src="js/badge_data\.js(\?v=\d+)?"', 
                f'src="js/badge_data.js?v={timestamp}"', 
                content
            )
            
            if new_content != content:
                with open(INDEX_FILE, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated {INDEX_FILE} with new cache buster: v={timestamp}")
    except Exception as e:
        print(f"Failed to update {INDEX_FILE}: {e}")

if __name__ == "__main__":
    update_stats()
