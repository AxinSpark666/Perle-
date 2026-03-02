import json
import urllib.request
import datetime
import time
import os
import re

# 配置
RPC_ENDPOINT = "https://mainnet.helius-rpc.com/?api-key=236b88d9-ac4e-4da5-9361-c17b6b9661a4"
DATA_FILE = "badge_stats.json"
INDEX_FILE = "index.html"
DAYS_TO_TRACE = 45

# 徽章配置
BADGES = [
    {"id": "newcomer", "address": "Cpy7V4GKHVbJaVchR5qKPANtccjVC5bBbtabZJX6E2gT"},
    {"id": "researcher", "address": "7oXuyGZAUzmij4c76uz9TvM2seDcsRWP1zhfLMJfRdyk"},
    {"id": "scholar", "address": "7AEpoq5eKoSRUN36CTFFPQESDXepcSby7CfQZs44wgds"}
]

def get_beijing_datetime(ts):
    """将 Unix 时间戳转换为北京时间 datetime 对象"""
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc) + datetime.timedelta(hours=8)

def get_beijing_date_str(ts):
    """获取北京时间的日期字符串 YYYY-MM-DD"""
    return get_beijing_datetime(ts).strftime("%Y-%m-%d")

def fetch_current_supply(address):
    """获取当前总供应量"""
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
    except:
        pass
    
    # Fallback
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAssetsByGroup",
            "params": {"groupKey": "collection", "groupValue": address, "page": 1, "limit": 1}
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
    except:
        pass
    return None

def fetch_signatures(address, days_limit=30):
    """获取指定天数内的所有交易签名"""
    all_sigs = []
    before = None
    
    # 计算截止时间戳
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff_time = now - datetime.timedelta(days=days_limit + 2) # 多取一点缓冲
    cutoff_ts = cutoff_time.timestamp()
    
    print(f"  Fetching history for {address} (cutoff: {cutoff_time})...")
    
    while True:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [
                address,
                {"limit": 1000}
            ]
        }
        if before:
            payload["params"][1]["before"] = before

        try:
            req = urllib.request.Request(
                RPC_ENDPOINT,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                data = json.loads(response.read().decode('utf-8'))
                sigs = data.get('result', [])
                
                if not sigs:
                    break
                
                # 过滤错误交易并收集时间戳
                valid_sigs = [s for s in sigs if s.get('err') is None]
                all_sigs.extend(valid_sigs)
                
                last_ts = sigs[-1]['blockTime']
                before = sigs[-1]['signature']
                
                # 打印进度
                # print(f"    Fetched {len(sigs)} sigs, last date: {get_beijing_date_str(last_ts)}")

                if last_ts < cutoff_ts:
                    break
                    
                time.sleep(0.2) # 避免速率限制
                
        except Exception as e:
            print(f"    Error fetching signatures: {e}")
            break
            
    return all_sigs

def reconstruct_history():
    print("Starting historical data reconstruction...")
    
    # 1. 初始化日期映射
    # 生成过去30天的日期列表
    today = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)
    date_list = []
    for i in range(DAYS_TO_TRACE + 1):
        d = today - datetime.timedelta(days=i)
        date_list.append(d.strftime("%Y-%m-%d"))
    date_list.sort() # 从旧到新
    
    # 数据结构: { "2026-02-01": { "newcomer": 0, "researcher": 0 ... } }
    daily_stats = {date: {} for date in date_list}
    
    # 2. 对每个徽章进行回溯
    for badge in BADGES:
        badge_id = badge['id']
        address = badge['address']
        
        print(f"Processing {badge_id}...")
        
        # 获取当前总数
        current_supply = fetch_current_supply(address)
        if current_supply is None:
            print(f"  Failed to get current supply for {badge_id}, skipping.")
            continue
            
        print(f"  Current Supply: {current_supply}")
        
        # 获取历史交易
        sigs = fetch_signatures(address, DAYS_TO_TRACE)
        print(f"  Total transactions found: {len(sigs)}")
        
        # 按日期聚合交易量
        tx_counts = {} # { "2026-02-12": 150, "2026-02-11": 200 }
        for s in sigs:
            ts = s['blockTime']
            date_str = get_beijing_date_str(ts)
            tx_counts[date_str] = tx_counts.get(date_str, 0) + 1
            
        # 回溯计算
        # 今天的最新值 = current_supply
        # 昨天的值 = 今天的值 - 今天的增量 (Tx Count)
        # 注意：这里的逻辑是“持有量”。
        # 如果今天是 2026-02-12，我们在 stats 中记录的是 02-12 的值（即 current_supply）。
        # 那么 02-11 的值应该是 02-12 的值 - 02-12 这一天发生的交易量。
        
        supply_cursor = current_supply
        
        # 按日期倒序遍历 (从今天往前)
        sorted_dates = sorted(date_list, reverse=True)
        
        for date_str in sorted_dates:
            # 记录当天的值（即当天结束时的值）
            if date_str in daily_stats:
                daily_stats[date_str][badge_id] = supply_cursor
            
            # 减去当天的交易量，为下一轮（即前一天）做准备
            day_tx_count = tx_counts.get(date_str, 0)
            supply_cursor = max(0, supply_cursor - day_tx_count)
            
    # 3. 转换为列表格式并保存
    final_history = []
    for date_str in date_list:
        entry = {
            "date": date_str,
            "timestamp": int(datetime.datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)
        }
        # 填充数据
        for badge in BADGES:
            entry[badge['id']] = daily_stats[date_str].get(badge['id'], 0)
            
        final_history.append(entry)
        
    # 保存文件 (JSON)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_history, f, indent=2)

    # 同时保存为 JS 文件，供前端直接读取 (解决 file:// 协议跨域问题)
    js_content = f"window.BADGE_HISTORY = {json.dumps(final_history, indent=2)};"
    with open('js/badge_data.js', 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print(f"Successfully reconstructed {len(final_history)} days of history to {DATA_FILE} and js/badge_data.js")

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
    reconstruct_history()
