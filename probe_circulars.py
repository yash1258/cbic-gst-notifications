import urllib.request
import ssl
import json
import asyncio

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

async def check_id(nid):
    url = f"https://taxinformation.cbic.gov.in/api/cbic-circular-msts/{nid}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla'})
    try:
        urllib.request.urlopen(req, context=ctx, timeout=5)
        return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        return True # exists but error
    except Exception:
        return False

async def main():
    low = 1000001
    high = 1050000
    max_found = 1000001
    
    # Let's do a simple exponential search to find upper bound, then binary search
    step = 1000
    curr = low
    while True:
        exists = await check_id(curr)
        if exists:
            max_found = curr
            curr += step
        else:
            high = curr
            break
            
    print(f"Upper bound found at {high}. Doing binary search between {max_found} and {high}...")
    
    low = max_found
    while low <= high:
        mid = (low + high) // 2
        exists = await check_id(mid)
        if exists:
            low = mid + 1
            max_found = mid
        else:
            high = mid - 1
            
    print(f"Max Circular ID: {max_found}")

if __name__ == "__main__":
    asyncio.run(main())
