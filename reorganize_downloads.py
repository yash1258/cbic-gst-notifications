"""
Reorganize existing downloads into english/ folder and create metadata.json files.
Part of systematic restructuring for AI agent compatibility.
"""

import json
import os
import shutil
from pathlib import Path

METADATA_DIR = "data/metadata"
DOWNLOAD_DIR = "downloads"


def slugify(text):
    """Convert text to file-friendly slug."""
    return text.replace("/", "-").replace(" ", "-").replace("(", "").replace(")", "")


def get_pdf_info(notification):
    """Generate paths and metadata from notification."""
    year = notification["notificationDt"][:4]
    category = notification.get("notificationCategory", "Unknown").replace(" ", "-")
    
    # Extract notification number for subfolder
    notif_no = notification.get("notificationNo", "")
    number_part = notif_no.split("/")[0] if "/" in notif_no else "unknown"
    
    # Filename without language suffix
    safe_name = slugify(notif_no)
    pdf_filename = f"{safe_name}.pdf"
    
    # Paths
    rel_path = f"{year}/{category}/{number_part}"
    
    return {
        "rel_path": rel_path,
        "pdf_filename": pdf_filename,
        "year": year,
        "category": category,
        "number": number_part,
        "notification": notification
    }


def reorganize_english(year=2025):
    """Move existing English PDFs to english/ folder and create metadata."""
    
    print(f"Reorganizing English PDFs for year {year}...")
    
    # Load metadata for specified year
    with open(f"{METADATA_DIR}/{year}.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        notifications = data.get("notifications", [])
    
    moved = 0
    skipped = 0
    
    for notification in notifications:
        info = get_pdf_info(notification)
        
        # Source: old location
        old_path = f"{DOWNLOAD_DIR}/{info['rel_path']}/{info['pdf_filename'].replace('.pdf', '-eng.pdf')}"
        
        # Destination: new location
        new_dir = f"{DOWNLOAD_DIR}/english/{info['rel_path']}"
        new_path = f"{new_dir}/{info['pdf_filename']}"
        
        # Check if English PDF exists
        has_english = os.path.exists(old_path)
        
        # Check if Hindi exists (has filename in metadata)
        has_hindi = bool(notification.get("docFileNameHi"))
        
        # Create metadata
        metadata = {
            "id": notification["id"],
            "notification_no": notification.get("notificationNo", ""),
            "date": notification.get("notificationDt", ""),
            "category": notification.get("notificationCategory", ""),
            "subject": notification.get("notificationName", ""),
            "language": "english",
            "available": has_english,
            "files": {
                "english": info["pdf_filename"] if has_english else None,
                "hindi": f"{info['pdf_filename'].replace('.pdf', '')}.pdf" if has_hindi else None
            },
            "hindi_id": notification["id"],  # Same ID for both languages
            "missing_reason": None
        }
        
        # If English not available, explain why
        if not has_english:
            if not notification.get("docFileName") and notification.get("docFileNameHi"):
                metadata["missing_reason"] = "hindi_only_corrigendum"
                metadata["notes"] = "This notification was published only in Hindi as a corrigendum (correction). No English version exists in the CBIC system."
            else:
                metadata["missing_reason"] = "not_found"
                metadata["notes"] = "English PDF not found on server (may not exist or server error)."
        
        # Create directory
        os.makedirs(new_dir, exist_ok=True)
        
        # Move file if it exists
        if has_english:
            shutil.move(old_path, new_path)
            moved += 1
        else:
            skipped += 1
        
        # Save metadata
        meta_path = f"{new_dir}/metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"Moved: {moved} PDFs")
    print(f"Missing (metadata only): {skipped}")
    print(f"Created metadata.json in each folder")


def cleanup_old_structure(year=2025):
    """Remove old directory structure after reorganization."""
    old_year_dir = f"{DOWNLOAD_DIR}/{year}"
    if os.path.exists(old_year_dir):
        shutil.rmtree(old_year_dir)
        print(f"Cleaned up old structure: {old_year_dir}")
    
    # Also remove progress/error files from root of downloads
    for fname in [f"progress_{year}.json", f"errors_{year}.json"]:
        fpath = f"{DOWNLOAD_DIR}/{fname}"
        if os.path.exists(fpath):
            os.remove(fpath)
            print(f"Removed: {fname}")


if __name__ == "__main__":
    import sys
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    
    print("=" * 60)
    print(f"Reorganizing Downloads for AI Agent Compatibility ({year})")
    print("=" * 60)
    print()
    
    reorganize_english(year)
    print()
    
    cleanup_old_structure(year)
    print()
    
    print("=" * 60)
    print("Reorganization Complete!")
    print("=" * 60)
    print()
    print("New structure:")
    print(f"  downloads/english/{year}/Central-Tax/01/")
    print(f"    - 01-{year}-Central-Tax.pdf")
    print("    - metadata.json")
    print()
    print("Next: Run download_hindi.py to add Hindi PDFs")
