import os
import glob
import shutil
from pathlib import Path

def rename_photos_faces(folder_path):
    """
    Rename ALL images to face_1.png, face_2.png... PERFECTLY ordered from 1 to N
    ROBUST: Handles missing files and conflicts
    """
    # Step 1: Collect ALL current image files that ACTUALLY EXIST
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.gif']
    all_image_files = []
    
    print("Scanning folder...")
    for ext in image_extensions:
        files = glob.glob(os.path.join(folder_path, ext))
        files.extend(glob.glob(os.path.join(folder_path, ext.upper())))
        for f in files:
            if os.path.exists(f):  # Only files that exist
                all_image_files.append(f)
    
    if not all_image_files:
        print("❌ No images found in the folder!")
        return
    
    # Remove duplicates and sort
    all_image_files = sorted(list(set(all_image_files)))
    print(f"Found {len(all_image_files)} existing images")
    
    # Step 2: Create temp folder
    temp_dir = os.path.join(folder_path, "__temp_rename__")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    try:
        # Step 3: Move ALL existing images to temp (skip if already moved)
        print("Moving files to temp...")
        moved_files = []
        for i, old_path in enumerate(all_image_files, 1):
            if not os.path.exists(old_path):  # Skip if already moved
                continue
                
            temp_path = os.path.join(temp_dir, f"temp_{i:03d}.tmp")
            try:
                shutil.move(old_path, temp_path)
                moved_files.append(temp_path)
                print(f"Moved: {os.path.basename(old_path)} → temp_{i:03d}.tmp")
            except Exception as e:
                print(f"Skip {os.path.basename(old_path)}: {e}")
        
        # Step 4: Rename from temp back to face_1.png, face_2.png...
        print("Renaming to face_X.png...")
        for i, temp_path in enumerate(moved_files, 1):
            if os.path.exists(temp_path):
                new_path = os.path.join(folder_path, f"face_{i}.png")
                shutil.move(temp_path, new_path)
                print(f"Renamed → face_{i}.png")
        
        print(f"\n✅ SUCCESS! {len(moved_files)} files ordered: face_1.png → face_{len(moved_files)}.png")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
    finally:
        # Cleanup temp folder
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                print("Warning: Could not delete temp folder")

def main():
    print("=== Face Renamer (Perfect Sequential Order - ROBUST) ===")
    folder = input("Enter folder path: ").strip().strip('"')
    
    if not os.path.exists(folder):
        print("❌ Folder not found!")
        return
    
    print(f"Folder: {folder}")
    confirm = input("⚠️  This will RENUMBER ALL images from face_1.png to face_N.png\nContinue? (y/n): ").lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    rename_photos_faces(folder)

if __name__ == "__main__":
    main()
