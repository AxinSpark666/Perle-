import urllib.request
import urllib.error
import json

def try_url(url):
    print(f"Testing: {url}")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"  -> Status: {response.status}")
            content = response.read().decode('utf-8')
            # Try to parse as JSON
            try:
                data = json.loads(content)
                print("  -> JSON response received!")
                if isinstance(data, dict):
                     keys = list(data.keys())[:5]
                     print(f"  -> Keys: {keys}")
                     if 'data' in data:
                         print(f"  -> 'data' field length: {len(data['data'])}")
                return True
            except json.JSONDecodeError:
                print("  -> Not JSON (likely HTML)")
                if "NEXT_DATA" in content:
                    print("  -> Found NEXT_DATA (Next.js app)")
                return False
    except urllib.error.HTTPError as e:
        print(f"  -> HTTP Error: {e.code}")
    except Exception as e:
        print(f"  -> Error: {e}")
    return False

endpoints = [
    "https://api.perle.xyz/projects",
    "https://api.perle.xyz/api/projects",
    "https://app.perle.xyz/api/projects",
    "https://perle-web3-prod.storage.googleapis.com/projects.json", # Guessing
    "https://api.perle.xyz/v1/projects",
]

# Try to find API
found = False
for ep in endpoints:
    if try_url(ep):
        found = True
        break

# Try to scrape main page for NEXT_DATA
def scrape_next_data(url):
    print(f"\nScraping {url} for NEXT_DATA...")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
            if '<script id="__NEXT_DATA__" type="application/json">' in content:
                print("  -> Found __NEXT_DATA__!")
                start = content.find('<script id="__NEXT_DATA__" type="application/json">') + len('<script id="__NEXT_DATA__" type="application/json">')
                end = content.find('</script>', start)
                json_str = content[start:end]
                try:
                    data = json.loads(json_str)
                    print("  -> Parsed JSON successfully")
                    # Try to find tasks/projects in props
                    if 'props' in data and 'pageProps' in data['props']:
                        pp = data['props']['pageProps']
                        # Recursive search for "projects" or "tasks"
                        print(f"  -> pageProps keys: {list(pp.keys())}")
                        return data
                except:
                    print("  -> Failed to parse JSON")
            else:
                print("  -> __NEXT_DATA__ not found")
    except Exception as e:
        print(f"  -> Error: {e}")

scrape_next_data("https://app.perle.xyz/marketplace")
scrape_next_data("https://app.perle.xyz/")
