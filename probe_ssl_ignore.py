import urllib.request
import urllib.error
import ssl
import json

# Create unverified context
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def try_url(url):
    print(f"Testing: {url}")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
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
                     if 'items' in data:
                         print(f"  -> 'items' field length: {len(data['items'])}")
                return True
            except json.JSONDecodeError:
                print("  -> Not JSON")
                # print first 100 chars
                print(f"  -> Content preview: {content[:100]}")
                return False
    except urllib.error.HTTPError as e:
        print(f"  -> HTTP Error: {e.code}")
    except Exception as e:
        print(f"  -> Error: {e}")
    return False

endpoints = [
    "https://api.perle.xyz/projects",
    "https://api.perle.xyz/v1/projects",
    "https://api.perle.xyz/api/projects",
    "https://api-mainnet.perle.xyz/projects",
    "https://backend.perle.xyz/projects",
]

for ep in endpoints:
    try_url(ep)
