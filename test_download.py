import urllib.request
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://taxinformation.cbic.gov.in/api/cbic-circular-msts/download/1000001/ENG"
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx) as response:
        print(f"Status: {response.status}")
        data = json.loads(response.read().decode('utf-8'))
        print("Got data field length:", len(data.get("data", "")))
except Exception as e:
    print(f"Error: {e}")
