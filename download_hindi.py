"""
Download Hindi PDFs for all notifications.
Creates parallel structure in hindi/ folder with metadata.
"""

import asyncio
import base64
import json
import os
import ssl
import time
from datetime import datetime

import aiohttp

BASE_URL = "https://taxinformation.cbic.gov.in"
DOWNLOAD_ENDPOINT = "/api/cbic-notification-msts/download/{id}/HINDI"
METADATA_DIR = "data/metadata"
DOWNLOAD_DIR = "downloads"

MAX_CONCURRENT = 5
BATCH_SIZE = 20
BATCH_DELAY_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 60
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def slugify(text):
    return text.replace("/", "-").replace(" ", "-").replace("(", "").replace(")", "")


def get_hindi_path(notification):
    """Generate Hindi PDF path."""
    year = notification["notificationDt"][:4]
    category = notification.get("notificationCategory", "Unknown").replace(" ", "-")
    
    notif_no = notification.get("notificationNo", "")
    number_part = notif_no.split("/")[0] if "/" in notif_no else "unknown"
    
    safe_name = slugify(notif_no)
    pdf_filename = f"{safe_name}.pdf"
    
    hindi_dir = f"{DOWNLOAD_DIR}/hindi/{year}/{category}/{number_part}"
    
    return hindi_dir, pdf_filename


def load_metadata(year):
    with open(f"{METADATA_DIR}/{year}.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("notifications", [])


def load_progress(year):
    progress_file = f"{DOWNLOAD_DIR}/hindi_progress_{year}.json"
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            return set(json.load(f).get("downloaded_ids", []))
    return set()


def save_progress(year, downloaded_ids):
    progress_file = f"{DOWNLOAD_DIR}/hindi_progress_{year}.json"
    with open(progress_file, "w") as f:
        json.dump({
            "year": year,
            "downloaded_ids": list(downloaded_ids),
            "updated_at": datetime.now().isoformat()
        }, f)


def create_hindi_metadata(notification, hindi_dir, pdf_filename, available):
    """Create metadata.json for Hindi folder."""
    metadata = {
        "id": notification["id"],
        "notification_no": notification.get("notificationNo", ""),
        "date": notification.get("notificationDt", ""),
        "category": notification.get("notificationCategory", ""),
        "subject": notification.get("notificationName", ""),
        "language": "hindi",
        "available": available,
        "files": {
            "hindi": pdf_filename if available else None
        },
        "english_id": notification["id"],
        "notes": "Hindi version of notification" if available else "Hindi PDF not available"
    }
    
    meta_path = f"{hindi_dir}/metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


async def download_hindi_pdf(session, notification, semaphore, downloaded_ids, errors_list):
    """Download Hindi PDF."""
    notification_id = notification["id"]
    
    # Check if already downloaded
    if notification_id in downloaded_ids:
        return None, "already_downloaded"
    
    # Check if Hindi exists in metadata
    if not notification.get("docFileNameHi"):
        return None, "no_hindi_metadata"
    
    url = f"{BASE_URL}{DOWNLOAD_ENDPOINT.format(id=notification_id)}"
    hindi_dir, pdf_filename = get_hindi_path(notification)
    pdf_path = f"{hindi_dir}/{pdf_filename}"
    
    os.makedirs(hindi_dir, exist_ok=True)
    
    async with semaphore:
        for attempt in range(MAX_RETRIES):
            try:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS),
                    ssl=ssl_context
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "data" not in data:
                            create_hindi_metadata(notification, hindi_dir, pdf_filename, False)
                            return None, "no_data_field"
                        
                        # Decode and save
                        pdf_bytes = base64.b64decode(data["data"])
                        
                        with open(pdf_path, "wb") as f:
                            f.write(pdf_bytes)
                        
                        # Create metadata
                        create_hindi_metadata(notification, hindi_dir, pdf_filename, True)
                        
                        return pdf_path, "success"
                    
                    elif response.status == 500:
                        if attempt == MAX_RETRIES - 1:
                            create_hindi_metadata(notification, hindi_dir, pdf_filename, False)
                            return None, "server_error_500"
                        await asyncio.sleep(RETRY_DELAY_BASE ** (attempt + 1))
                        continue
                    
                    else:
                        create_hindi_metadata(notification, hindi_dir, pdf_filename, False)
                        return None, f"http_{response.status}"
                        
            except asyncio.TimeoutError:
                if attempt == MAX_RETRIES - 1:
                    create_hindi_metadata(notification, hindi_dir, pdf_filename, False)
                    return None, "timeout"
                await asyncio.sleep(RETRY_DELAY_BASE ** (attempt + 1))
                
            except Exception as e:
                create_hindi_metadata(notification, hindi_dir, pdf_filename, False)
                return None, str(e)[:200]
    
    return None, "max_retries"


async def download_batch(session, notifications, semaphore, downloaded_ids, errors_list):
    tasks = [
        download_hindi_pdf(session, n, semaphore, downloaded_ids, errors_list)
        for n in notifications
    ]
    results = await asyncio.gather(*tasks)
    return results


async def main(year=2025):
    print("=" * 60)
    print(f"Downloading Hindi PDFs for {year}")
    print("=" * 60)
    print()
    
    notifications = load_metadata(year)
    total = len(notifications)
    
    # Count those with Hindi
    with_hindi = sum(1 for n in notifications if n.get("docFileNameHi"))
    
    downloaded_ids = load_progress(year)
    already_done = len(downloaded_ids)
    
    print(f"Total notifications: {total}")
    print(f"With Hindi version: {with_hindi}")
    print(f"Already downloaded: {already_done}")
    print(f"Remaining: {with_hindi - already_done}")
    print()
    
    pending = [n for n in notifications if n.get("docFileNameHi") and n["id"] not in downloaded_ids]
    
    if not pending:
        print("All Hindi PDFs already processed!")
        return
    
    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT, ssl=ssl_context)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    headers = {
        "User-Agent": "CBIC-GST-Research-Scraper/1.0",
        "Accept": "application/json",
    }
    
    successful = 0
    failed = 0
    skipped = 0
    start_time = time.time()
    
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        for i in range(0, len(pending), BATCH_SIZE):
            batch = pending[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (len(pending) + BATCH_SIZE - 1) // BATCH_SIZE
            
            results = await download_batch(session, batch, semaphore, downloaded_ids, [])
            
            for (pdf_path, status), notification in zip(results, batch):
                if status == "success":
                    successful += 1
                    downloaded_ids.add(notification["id"])
                elif status == "already_downloaded":
                    skipped += 1
                else:
                    failed += 1
            
            processed = min(i + BATCH_SIZE, len(pending))
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            remaining = (len(pending) - processed) / rate if rate > 0 else 0
            
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] "
                  f"Batch {batch_num}/{total_batches} | "
                  f"Progress: {processed}/{len(pending)} ({processed/len(pending)*100:.1f}%) | "
                  f"OK: {successful} | Fail: {failed} | "
                  f"ETA: {remaining/60:.0f}min")
            
            save_progress(year, downloaded_ids)
            
            if i + BATCH_SIZE < len(pending):
                await asyncio.sleep(BATCH_DELAY_SECONDS)
    
    elapsed = time.time() - start_time
    print()
    print("=" * 60)
    print("HINDI DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"Downloaded: {successful}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print(f"Time: {elapsed/60:.1f} minutes")
    print(f"Location: {DOWNLOAD_DIR}/hindi/{year}/")


if __name__ == "__main__":
    import sys
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    asyncio.run(main(year))
