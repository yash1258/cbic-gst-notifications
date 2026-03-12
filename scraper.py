"""
CBIC GST Notification Scraper
Scans the CBIC API to collect GST notification metadata from 2017 onwards.
Uses async/await with very gentle settings to avoid overloading the server.
"""

import asyncio
import json
import os
import ssl
import time
from datetime import datetime
from pathlib import Path

import aiohttp

import config


def ensure_dirs():
    """Create required directories."""
    for d in [config.DATA_DIR, config.ERROR_DIR]:
        os.makedirs(d, exist_ok=True)


def load_progress():
    """Load last scanned ID from progress file."""
    if os.path.exists(config.PROGRESS_FILE):
        with open(config.PROGRESS_FILE, "r") as f:
            data = json.load(f)
            return data.get("last_id", config.ID_START - 1)
    return config.ID_START - 1


def save_progress(last_id):
    """Save last scanned ID for resume capability."""
    with open(config.PROGRESS_FILE, "w") as f:
        json.dump({"last_id": last_id, "updated_at": datetime.now().isoformat()}, f)


def load_existing_results():
    """Load existing results if resuming."""
    if os.path.exists(config.RAW_METADATA_FILE):
        with open(config.RAW_METADATA_FILE, "r") as f:
            return json.load(f)
    return []


def save_results(notifications):
    """Save raw metadata to JSON file."""
    with open(config.RAW_METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(notifications, f, indent=2, ensure_ascii=False, default=str)


def save_errors(errors):
    """Save error log to JSON file."""
    with open(config.ERROR_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(errors, f, indent=2, ensure_ascii=False, default=str)


def parse_notification(record):
    """Extract relevant fields from API response."""
    tax_id = record.get("tax", {}).get("id")
    date_str = record.get("notificationDt", "")
    
    # Filter: GST only, date >= 2017
    if tax_id != config.GST_TAX_ID:
        return None
    if date_str and date_str[:10] < config.MIN_DATE:
        return None
    
    return {
        "id": record.get("id"),
        "notificationNo": record.get("notificationNo", ""),
        "notificationDt": date_str[:10] if date_str else "",
        "notificationName": record.get("notificationName", ""),
        "notificationCategory": record.get("notificationCategory", ""),
        "notificationNoHi": record.get("notificationNoHi", ""),
        "notificationNameHi": record.get("notificationNameHi", ""),
        "docFileName": record.get("docFileName", ""),
        "docFileNameHi": record.get("docFileNameHi", ""),
        "docFilePath": record.get("docFilePath", ""),
        "isAmended": record.get("isAmended", ""),
        "isOmitted": record.get("isOmitted", ""),
        "parentId": record.get("parentId"),
        "orderId": record.get("orderId"),
    }


async def fetch_notification(session, notification_id, semaphore, errors):
    """Fetch a single notification by ID with retry logic."""
    url = f"{config.BASE_URL}{config.METADATA_ENDPOINT.format(id=notification_id)}"
    
    async with semaphore:
        for attempt in range(config.MAX_RETRIES):
            try:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT_SECONDS),
                    ssl=False
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return parse_notification(data)
                    elif response.status == 404:
                        return None  # ID doesn't exist, skip silently
                    elif response.status in (429, 503):
                        # Rate limited - wait and retry
                        wait_time = config.RETRY_DELAY_BASE ** (attempt + 1)
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        errors.append({
                            "id": notification_id,
                            "status": response.status,
                            "attempt": attempt + 1,
                            "error": f"HTTP {response.status}",
                            "timestamp": datetime.now().isoformat()
                        })
                        return None
            except asyncio.TimeoutError:
                errors.append({
                    "id": notification_id,
                    "status": None,
                    "attempt": attempt + 1,
                    "error": "Timeout",
                    "timestamp": datetime.now().isoformat()
                })
                if attempt < config.MAX_RETRIES - 1:
                    await asyncio.sleep(config.RETRY_DELAY_BASE ** (attempt + 1))
            except aiohttp.ClientError as e:
                errors.append({
                    "id": notification_id,
                    "status": None,
                    "attempt": attempt + 1,
                    "error": str(e)[:200],
                    "timestamp": datetime.now().isoformat()
                })
                if attempt < config.MAX_RETRIES - 1:
                    await asyncio.sleep(config.RETRY_DELAY_BASE ** (attempt + 1))
            except Exception as e:
                errors.append({
                    "id": notification_id,
                    "status": None,
                    "attempt": attempt + 1,
                    "error": f"Unexpected: {str(e)[:200]}",
                    "timestamp": datetime.now().isoformat()
                })
                return None
    
    return None


async def scan_batch(session, ids, semaphore, errors):
    """Scan a batch of IDs concurrently."""
    tasks = [fetch_notification(session, id_, semaphore, errors) for id_ in ids]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]


async def main():
    """Main scanning loop."""
    ensure_dirs()
    
    start_id = load_progress() + 1
    existing = load_existing_results()
    existing_ids = {n["id"] for n in existing}
    
    print(f"=" * 60)
    print(f"CBIC GST Notification Scraper")
    print(f"=" * 60)
    print(f"Scanning IDs: {start_id:,} to {config.ID_END:,}")
    print(f"Concurrency: {config.MAX_CONCURRENT}")
    print(f"Batch delay: {config.BATCH_DELAY_SECONDS}s per {config.BATCH_SIZE} IDs")
    print(f"Existing records: {len(existing):,}")
    print(f"Est. time: ~18-20 minutes")
    print(f"=" * 60)
    
    all_notifications = list(existing)
    all_errors = []
    
    # Create SSL context that doesn't verify (CBIC has cert issues)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(
        limit=config.MAX_CONCURRENT,
        ssl=ssl_context
    )
    
    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT)
    
    headers = {
        "User-Agent": "CBIC-GST-Research-Scraper/1.0 (Educational/Research Purpose)",
        "Accept": "application/json",
    }
    
    async with aiohttp.ClientSession(
        connector=connector,
        headers=headers
    ) as session:
        total_ids = config.ID_END - start_id + 1
        processed = 0
        gst_found = 0
        batch_start_time = time.time()
        
        for batch_start in range(start_id, config.ID_END + 1, config.BATCH_SIZE):
            batch_end = min(batch_start + config.BATCH_SIZE, config.ID_END + 1)
            batch_ids = [id_ for id_ in range(batch_start, batch_end) if id_ not in existing_ids]
            
            if not batch_ids:
                processed += (batch_end - batch_start)
                continue
            
            results = await scan_batch(session, batch_ids, semaphore, all_errors)
            
            # Deduplicate
            for r in results:
                if r["id"] not in existing_ids:
                    all_notifications.append(r)
                    existing_ids.add(r["id"])
                    gst_found += 1
            
            processed += len(batch_ids)
            
            # Progress update every 500 IDs
            if processed % 500 < config.BATCH_SIZE:
                elapsed = time.time() - batch_start_time
                rate = processed / elapsed if elapsed > 0 else 0
                remaining = (total_ids - processed) / rate if rate > 0 else 0
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] "
                      f"ID {batch_start:,}/{config.ID_END:,} | "
                      f"Progress: {processed/total_ids*100:.1f}% | "
                      f"GST found: {gst_found} | "
                      f"Errors: {len(all_errors)} | "
                      f"Rate: {rate:.0f}/s | "
                      f"ETA: {remaining/60:.0f}min")
            
            # Save progress and intermediate results every 1000 IDs
            if processed % 1000 < config.BATCH_SIZE:
                save_progress(batch_end - 1)
                save_results(all_notifications)
                save_errors(all_errors)
            
            # Gentle delay between batches
            await asyncio.sleep(config.BATCH_DELAY_SECONDS)
    
    # Final save
    save_progress(config.ID_END)
    save_results(all_notifications)
    save_errors(all_errors)
    
    # Print summary
    print(f"\n{'=' * 60}")
    print(f"SCAN COMPLETE")
    print(f"{'=' * 60}")
    print(f"Total IDs scanned: {processed:,}")
    print(f"GST notifications found: {len(all_notifications):,}")
    print(f"Errors encountered: {len(all_errors):,}")
    print(f"Results saved to: {config.RAW_METADATA_FILE}")
    print(f"Errors saved to: {config.ERROR_LOG_FILE}")
    
    # Quick breakdown by year
    year_counts = {}
    for n in all_notifications:
        year = n.get("notificationDt", "")[:4]
        if year:
            year_counts[year] = year_counts.get(year, 0) + 1
    
    print(f"\nNotifications by year:")
    for year in sorted(year_counts.keys()):
        print(f"  {year}: {year_counts[year]}")


if __name__ == "__main__":
    asyncio.run(main())
