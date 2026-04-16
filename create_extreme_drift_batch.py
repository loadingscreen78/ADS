"""
Create EXTREME Drift Batch
This will DEFINITELY trigger RETRAIN_FULL for demo
"""

import numpy as np
import pandas as pd
from pathlib import Path

def create_extreme_drift_batch():
    """Create batch with EXTREME drift to trigger retraining"""
    print("\n" + "="*80)
    print("  CREATING EXTREME DRIFT BATCH")
    print("  This will trigger RETRAIN_FULL!")
    print("="*80)
    
    N_SAMPLES = 50_000  # Smaller for faster upload
    np.random.seed(999)
    
    print(f"\n[1/3] Generating {N_SAMPLES:,} rows with EXTREME drift...")
    
    # EXTREME drift - completely different distribution
    data = {
        # MUCH higher amounts (3x baseline)
        'amount': np.random.lognormal(5.5, 2.0, N_SAMPLES),  # Mean ~$800 vs $168
        
        # Different merchant distribution
        'merchant_category': np.random.choice([3, 4], N_SAMPLES, p=[0.7, 0.3]),  # Mostly high-risk
        
        # Much higher transaction frequency
        'transaction_count_7d': np.random.poisson(15, N_SAMPLES),  # 15 vs 5
        
        # Different card types
        'card_type': np.random.choice([2, 3], N_SAMPLES, p=[0.6, 0.4]),  # Premium/Business
        
        # Much newer cards
        'card_age_days': np.random.exponential(200, N_SAMPLES),  # 200 vs 730
        
        # Higher limits
        'card_limit': np.random.choice([10000, 25000], N_SAMPLES, p=[0.4, 0.6]),
        
        # Younger users
        'user_age': np.random.normal(32, 12, N_SAMPLES).clip(18, 90),  # 32 vs 40
        
        # Higher income
        'income_bracket': np.random.choice([2, 3], N_SAMPLES, p=[0.5, 0.5]),  # High/Very High
        
        # Newer accounts
        'account_age_days': np.random.exponential(400, N_SAMPLES),  # 400 vs 1095
        
        # Different time patterns (late night)
        'hour_of_day': np.random.choice(list(range(0, 6)) + list(range(22, 24)), N_SAMPLES),
        
        # Weekend heavy
        'day_of_week': np.random.choice([5, 6], N_SAMPLES, p=[0.5, 0.5]),  # Sat/Sun
        
        # Specific months
        'month': np.random.choice([11, 12], N_SAMPLES, p=[0.5, 0.5]),  # Nov/Dec
        
        # MUCH more international
        'is_international': np.random.choice([0, 1], N_SAMPLES, p=[0.65, 0.35]),  # 35% vs 5%
        
        # Much further from home
        'distance_from_home': np.random.exponential(50, N_SAMPLES),  # 50 vs 10
    }
    
    # MUCH higher fraud probability
    fraud_prob = 0.15 + \
                 (data['amount'] > np.percentile(data['amount'], 80)) * 0.08 + \
                 data['is_international'] * 0.05 + \
                 (data['hour_of_day'] < 6) * 0.04
    
    data['is_fraud'] = (np.random.random(N_SAMPLES) < fraud_prob).astype(int)
    
    df = pd.DataFrame(data)
    
    print(f"  ✓ Generated {len(df):,} rows")
    print(f"  ✓ Fraud rate: {df['is_fraud'].mean():.2%} (EXTREME!)")
    print(f"  ✓ Mean amount: ${df['amount'].mean():.2f} (vs $168 baseline)")
    print(f"  ✓ International: {df['is_international'].mean():.2%} (vs 5% baseline)")
    
    # Save files
    output_dir = Path('extreme_drift')
    output_dir.mkdir(exist_ok=True)
    
    # Parquet
    parquet_file = output_dir / 'extreme_drift_50K.parquet'
    print(f"\n[2/3] Saving Parquet file...")
    df.to_parquet(parquet_file, compression='snappy', index=False)
    parquet_size = parquet_file.stat().st_size / 1024 / 1024
    print(f"  ✓ Saved: {parquet_size:.2f} MB")
    
    # Excel for judges
    excel_file = output_dir / 'extreme_drift_50K.xlsx'
    print(f"\n[3/3] Creating Excel file for judges...")
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Data sample
        df.head(1000).to_excel(writer, sheet_name='Data Sample', index=False)
        
        # Summary
        summary_data = {
            'Metric': [
                'Total Rows',
                'Fraud Rate',
                'Mean Amount',
                'Median Amount',
                'International Rate',
                'Avg Transaction Count',
                'Late Night Transactions',
                'Weekend Transactions',
            ],
            'Value': [
                f"{len(df):,}",
                f"{df['is_fraud'].mean():.2%}",
                f"${df['amount'].mean():.2f}",
                f"${df['amount'].median():.2f}",
                f"{df['is_international'].mean():.2%}",
                f"{df['transaction_count_7d'].mean():.1f}",
                f"{(df['hour_of_day'] < 6).mean():.2%}",
                f"{(df['day_of_week'] >= 5).mean():.2%}",
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Drift comparison
        drift_data = {
            'Feature': [
                'Mean Amount',
                'Fraud Rate',
                'International',
                'Transaction Count',
                'Card Age',
                'User Age',
            ],
            'Baseline': [
                '$168',
                '6.0%',
                '5.0%',
                '5.0',
                '730 days',
                '40 years',
            ],
            'This Batch': [
                f"${df['amount'].mean():.0f}",
                f"{df['is_fraud'].mean():.1%}",
                f"{df['is_international'].mean():.1%}",
                f"{df['transaction_count_7d'].mean():.1f}",
                f"{df['card_age_days'].mean():.0f} days",
                f"{df['user_age'].mean():.0f} years",
            ],
            'Change': [
                f"+{((df['amount'].mean() / 168 - 1) * 100):.0f}%",
                f"+{((df['is_fraud'].mean() / 0.06 - 1) * 100):.0f}%",
                f"+{((df['is_international'].mean() / 0.05 - 1) * 100):.0f}%",
                f"+{((df['transaction_count_7d'].mean() / 5 - 1) * 100):.0f}%",
                f"-{((1 - df['card_age_days'].mean() / 730) * 100):.0f}%",
                f"-{((1 - df['user_age'].mean() / 40) * 100):.0f}%",
            ]
        }
        drift_df = pd.DataFrame(drift_data)
        drift_df.to_excel(writer, sheet_name='Drift Comparison', index=False)
    
    excel_size = excel_file.stat().st_size / 1024 / 1024
    print(f"  ✓ Saved: {excel_size:.2f} MB")
    
    # Summary
    print("\n" + "="*80)
    print("  EXTREME DRIFT BATCH CREATED!")
    print("="*80)
    
    print(f"\n📁 Files Created:")
    print(f"   1. {parquet_file}")
    print(f"      Size: {parquet_size:.2f} MB")
    print(f"      For: Upload to dashboard")
    
    print(f"\n   2. {excel_file}")
    print(f"      Size: {excel_size:.2f} MB")
    print(f"      For: Show to judges")
    
    print(f"\n📊 Extreme Drift Characteristics:")
    print(f"   Fraud Rate: {df['is_fraud'].mean():.2%} (vs 6% baseline) = +{((df['is_fraud'].mean() / 0.06 - 1) * 100):.0f}%")
    print(f"   Mean Amount: ${df['amount'].mean():.2f} (vs $168) = +{((df['amount'].mean() / 168 - 1) * 100):.0f}%")
    print(f"   International: {df['is_international'].mean():.2%} (vs 5%) = +{((df['is_international'].mean() / 0.05 - 1) * 100):.0f}%")
    print(f"   Transaction Count: {df['transaction_count_7d'].mean():.1f} (vs 5) = +{((df['transaction_count_7d'].mean() / 5 - 1) * 100):.0f}%")
    
    print(f"\n🎯 Expected Results:")
    print(f"   Drift Ratio: 70-90% (EXTREME)")
    print(f"   Severity: SIGNIFICANT")
    print(f"   CARA Score: > 0.7")
    print(f"   CARA Decision: RETRAIN_FULL ✅")
    print(f"   Auto-Retrain: YES ✅")
    
    print(f"\n📤 How to Upload:")
    print(f"   1. Open: http://localhost:8080")
    print(f"   2. Click: 📁 Upload Custom File")
    print(f"   3. Select: {parquet_file.name}")
    print(f"   4. Batch ID: extreme_drift_001")
    print(f"   5. Watch: RETRAIN_FULL triggered!")
    
    print(f"\n✅ This batch will DEFINITELY trigger retraining!")
    print("="*80 + "\n")

if __name__ == "__main__":
    create_extreme_drift_batch()
