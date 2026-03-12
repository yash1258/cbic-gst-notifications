"""
CBIC GST Notification PDF Downloader
Downloads English PDFs for specified year(s).
Phase 2 of the CBIC scraping pipeline.
"""

import asyncio
import base64
import json
import os
import ssl
import time
from datetime import datetime
from pathlib import Path

import aiohttp

# Configuration
BASE_URL = "https://taxinformation.cbic.gov.in"
DOWNLOAD_ENDPOINT = "/api/cbic-notification-msts/download/{id}/ENG"
METADATA_DIR = "data/metadata"
DOWNLOAD_DIR = "downloads"

# Rate limiting - gentle settings
MAX_CONCURRENT = 5
BATCH_SIZE = 20
BATCH_DELAY_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 60  # PDFs take longer
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2

# SSL context for CBIC's self-signed cert
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def slugify(text):
    """Convert text to URL/file-friendly slug."""
    return text.replace("/", "-").replace(" ", "-").replace("(", "").replace(")", "")


def ensure_dirs():
    """Create download directory structure."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def load_metadata(year):
    """Load metadata for specific year."""
    filepath = os.path.join(METADATA_DIR, f"{year}.json")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Metadata file not found: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("notifications", [])


def get_pdf_path(notification):
    """Generate PDF path based on notification metadata."""
    year = notification["notificationDt"][:4]
    category = notification.get("notificationCategory", "Unknown").replace(" ", "-")
    
    # Extract notification number for subfolder
    notif_no = notification.get("notificationNo", "")
    # Parse "01/2025-Central Tax" -> "01"
    number_part = notif_no.split("/")[0] if "/" in notif_no else "unknown"
    
    # Create path: downloads/2025/Central-Tax/01/
    pdf_dir = os.path.join(DOWNLOAD_DIR, year, category, number_part)
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Filename: 01-2025-Central-Tax-eng.pdf
    safe_name = slugify(notif_no)
    pdf_filename = f"{safe_name}-eng.pdf"
    
    return os.path.join(pdf_dir, pdf_filename)


def load_progress(year):
    """Load download progress for resumability."""
    progress_file = os.path.join(DOWNLOAD_DIR, f"progress_{year}.json")
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            return set(json.load(f).get("downloaded_ids", []))
    return set()


def save_progress(year, downloaded_ids):
    """Save download progress."""
    progress_file = os.path.join(DOWNLOAD_DIR, f"progress_{year}.json")
    with open(progress_file, "w") as f:
        json.dump({
            "year": year,
            "downloaded_ids": list(downloaded_ids),
            "updated_at": datetime.now().isoformat()
        }, f)


def save_error(year, notification_id, error_msg):
    """Log download errors."""
    error_file = os.path.join(DOWNLOAD_DIR, f"errors_{year}.json")
    errors = []
    
    if os.path.exists(error_file):
        with open(error_file, "r") as f:
            errors = json.load(f)
    
    errors.append({
        "id": notification_id,
        "error": error_msg,
        "timestamp": datetime.now().isoformat()
    })
    
    with open(error_file, "w") as f:
        json.dump(errors, f, indent=2)


async def download_pdf(session, notification, semaphore, downloaded_ids, errors_list):
    """Download a single PDF with retry logic."""
    notification_id = notification["id"]
    
    # Skip if already downloaded
    if notification_id in downloaded_ids:
        return None, "already_downloaded"
    
    url = f"{BASE_URL}{DOWNLOAD_ENDPOINT.format(id=notification_id)}"
    pdf_path = get_pdf_path(notification)
    
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
                            error_msg = "No 'data' field in response"
                            errors_list.append({"id": notification_id, "error": error_msg})
                            save_error(datetime.now().year, notification_id, error_msg)
                            return None, error_msg
                        
                        # Decode base64 and save
                        pdf_bytes = base64.b64decode(data["data"])
                        
                        with open(pdf_path, "wb") as f:
                            f.write(pdf_bytes)
                        
                        return pdf_path, "success"
                    
                    elif response.status == 500:
                        error_msg = f"Server error (500) - PDF may not exist"
                        if attempt == MAX_RETRIES - 1:
                            errors_list.append({"id": notification_id, "error": error_msg})
                            save_error(datetime.now().year, notification_id, error_msg)
                        await asyncio.sleep(RETRY_DELAY_BASE ** (attempt + 1))
                        continue
                    
                    else:
                        error_msg = f"HTTP {response.status}"
                        errors_list.append({"id": notification_id, "error": error_msg})
                        save_error(datetime.now().year, notification_id, error_msg)
                        return None, error_msg
                        
            except asyncio.TimeoutError:
                error_msg = "Timeout"
                if attempt == MAX_RETRIES - 1:
                    errors_list.append({"id": notification_id, "error": error_msg})
                    save_error(datetime.now().year, notification_id, error_msg)
                await asyncio.sleep(RETRY_DELAY_BASE ** (attempt + 1))
                
            except Exception as e:
                error_msg = str(e)[:200]
                errors_list.append({"id": notification_id, "error": error_msg})
                save_error(datetime.now().year, notification_id, error_msg)
                return None, error_msg
    
    return None, "max_retries_exceeded"


async def download_batch(session, notifications, semaphore, downloaded_ids, errors_list):
    """Download a batch of PDFs concurrently."""
    tasks = [
        download_pdf(session, n, semaphore, downloaded_ids, errors_list)
        for n in notifications
    ]
    results = await asyncio.gather(*tasks)
    return results


async def main(year=2025):
    """Main download loop for specified year."""
    ensure_dirs()
    
    # Load metadata
    print(f"Loading metadata for year {year}...")
    notifications = load_metadata(year)
    total = len(notifications)
    print(f"Found {total} notifications")
    
    # Load progress
    downloaded_ids = load_progress(year)
    already_downloaded = len(downloaded_ids)
    print(f"Already downloaded: {already_downloaded}")
    print(f"Remaining: {total - already_downloaded}")
    print()
    
    # Filter out already downloaded
    pending = [n for n in notifications if n["id"] not in downloaded_ids]
    
    if not pending:
        print("All PDFs already downloaded!")
        return
    
    # Setup
    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT, ssl=ssl_context)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    headers = {
        "User-Agent": "CBIC-GST-Research-Scraper/1.0 (Educational/Research Purpose)",
        "Accept": "application/json",
    }
    
    errors_list = []
    successful = 0
    failed = 0
    skipped = 0
    
    print("=" * 60)
    print(f"Downloading {year} PDFs")
    print("=" * 60)
    print(f"Total: {len(pending)} | Concurrent: {MAX_CONCURRENT} | Batch delay: {BATCH_DELAY_SECONDS}s")
    print()
    
    start_time = time.time()
    
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        for i in range(0, len(pending), BATCH_SIZE):
            batch = pending[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (len(pending) + BATCH_SIZE - 1) // BATCH_SIZE
            
            results = await download_batch(session, batch, semaphore, downloaded_ids, errors_list)
            
            # Process results
            for (pdf_path, status), notification in zip(results, batch):
                if status == "success":
                    successful += 1
                    downloaded_ids.add(notification["id"])
                elif status == "already_downloaded":
                    skipped += 1
                else:
                    failed += 1
            
            # Progress update
            processed = min(i + BATCH_SIZE, len(pending))
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            remaining = (len(pending) - processed) / rate if rate > 0 else 0
            
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] "
                  f"Batch {batch_num}/{total_batches} | "
                  f"Progress: {processed}/{len(pending)} ({processed/len(pending)*100:.1f}%) | "
                  f"OK: {successful} | Fail: {failed} | "
                  f"Rate: {rate:.1f}/s | ETA: {remaining/60:.0f}min")
            
            # Save progress
            save_progress(year, downloaded_ids)
            
            # Gentle delay between batches
            if i + BATCH_SIZE < len(pending):
                await asyncio.sleep(BATCH_DELAY_SECONDS)
    
    # Final summary
    elapsed = time.time() - start_time
    print()
    print("=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"Year: {year}")
    print(f"Total notifications: {total}")
    print(f"Downloaded: {successful}")
    print(f"Failed: {failed}")
    print(f"Skipped (already had): {skipped}")
    print(f"Time: {elapsed/60:.1f} minutes")
    print(f"Download location: {DOWNLOAD_DIR}/{year}/")
    
    if errors_list:
        print(f"\nErrors logged to: {DOWNLOAD_DIR}/errors_{year}.json")


if __name__ == "__main__":
    import sys
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    asyncio.run(main(year))
