"""
Upload Data Batches to Dashboard
Simple script to upload the 2 data batch files
"""

import requests
from pathlib import Path

def upload_batch(file_path, batch_id, batch_name):
    """Upload a batch file"""
    print(f"\n{'='*80}")
    print(f"  UPLOADING: {batch_name}")
    print(f"{'='*80}\n")
    
    url = "http://localhost:8080/api/upload/batch"
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    file_size = Path(file_path).stat().st_size / 1024 / 1024
    print(f"📁 File: {Path(file_path).name}")
    print(f"📊 Size: {file_size:.2f} MB")
    print(f"🆔 Batch ID: {batch_id}")
    
    try:
        print(f"\n⏳ Uploading...")
        
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'application/octet-stream')}
            data = {'batch_id': batch_id}
            
            response = requests.post(url, files=files, data=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                print(f"\n✅ Upload Successful!")
                
                meta = result.get('metadata', {})
                print(f"\n📊 Batch Statistics:")
                print(f"   Rows: {meta.get('n_rows', 0):,}")
                print(f"   Columns: {meta.get('n_columns', 0)}")
                print(f"   Fraud Rate: {meta.get('fraud_rate', 0):.2%}")
                print(f"   Has Target: {meta.get('has_target', False)}")
                
                return True
            else:
                print(f"\n❌ Upload failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"\n❌ Server error: {response.status_code}")
            print(f"   {response.text}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to server at {url}")
        print(f"   Make sure server is running:")
        print(f"   python src/services/api_server.py")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def main():
    """Upload both data batches"""
    print("\n" + "="*80)
    print("  DATA BATCH UPLOAD TOOL")
    print("  Upload the 2 data batches to the dashboard")
    print("="*80)
    
    # Check server
    print("\n[1/3] Checking server status...")
    try:
        response = requests.get("http://localhost:8080/api/status", timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is running")
        else:
            print("   ❌ Server returned error")
            return
    except:
        print("   ❌ Server is not running")
        print("   Start server: python src/services/api_server.py")
        return
    
    # Upload original batch
    print("\n[2/3] Uploading ORIGINAL batch...")
    success1 = upload_batch(
        "data/large_scale/original_100K.parquet",
        "original_batch",
        "Original Dataset (Baseline)"
    )
    
    # Upload drifted batch
    print("\n[3/3] Uploading DRIFTED batch...")
    success2 = upload_batch(
        "data/large_scale/drifted_100K.parquet",
        "drifted_batch",
        "Drifted Dataset (With Drift)"
    )
    
    # Summary
    print("\n" + "="*80)
    print("  UPLOAD SUMMARY")
    print("="*80)
    print(f"\n  Original Batch: {'✅ SUCCESS' if success1 else '❌ FAILED'}")
    print(f"  Drifted Batch:  {'✅ SUCCESS' if success2 else '❌ FAILED'}")
    
    if success1 and success2:
        print(f"\n🎉 Both batches uploaded successfully!")
        print(f"\n📊 Next Steps:")
        print(f"   1. View uploaded batches:")
        print(f"      curl http://localhost:8080/api/upload/batches")
        print(f"\n   2. Process a batch for drift detection:")
        print(f"      curl -X POST http://localhost:8080/api/upload/process/original_batch")
        print(f"\n   3. Open dashboard:")
        print(f"      http://localhost:8080")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
