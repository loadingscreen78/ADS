"""
IEEE Fraud Detection Dataset Setup Script
Helps download and prepare the dataset for the project
"""

import os
import sys
from pathlib import Path
import subprocess

print("=" * 70)
print("IEEE FRAUD DETECTION DATASET SETUP")
print("=" * 70)
print()

# Check if Kaggle is installed
try:
    import kaggle
    print("[OK] Kaggle CLI is installed")
except ImportError:
    print("[ERROR] Kaggle CLI not found")
    print("\nInstalling Kaggle CLI...")
    subprocess.run([sys.executable, "-m", "pip", "install", "kaggle"])
    print("[OK] Kaggle CLI installed")

# Check for Kaggle credentials
kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
if not kaggle_json.exists():
    print("\n" + "=" * 70)
    print("KAGGLE API CREDENTIALS REQUIRED")
    print("=" * 70)
    print("""
To download the IEEE fraud dataset, you need Kaggle API credentials:

1. Go to: https://www.kaggle.com/account
2. Scroll to "API" section
3. Click "Create New API Token"
4. This downloads kaggle.json
5. Move it to: ~/.kaggle/kaggle.json (Linux/Mac) or C:\\Users\\<username>\\.kaggle\\kaggle.json (Windows)
6. On Linux/Mac, run: chmod 600 ~/.kaggle/kaggle.json

After setting up credentials, run this script again.
""")
    sys.exit(1)

print("[OK] Kaggle credentials found")

# Create data directory
data_dir = Path("data/ieee_fraud")
data_dir.mkdir(parents=True, exist_ok=True)
print(f"[OK] Data directory: {data_dir}")

# Check if dataset already exists
required_files = [
    data_dir / "train_transaction.csv",
    data_dir / "train_identity.csv"
]

if all(f.exists() for f in required_files):
    print("\n[INFO] Dataset already downloaded!")
    print("Files found:")
    for f in required_files:
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  - {f.name} ({size_mb:.1f} MB)")
    
    response = input("\nRe-download dataset? (y/N): ")
    if response.lower() != 'y':
        print("\nSkipping download. Proceeding to data preparation...")
        prepare_data = True
    else:
        prepare_data = False
else:
    prepare_data = False

if not prepare_data:
    print("\n" + "=" * 70)
    print("DOWNLOADING DATASET")
    print("=" * 70)
    print("""
This will download the IEEE-CIS Fraud Detection dataset from Kaggle.
Dataset size: ~500 MB compressed, ~2 GB uncompressed
This may take several minutes depending on your internet speed.
""")
    
    response = input("Continue? (Y/n): ")
    if response.lower() == 'n':
        print("Download cancelled.")
        sys.exit(0)
    
    print("\nDownloading...")
    try:
        # Download using Kaggle API
        os.chdir(data_dir)
        subprocess.run([
            "kaggle", "competitions", "download",
            "-c", "ieee-fraud-detection"
        ], check=True)
        
        print("\n[OK] Download complete")
        
        # Unzip files
        print("\nExtracting files...")
        import zipfile
        
        zip_file = data_dir / "ieee-fraud-detection.zip"
        if zip_file.exists():
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(data_dir)
            print("[OK] Extraction complete")
            
            # Clean up zip file
            zip_file.unlink()
            print("[OK] Cleaned up zip file")
        else:
            print("[WARN] Zip file not found, files may already be extracted")
        
        os.chdir(Path(__file__).parent)
        
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Download failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your Kaggle credentials")
        print("2. Accept competition rules at: https://www.kaggle.com/c/ieee-fraud-detection/rules")
        print("3. Try manual download from: https://www.kaggle.com/c/ieee-fraud-detection/data")
        sys.exit(1)

# Prepare data for the project
print("\n" + "=" * 70)
print("PREPARING DATA FOR PROJECT")
print("=" * 70)

try:
    from src.utils.ieee_fraud_loader import IEEEFraudLoader
    
    print("\nLoading and preparing dataset...")
    loader = IEEEFraudLoader()
    
    # Load dataset (sample for memory efficiency)
    df = loader.load_and_prepare(sample_size=200000)
    
    # Create weekly windows
    windows = loader.create_time_windows(df, n_windows=10)
    
    # Save windows
    loader.save_windows(windows)
    
    print("\n[OK] Data preparation complete!")
    print("\nGenerated files:")
    print("  - data/reference/ieee_reference.parquet (reference distribution)")
    print("  - data/ieee_windows/week_01.parquet to week_10.parquet")
    
    print("\n" + "=" * 70)
    print("SETUP COMPLETE")
    print("=" * 70)
    print("""
The IEEE fraud dataset is ready for use!

Next steps:
1. Run the complete workflow:
   python run_day1_to_day6.py

2. Or test with IEEE data specifically:
   python src/drift/drift_engine.py

The system will now use real-world fraud data with natural drift patterns.
""")

except Exception as e:
    print(f"\n[ERROR] Data preparation failed: {e}")
    print("\nThe dataset was downloaded but preparation failed.")
    print("You can still use the synthetic data by running:")
    print("  python run_day1_to_day6.py")
    sys.exit(1)
