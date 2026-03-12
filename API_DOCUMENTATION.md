# CBIC Tax Information Portal API Documentation

**Base URL:** `https://taxinformation.cbic.gov.in`  
**Authentication:** None required (public endpoints)  
**SSL Certificate:** Self-signed (disable verification)  
**Last Updated:** March 13, 2026  

---

## Overview

This document describes the public REST API endpoints discovered for the CBIC (Central Board of Indirect Taxes and Customs) Tax Information Portal. These endpoints provide access to GST, Customs, and Central Excise notifications, circulars, and related documents.

**Tax Type IDs:**
- `1000001` - GST (Goods and Services Tax)
- `1000002` - Customs
- `1000003` - Central Excise
- `100005` - HSNS Cess

---

## Endpoints

### 1. Get Tax Types

Lists all available tax types in the system.

**Endpoint:** `GET /api/cbic-tax-msts`

**Response:**
```json
[
  {
    "id": 1000001,
    "contentId": 1001000001,
    "taxName": "GST",
    "taxNameHi": "जीएसटी",
    "isActive": "Y",
    "createdBy": 1038563,
    "createdDt": "2021-07-21T05:30:00+05:30"
  }
]
```

---

### 2. Get Notification Metadata

Retrieves complete metadata for a specific notification by ID.

**Endpoint:** `GET /api/cbic-notification-msts/{id}`

**Parameters:**
- `id` (path, integer): Database ID of the notification (range: 1000001-1010588)

**Response (200 OK):**
```json
{
  "id": 1010546,
  "contentId": 1501010546,
  "contentLanguage": "ENGLISH",
  "isActive": "Y",
  "createdDt": "2026-01-01T05:30:00+05:30",
  "updatedDt": null,
  "isAmended": "",
  "isOmitted": "",
  "parentId": null,
  "orderId": 202512311020,
  "versionNo": null,
  "notificationNo": "20/2025-Central Tax",
  "notificationName": "Seeks to notify Central Goods and Services Tax (Fifth Amendment) Rules, 2025",
  "notificationCategory": "Central Tax",
  "notificationDt": "2025-12-31T05:30:00+05:30",
  "issueDt": null,
  "amendDt": null,
  "docFilePath": "tax_repository\\gst\\notifications\\20-2025-ct.pdf",
  "docFileName": "20-2025-ct.pdf",
  "docFilePathHi": "tax_repository\\gst\\notifications\\20-2025h-ct.pdf",
  "docFileNameHi": "20-2025h-ct.pdf",
  "docFilePathAOD": "",
  "docFileNameAOD": "",
  "tax": {
    "id": 1000001,
    "contentId": null,
    "taxName": null,
    "taxNameHi": null,
    "isActive": null,
    "createdBy": null,
    "createdDt": null,
    "updatedBy": null,
    "updatedDt": null
  },
  "isAttachment": null,
  "ntRemarks": null,
  "isHistory": null,
  "notificationNoHi": "",
  "notificationNameHi": "",
  "notificationCategoryHi": null,
  "notificationDtHi": null,
  "language": null
}
```

**Response Codes:**
- `200` - Success, notification found
- `404` - Notification ID does not exist

**Field Descriptions:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | integer | Database primary key | 1010546 |
| `notificationNo` | string | Official notification number | "20/2025-Central Tax" |
| `notificationName` | string | Subject/title of notification | "Seeks to notify Central Goods..." |
| `notificationCategory` | string | Category classification | "Central Tax" |
| `notificationDt` | string (ISO 8601) | Issue date | "2025-12-31T05:30:00+05:30" |
| `docFileName` | string | English PDF filename | "20-2025-ct.pdf" |
| `docFileNameHi` | string | Hindi PDF filename | "20-2025h-ct.pdf" |
| `isAmended` | string | Amendment flag ("Y" or "") | "" |
| `isOmitted` | string | Omission flag ("Y" or "") | "" |
| `parentId` | integer/null | Reference to parent if amended | null |
| `tax.id` | integer | Tax type ID | 1000001 (GST) |

**Categories Identified:**
- Central Tax
- Central Tax (Rate)
- Integrated Tax
- Integrated Tax (Rate)
- Union Territory Tax
- Union Territory Tax (Rate)
- Compensation Cess
- Compensation Cess (Rate)

---

### 3. Download Notification PDF

Downloads the PDF document for a notification (base64-encoded).

**Endpoint:** `GET /api/cbic-notification-msts/download/{id}/{language}`

**Parameters:**
- `id` (path, integer): Database ID of the notification
- `language` (path, string): Language code
  - `ENG` - English
  - `HIN` - Hindi (may return 500 for some notifications)

**Response (200 OK):**
```json
{
  "data": "JVBERi0xLjcKCjQgMCBvYmoKKElkZW50aXR5KQplbmRvYmo..."
}
```

The `data` field contains **base64-encoded PDF binary**.

**Decoding Example:**
```python
import base64
import json

response = '{"data": "JVBERi0xLjc..."}'
data = json.loads(response)
pdf_bytes = base64.b64decode(data["data"])

with open("notification.pdf", "wb") as f:
    f.write(pdf_bytes)
```

**Response Codes:**
- `200` - Success, PDF available
- `500` - Server error (common for Hindi PDFs or missing files)
- `404` - Notification not found

**Notes:**
- PDFs are typically 50KB-500KB in size
- Hindi PDFs (`HIN`) may return 500 error for some notifications
- The base64 string can be very long (hundreds of KB)

---

## ID Range Information

### Valid Notification IDs
- **Minimum:** 1000001
- **Maximum:** 1010588 (as of March 2026)
- **Total IDs:** ~10,588

### ID Distribution by Tax Type

**GST (tax.id = 1000001, 2017+):**
- 2017: 284 notifications
- 2018: 196 notifications
- 2019: 190 notifications
- 2020: 127 notifications
- 2021: 116 notifications
- 2022: 78 notifications
- 2023: 131 notifications
- 2024: 66 notifications
- 2025: 93 notifications
- **Total:** 1,281 GST notifications (2017-2025)

**Note:** IDs are NOT sequential by date or tax type. IDs contain mixed records from all tax types across the entire range.

---

## Implementation Notes

### Rate Limiting
- No documented rate limits
- Recommended: 5-10 concurrent connections max
- Suggested delay: 1 second per 100 requests
- Total scan time: ~18-20 minutes for full range

### SSL/TLS
The CBIC server uses a self-signed certificate. Disable SSL verification in your HTTP client:

**Python (aiohttp/requests):**
```python
# aiohttp
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# requests
requests.get(url, verify=False)
```

**cURL:**
```bash
curl -k "https://taxinformation.cbic.gov.in/api/cbic-notification-msts/1010546"
```

### Error Handling
- Implement exponential backoff for 429/503 errors
- Retry failed requests up to 3 times
- Log 404s silently (ID doesn't exist)
- Handle 500 errors gracefully (server issues)

### Resume Capability
Since IDs span a wide range without date ordering:
- Save progress after every 1000 IDs
- Store last successfully scanned ID
- Filter results client-side for specific tax types/date ranges

---

## Data Collection Statistics

**Scan Date:** March 13, 2026  
**Total IDs Scanned:** 10,588  
**GST Notifications Found (2017+):** 1,281  
**Errors Encountered:** 0  
**Success Rate:** 100%

**Collection Method:**
- Async concurrent scanning (5 connections)
- 1-second batch delays
- Exponential backoff retry logic
- 30-second request timeout

---

## Limitations

1. **No Search API** - Cannot query by date, category, or tax type
2. **No Pagination** - Must scan entire ID range
3. **Hindi PDFs** - Many return 500 errors (server-side issue)
4. **No Amendment Chains** - Parent-child relationships exist but require manual traversal
5. **Static IDs** - New notifications get sequential IDs, but no push notification system

---

## Use Cases

### 1. Metadata Extraction
Scrape all notification metadata for:
- Compliance tracking
- Historical analysis
- Amendment tracking
- Cross-referencing

### 2. Document Archive
Download PDFs for:
- Legal documentation
- Offline access
- Text extraction and embedding
- RAG (Retrieval-Augmented Generation) systems

### 3. Monitoring
Periodic scans (weekly/monthly) to:
- Detect new notifications
- Track amendments
- Build notification feeds

---

## Sample Implementation

```python
import aiohttp
import asyncio
import ssl

BASE_URL = "https://taxinformation.cbic.gov.in"

async def fetch_notification(session, notification_id):
    url = f"{BASE_URL}/api/cbic-notification-msts/{notification_id}"
    async with session.get(url, ssl=False) as response:
        if response.status == 200:
            return await response.json()
        return None

# Usage
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async with aiohttp.ClientSession() as session:
    data = await fetch_notification(session, 1010546)
    print(data["notificationNo"])  # "20/2025-Central Tax"
```

---

## Related Endpoints (Require Authentication)

These endpoints return 401 Unauthorized and require authentication:
- `GET /api/notifications`
- `GET /api/content-types`
- `GET /api/_search/*`

They appear to be administrative/internal endpoints not intended for public access.

---

## Changelog

**v1.0 - March 13, 2026**
- Initial documentation
- Documented 3 public endpoints
- Added ID range and statistics
- Included implementation examples

---

**Disclaimer:** This documentation is based on reverse engineering and public API exploration. CBIC may change endpoints or add authentication without notice. Use responsibly and respect rate limits.
