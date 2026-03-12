"""
Fix metadata.json files to correctly reflect PDF availability.
Run this after reorganization to ensure metadata matches actual files.
"""

import json
import os
from pathlib import Path

def fix_metadata(year, language):
    """Fix metadata files to correctly show PDF availability."""
    base_dir = f"downloads/{language}/{year}"
    
    if not os.path.exists(base_dir):
        print(f"Directory not found: {base_dir}")
        return
    
    fixed = 0
    for root, dirs, files in os.walk(base_dir):
        if 'metadata.json' in files:
            meta_path = os.path.join(root, 'metadata.json')
            
            # Check if PDF exists
            has_pdf = any(f.endswith('.pdf') for f in files)
            
            # Load current metadata
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Update availability
            old_available = metadata.get('available', False)
            metadata['available'] = has_pdf
            
            if has_pdf:
                # Find the PDF filename
                pdf_file = [f for f in files if f.endswith('.pdf')][0]
                
                if language == 'english':
                    metadata['files']['english'] = pdf_file
                    metadata['missing_reason'] = None
                    metadata['notes'] = None
                else:
                    metadata['files']['hindi'] = pdf_file
                    metadata['notes'] = None
            
            # Save updated metadata
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            if old_available != has_pdf:
                fixed += 1
                print(f"Fixed: {meta_path} (available: {has_pdf})")
    
    print(f"\nTotal fixed: {fixed}")

if __name__ == "__main__":
    import sys
    year = sys.argv[1] if len(sys.argv) > 1 else "2025"
    
    print(f"Fixing metadata for year {year}...")
    print("=" * 60)
    
    print("\nEnglish:")
    fix_metadata(year, "english")
    
    print("\nHindi:")
    fix_metadata(year, "hindi")
    
    print("\n" + "=" * 60)
    print("Done!")
