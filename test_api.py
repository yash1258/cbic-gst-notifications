import urllib.request
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    "https://taxinformation.cbic.gov.in/api/cbic-circular-msts/1000001",
    "https://taxinformation.cbic.gov.in/api/cbic-circulars-msts/1000001",
    "https://taxinformation.cbic.gov.in/api/cbic-circular-msts",
    "https://taxinformation.cbic.gov.in/api/cbic-circulars",
    "https://taxinformation.cbic.gov.in/api/cbic-circular-msts/1010000",
    "https://taxinformation.cbic.gov.in/api/cbic-circular-msts/2000001",
]

for url in urls:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            print(f"[OK] {url} -> {response.status}")
    except urllib.error.HTTPError as e:
        print(f"[HTTP ERROR] {url} -> {e.code}")
    except urllib.error.URLError as e:
        print(f"[URL ERROR] {url} -> {e.reason}")
    except Exception as e:
        print(f"[ERROR] {url} -> {e}")
