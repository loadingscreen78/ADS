"""
Test File Upload API
Quick test to verify upload endpoint is working
"""

import requests
from pathlib import Path

def test_upload():
    """Test file upload endpoint"""
    print("\n" + "="*80)
    print("  TESTING FILE UPLOAD API")
    print("="*80 + "\n")
    
    # API endpoint
    url = "http://localhost:8080/api/upload/batch"
    
    # Test file
    test_file = "data/large_scale/original_100K.parquet"
    
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        print("   Run: python generate_datasets_quick.py")
        return
    
    print(f"[1/3] Uploading file: {test_file}")
    print(f"      Size: {Path(test_file).stat().st_size / 1024 / 1024:.2f} MB")
    
    # Upload file
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (Path(test_file).name, f, 'application/octet-stream')}
            data = {'batch_id': 'test_batch_001'}
            
            response = requests.post(url, files=files, data=data, timeout=30)
        
        print(f"\n[2/3] Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n[3/3] Upload Result:")
            print(f"      Success: {result.get('success')}")
            print(f"      Batch ID: {result.get('batch_id')}")
            
            if 'metadata' in result:
                meta = result['metadata']
                print(f"      Rows: {meta.get('n_rows', 0):,}")
                print(f"      Columns: {meta.get('n_columns', 0)}")
                print(f"      Fraud Rate: {meta.get('fraud_rate', 0):.2%}")
            
            print(f"\n✅ File upload working!")
        else:
            print(f"\n❌ Upload failed: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to server at {url}")
        print("   Make sure server is running:")
        print("   python src/services/api_server.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "="*80 + "\n")

def test_list_batches():
    """Test list batches endpoint"""
    print("\n" + "="*80)
    print("  TESTING LIST BATCHES API")
    print("="*80 + "\n")
    
    url = "http://localhost:8080/api/upload/batches"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            batches = result.get('batches', [])
            
            print(f"Total Batches: {result.get('total', 0)}")
            
            if batches:
                print(f"\nUploaded Batches:")
                for batch in batches:
                    print(f"  • {batch.get('batch_id')}")
                    print(f"    Rows: {batch.get('n_rows', 0):,}")
                    print(f"    Fraud Rate: {batch.get('fraud_rate', 0):.2%}")
            else:
                print("\nNo batches uploaded yet.")
            
            print(f"\n✅ List batches working!")
        else:
            print(f"❌ Request failed: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {url}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*80 + "\n")

def test_system_status():
    """Test system status endpoint"""
    print("\n" + "="*80)
    print("  TESTING SYSTEM STATUS API")
    print("="*80 + "\n")
    
    url = "http://localhost:8080/api/status"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"Status: {result.get('status')}")
            print(f"Timestamp: {result.get('timestamp')}")
            
            components = result.get('components', {})
            print(f"\nComponents:")
            for name, status in components.items():
                icon = "✅" if status else "❌"
                print(f"  {icon} {name}: {status}")
            
            metrics = result.get('metrics', {})
            print(f"\nMetrics:")
            print(f"  Accuracy: {metrics.get('accuracy', 0):.1%}")
            print(f"  Drift: {metrics.get('current_drift', '0%')}")
            print(f"  Model Version: {metrics.get('model_version', 'N/A')}")
            print(f"  Processed Batches: {metrics.get('processed_batches', 0)}")
            
            print(f"\n✅ System status working!")
        else:
            print(f"❌ Request failed: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {url}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("  API ENDPOINT TESTING")
    print("  Server: http://localhost:8080")
    print("="*80)
    
    # Test system status first
    test_system_status()
    
    # Test file upload
    test_upload()
    
    # Test list batches
    test_list_batches()
    
    print("\n" + "="*80)
    print("  TESTING COMPLETE")
    print("="*80 + "\n")
