# CBIC Data Extraction Status

**Last Updated:** March 14, 2026  
**Portal:** https://taxinformation.cbic.gov.in  

---

## Tax Types on CBIC Portal

| ID | Tax Type | Status |
|---|---|---|
| `1000001` | **GST** | ✅ Extraction Complete (Notifications, Circulars, Orders, Instructions, Forms) |
| `1000002` | **Customs** | 📋 Metadata Complete (PDFs pending) |
| `1000003` | **Central Excise** | ⬜ Not Started |
| `100005` | **HSNS Cess** | ⬜ Not Started |

---

## ✅ Completed Extractions

### 1. GST Notifications

**Status:** ✅ Fully Extracted  
**Documents:** 1,281 notifications (2017–2025)  
**Pipeline:** `scrape` → `organize` → `download` → `analyze`

| Year | Count | English PDFs | Hindi PDFs | Notes |
|---|---|---|---|---|
| 2017 | 284 | ✅ 100% | ✅ Complete | |
| 2018 | 196 | ✅ 100% | ✅ Complete | |
| 2019 | 190 | ✅ 100% | ✅ Complete | |
| 2020 | 127 | ✅ 100% | ✅ Complete | |
| 2021 | 116 | ✅ 100% | ✅ Complete | |
| 2022 | 78 | ✅ 100% | ✅ Complete | |
| 2023 | 131 | ✅ 100% | ✅ Complete | |
| 2024 | 66 | ✅ 100% | ✅ Complete | |
| 2025 | 93 | ✅ 100% | ✅ Complete | |

**Categories:** Central Tax, Central Tax (Rate), Integrated Tax, Integrated Tax (Rate), Union Territory Tax, Union Territory Tax (Rate), Compensation Cess, Compensation Cess (Rate)

---

### 2. GST Circulars

**Status:** ✅ Fully Extracted  
**Documents:** 271 circulars (2017–2025)  
**Pipeline:** `scrape-circ` → `organize-circ` → `download-circ` → `analyze-circ`

| Year | Count | English PDFs | Hindi PDFs | Hindi Missing (Server 500) |
|---|---|---|---|---|
| 2017 | 29 | ✅ 100% | 20/29 | 9 |
| 2018 | 59 | ✅ 100% | 15/59 | 44 |
| 2019 | 56 | ✅ 100% | 23/56 | 33 |
| 2020 | 14 | ✅ 100% | 1/14 | 13 |
| 2021 | 25 | ✅ 100% | 0/25 | 25 |
| 2022 | 20 | ✅ 100% | 1/20 | 19 |
| 2023 | 18 | ✅ 100% | 0/18 | 18 |
| 2024 | 38 | ✅ 100% | 8/38 | 30 |
| 2025 | 12 | ✅ 100% | 7/11 | 4 |

> [!NOTE]
> 195 Hindi circular PDFs are unavailable due to CBIC server-side `HTTP 500` errors. This is a known upstream issue, not a pipeline bug. Failures are logged in each folder's `metadata.json`.

---

### 3. GST Orders

**Status:** ✅ Fully Extracted  
**Documents:** 39 orders (2017–2022)  
**Pipeline:** `scrape-order` → `organize-order` → `download-order` → `analyze-order`

| Year | Count | English PDFs | Hindi PDFs | Notes |
|---|---|---|---|---|
| 2017 | 13 | ✅ 100% | 2/2 ✅ | |
| 2018 | 8 | ✅ 100% | 4/4 ✅ | |
| 2019 | 15 | ✅ 100% | 13/13 ✅ | |
| 2020 | 2 | ✅ 100% | 1/1 ✅ | |
| 2022 | 1 | ✅ 100% | 0 expected | No Hindi reference |

**Categories:** Order-CGST, Order-UTSGT, Removal of Difficulty - CGST, Removal of Difficulty - UTGST

> [!NOTE]
> No GST orders exist for 2021, 2023–2025. Removal of Difficulty orders expired legally on June 30, 2020 (Section 172 CGST Act — 3-year limit from July 1, 2017).

---

### 4. GST Instructions

**Status:** ✅ Fully Extracted  
**Documents:** 42 instructions (2019–2025)  
**Pipeline:** `scrape-inst` → `organize-inst` → `download-inst` → `analyze-inst`

| Year | Count | English PDFs | Hindi PDFs | Notes |
|---|---|---|---|---|
| 2019 | 5 | 4/5 ✅ | 4/4 ✅ | 1 empty instruction_no (Corrigendum) |
| 2020 | 4 | 3/4 ✅ | 0 expected | 1 empty instruction_no |
| 2021 | 7 | 5/7 ✅ | 4/4 ✅ | 2 empty instruction_no |
| 2022 | 8 | 8/8 ✅ | 4/4 ✅ | |
| 2023 | 5 | 5/5 ✅ | 0 expected | |
| 2024 | 5 | 5/5 ✅ | 3/3 ✅ | |
| 2025 | 7 | 6/7 ✅ | 6/6 ✅ | 1 empty instruction_no |

> [!NOTE]
> 5 records have empty `instructionNo` fields (Corrigendum/Addendum entries in the CBIC database). PDFs were downloaded but can't be path-verified by the analyzer.

---

### 5. GST Forms

**Status:** ✅ Fully Extracted  
**Documents:** 197 forms (196 PDFs + 1 server error) across 21 categories  
**Pipeline:** `scrape-forms` → `download-forms` → `analyze-forms`  
**API:** Bulk fetch — `/api/cbic-form-msts/fetchForms/1000001`

| Category | Forms | Status |
|---|---|---|
| Registration | 33 | ✅ |
| Demand & Recovery | 31 | ✅ |
| Return | 22 | ✅ |
| Assessment | 18 | ✅ |
| Refund | 16 | ✅ |
| Appeal | 12 | ✅ |
| Payment | 9 | ✅ |
| Composition Levy | 8 | ✅ |
| GST Amnesty 2024 | 8 | ✅ |
| Other (12 categories) | 40 | ✅ |

> [!NOTE]
> 1 form (ID 1000379, empty formNo, category "All") returns server_error_500 — likely an orphan/broken record in CBIC database.

---

## 📋 Metadata Complete (PDFs Pending)

### 6. Customs Notifications

**Status:** 📋 Metadata Extracted — PDFs not yet downloaded  
**Documents:** 6,872 notifications (1935–2026)  
**Pipeline:** `scrape-customs` → `organize-customs` → `download-customs` → `analyze-customs`

| Era | Years | Count |
|---|---|---|
| Historical | 1935–1999 | 196 |
| 2000s | 2000–2009 | 2,346 |
| 2010s | 2010–2019 | 2,034 |
| 2020s | 2020–2026 | 1,427 |

---

### 7. Customs Circulars

**Status:** 📋 Metadata Extracted — PDFs not yet downloaded  
**Documents:** 1,760 circulars (1995–2026)  
**Pipeline:** `scrape-customs-circ` → `organize-customs-circ` → `download-customs-circ` → `analyze-customs-circ`

---

### 8. Customs Instructions

**Status:** 📋 Metadata Extracted — PDFs not yet downloaded  
**Documents:** 393 instructions (2004–2026)  
**Pipeline:** `scrape-customs-inst` → `organize-customs-inst` → `download-customs-inst` → `analyze-customs-inst`

---

## ⬜ Remaining Extractions

### 9. Central Excise Notifications
- **API Endpoint:** `GET /api/cbic-notification-msts/{id}` (filter `tax.id = 1000003`)
- **Estimated Volume:** Unknown — likely pre-2017 data
- **Approach:** Reuse notifications pipeline with Central Excise tax filter

### 10. Central Excise Circulars
- **API Endpoint:** `GET /api/cbic-circular-msts/{id}` (filter `tax.id = 1000003`)
- **Estimated Volume:** Unknown
- **Approach:** Reuse circulars pipeline with Central Excise tax filter

### 11. HSNS Cess Notifications / Circulars
- **Tax ID:** `100005`
- **Estimated Volume:** Unknown — may be minimal
- **Approach:** Reuse existing pipelines

---

## Data Layout

```
data/
├── gst/
│   ├── notifications/         # 1,281 docs — year/category/english+hindi PDFs
│   ├── circulars/             # 271 docs
│   ├── orders/                # 39 docs
│   ├── instructions/          # 42 docs
│   └── forms/                 # 197 docs — organized by category (not year)
│       ├── metadata/          # Per-category JSONs + summary
│       ├── downloads/         # PDFs in {category}/{id}/ folders
│       └── logs/
└── customs/
    ├── notifications/         # 6,872 — metadata only
    ├── circulars/             # 1,760 — metadata only
    └── instructions/          # 393 — metadata only
```

Each module follows the pattern: `metadata/` (raw + organized JSONs), `downloads/` (PDFs with per-item `metadata.json`), `logs/` (progress + errors).

---

## CLI Reference

```bash
# GST Notifications
python run.py scrape                          # Scrape metadata
python run.py organize                        # Organize into year JSONs
python run.py download <year> [-l ENG|HINDI|BOTH]  # Download PDFs
python run.py analyze <year>                  # Verify completeness

# GST Circulars
python run.py scrape-circ / organize-circ / download-circ <year> / analyze-circ <year>

# GST Orders
python run.py scrape-order / organize-order / download-order <year> / analyze-order <year>

# GST Instructions
python run.py scrape-inst / organize-inst / download-inst <year> / analyze-inst <year>

# GST Forms (bulk API — no year argument)
python run.py scrape-forms                    # Fetch all 197 forms
python run.py download-forms                  # Download all PDFs
python run.py analyze-forms                   # Verify completeness

# Customs Notifications
python run.py scrape-customs / organize-customs / download-customs <year> / analyze-customs <year>

# Customs Circulars
python run.py scrape-customs-circ / organize-customs-circ / download-customs-circ <year> / analyze-customs-circ <year>

# Customs Instructions
python run.py scrape-customs-inst / organize-customs-inst / download-customs-inst <year> / analyze-customs-inst <year>
```
