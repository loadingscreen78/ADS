"""
Quick Dataset Generator - 100K rows for testing
Then can scale to millions
"""

import numpy as np
import pandas as pd
from pathlib import Path

def generate_quick_datasets():
    """Generate 100K row datasets quickly"""
    print("="*80)
    print("  QUICK DATASET GENERATION (100K rows)")
    print("="*80)
    
    N_SAMPLES = 100_000
    np.random.seed(42)
    
    # ORIGINAL DATASET
    print("\n[1/2] Generating ORIGINAL dataset...")
    data_orig = {
        'amount': np.random.lognormal(4.0, 1.5, N_SAMPLES),
        'merchant_category': np.random.choice([0, 1, 2, 3, 4], N_SAMPLES),
        'transaction_count_7d': np.random.poisson(5, N_SAMPLES),
        'card_type': np.random.choice([0, 1, 2, 3], N_SAMPLES),
        'card_age_days': np.random.exponential(730, N_SAMPLES),
        'card_limit': np.random.choice([1000, 2500, 5000, 10000, 25000], N_SAMPLES),
        'user_age': np.random.normal(40, 15, N_SAMPLES).clip(18, 90),
        'income_bracket': np.random.choice([0, 1, 2, 3], N_SAMPLES),
        'account_age_days': np.random.exponential(1095, N_SAMPLES),
        'hour_of_day': np.random.randint(0, 24, N_SAMPLES),
        'day_of_week': np.random.randint(0, 7, N_SAMPLES),
        'month': np.random.randint(1, 13, N_SAMPLES),
        'is_international': np.random.choice([0, 1], N_SAMPLES, p=[0.95, 0.05]),
        'distance_from_home': np.random.exponential(10, N_SAMPLES),
    }
    
    # Calculate fraud probability
    fraud_prob = 0.05 + \
                 (data_orig['amount'] > np.percentile(data_orig['amount'], 90)) * 0.03 + \
                 data_orig['is_international'] * 0.02 + \
                 (data_orig['hour_of_day'] < 6) * 0.02
    
    data_orig['is_fraud'] = (np.random.random(N_SAMPLES) < fraud_prob).astype(int)
    
    df_orig = pd.DataFrame(data_orig)
    print(f"  ✓ {len(df_orig):,} rows, {df_orig['is_fraud'].mean():.2%} fraud rate")
    
    # DRIFTED DATASET
    print("\n[2/2] Generating DRIFTED dataset...")
    data_drift = {
        'amount': np.random.lognormal(4.3, 1.5, N_SAMPLES),  # +30% drift
        'merchant_category': np.random.choice([0, 1, 2, 3, 4], N_SAMPLES),
        'transaction_count_7d': np.random.poisson(6.5, N_SAMPLES),  # +30% drift
        'card_type': np.random.choice([0, 1, 2, 3], N_SAMPLES),
        'card_age_days': np.random.exponential(600, N_SAMPLES),  # Newer cards
        'card_limit': np.random.choice([1000, 2500, 5000, 10000, 25000], N_SAMPLES),
        'user_age': np.random.normal(38, 15, N_SAMPLES).clip(18, 90),  # Younger
        'income_bracket': np.random.choice([0, 1, 2, 3], N_SAMPLES),
        'account_age_days': np.random.exponential(950, N_SAMPLES),  # Newer accounts
        'hour_of_day': np.random.randint(0, 24, N_SAMPLES),
        'day_of_week': np.random.randint(0, 7, N_SAMPLES),
        'month': np.random.randint(1, 13, N_SAMPLES),
        'is_international': np.random.choice([0, 1], N_SAMPLES, p=[0.90, 0.10]),  # More international
        'distance_from_home': np.random.exponential(15, N_SAMPLES),  # Further
    }
    
    # Calculate fraud probability (HIGHER in drifted data)
    fraud_prob_drift = 0.08 + \
                       (data_drift['amount'] > np.percentile(data_drift['amount'], 90)) * 0.03 + \
                       data_drift['is_international'] * 0.03 + \
                       (data_drift['hour_of_day'] < 6) * 0.02
    
    data_drift['is_fraud'] = (np.random.random(N_SAMPLES) < fraud_prob_drift).astype(int)
    
    df_drift = pd.DataFrame(data_drift)
    print(f"  ✓ {len(df_drift):,} rows, {df_drift['is_fraud'].mean():.2%} fraud rate")
    
    # Save datasets
    output_dir = Path('data/large_scale')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n[3/3] Saving datasets...")
    df_orig.to_parquet(output_dir / 'original_100K.parquet', compression='snappy', index=False)
    df_drift.to_parquet(output_dir / 'drifted_100K.parquet', compression='snappy', index=False)
    
    print(f"  ✓ Saved to {output_dir}/")
    
    # Summary
    print("\n" + "="*80)
    print("  GENERATION COMPLETE!")
    print("="*80)
    print(f"\nOriginal Dataset:")
    print(f"  Rows: {len(df_orig):,}")
    print(f"  Fraud Rate: {df_orig['is_fraud'].mean():.2%}")
    print(f"  Features: {len(df_orig.columns)}")
    
    print(f"\nDrifted Dataset:")
    print(f"  Rows: {len(df_drift):,}")
    print(f"  Fraud Rate: {df_drift['is_fraud'].mean():.2%}")
    print(f"  Features: {len(df_drift.columns)}")
    
    print(f"\nDrift Analysis:")
    print(f"  Amount: {df_orig['amount'].mean():.2f} → {df_drift['amount'].mean():.2f} ({((df_drift['amount'].mean() - df_orig['amount'].mean()) / df_orig['amount'].mean() * 100):+.1f}%)")
    print(f"  Fraud Rate: {df_orig['is_fraud'].mean():.2%} → {df_drift['is_fraud'].mean():.2%}")
    print(f"  International: {df_orig['is_international'].mean():.2%} → {df_drift['is_international'].mean():.2%}")
    
    print("\n✅ Ready for upload and drift detection!")
    print("="*80 + "\n")

if __name__ == "__main__":
    generate_quick_datasets()
