import urllib.request
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://taxinformation.cbic.gov.in/api/cbic-circular-msts/1003000"
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode('utf-8'))
        print(f"ID 1003000 Tax ID: {data.get('tax', {}).get('id')} Date: {data.get('circularDt')}")
except Exception as e:
    print(f"Error 1003000: {e}")

url = "https://taxinformation.cbic.gov.in/api/cbic-circular-msts/1003300"
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode('utf-8'))
        print(f"ID 1003300 Tax ID: {data.get('tax', {}).get('id')} Date: {data.get('circularDt')}")
except Exception as e:
    print(f"Error 1003300: {e}")
