import urllib.request
import ssl
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://taxinformation.cbic.gov.in/api/cbic-tax-msts"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode('utf-8'))
        for item in data:
            print(f"Tax ID: {item.get('id')} - {item.get('taxName')}")
except Exception as e:
    print(f"Error: {e}")
