"""
Populate Drift History
Uploads both batches multiple times to create drift history
"""

import requests
import time

API_URL = "http://localhost:8080"

def upload_batch(batch_type, batch_name):
    """Upload a batch"""
    print(f"\n{'='*60}")
    print(f"  Uploading {batch_name}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            f"{API_URL}/api/upload/quick/{batch_type}",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Success!")
                print(f"   Rows: {data['metadata']['n_rows']:,}")
                print(f"   Fraud: {data['metadata']['fraud_rate']:.2%}")
                print(f"   Drift: {data['drift_score']['overall_severity']} ({data['drift_score']['drift_ratio']:.1%})")
                print(f"   CARA: {data['cara_decision']['decision']}")
                return True
            else:
                print(f"❌ Failed: {data.get('error')}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Populate drift history with multiple uploads"""
    print("\n" + "="*60)
    print("  POPULATING DRIFT HISTORY")
    print("  Creating drift timeline for dashboard")
    print("="*60)
    
    # Upload sequence to show drift progression
    sequence = [
        ("original", "Original Batch (Baseline)"),
        ("original", "Original Batch (Week 2)"),
        ("drifted", "Drifted Batch (Week 3 - Drift Starts)"),
        ("original", "Original Batch (Week 4)"),
        ("drifted", "Drifted Batch (Week 5 - Drift Continues)"),
        ("drifted", "Drifted Batch (Week 6 - High Drift)"),
        ("original", "Original Batch (Week 7 - Back to Normal)"),
        ("drifted", "Drifted Batch (Week 8 - Drift Returns)"),
    ]
    
    success_count = 0
    
    for i, (batch_type, batch_name) in enumerate(sequence, 1):
        print(f"\n[{i}/{len(sequence)}] Processing...")
        
        if upload_batch(batch_type, batch_name):
            success_count += 1
        
        # Wait between uploads
        if i < len(sequence):
            print(f"\n⏳ Waiting 2 seconds...")
            time.sleep(2)
    
    # Summary
    print("\n" + "="*60)
    print("  DRIFT HISTORY POPULATED")
    print("="*60)
    print(f"\nUploaded: {success_count}/{len(sequence)} batches")
    print(f"\n📊 Now check the dashboard:")
    print(f"   1. Open: http://localhost:8080")
    print(f"   2. Go to: Drift Detection tab")
    print(f"   3. See: Drift History graph with {success_count} data points")
    print(f"\n✅ Drift timeline created!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
