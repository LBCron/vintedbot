#!/usr/bin/env python3
"""
Script to convert all HEIC files to JPEG in temp_photos directory
This fixes the issue where old drafts have HEIC photos that browsers cannot display
"""
import os
from pathlib import Path
from PIL import Image
import pillow_heif

# Register HEIF opener
pillow_heif.register_heif_opener()

def convert_heic_to_jpeg_batch():
    """Convert all HEIC files to JPEG in temp_photos directory"""
    temp_photos_dir = Path("backend/data/temp_photos")
    
    if not temp_photos_dir.exists():
        print(f"❌ Directory not found: {temp_photos_dir}")
        return
    
    heic_files = list(temp_photos_dir.rglob("*.HEIC"))
    heic_files.extend(list(temp_photos_dir.rglob("*.heic")))
    heic_files.extend(list(temp_photos_dir.rglob("*.HEIF")))
    heic_files.extend(list(temp_photos_dir.rglob("*.heif")))
    
    total = len(heic_files)
    print(f"\n🔍 Found {total} HEIC files to convert")
    
    if total == 0:
        print("✅ No HEIC files found - all done!")
        return
    
    converted = 0
    failed = 0
    
    for i, heic_path in enumerate(heic_files, 1):
        try:
            # Open HEIC image
            img = Image.open(heic_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create JPEG filename
            jpeg_path = heic_path.with_suffix('.jpg')
            
            # Skip if JPEG already exists
            if jpeg_path.exists():
                print(f"[{i}/{total}] ⏭️  Skipped (already exists): {jpeg_path.name}")
                continue
            
            # Save as JPEG
            img.save(jpeg_path, 'JPEG', quality=90)
            
            # Delete original HEIC file to save space
            heic_path.unlink()
            
            converted += 1
            if i % 100 == 0:
                print(f"[{i}/{total}] ✅ Converted {converted} files...")
            
        except Exception as e:
            failed += 1
            print(f"[{i}/{total}] ❌ Failed to convert {heic_path.name}: {e}")
    
    print(f"\n🎉 Conversion complete!")
    print(f"   ✅ Converted: {converted}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Total: {total}")

if __name__ == "__main__":
    convert_heic_to_jpeg_batch()
