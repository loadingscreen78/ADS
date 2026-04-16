"""
Create Custom Upload File
Generates a small test file for custom upload demo
"""

import numpy as np
import pandas as pd
from pathlib import Path

def create_custom_file():
    """Create a custom test file for upload"""
    print("\n" + "="*80)
    print("  CREATING CUSTOM UPLOAD FILE")
    print("="*80)
    
    # Generate smaller dataset (10K rows for quick upload)
    N_SAMPLES = 10_000
    np.random.seed(123)
    
    print(f"\n[1/3] Generating {N_SAMPLES:,} rows...")
    
    # Create realistic fraud detection data
    data = {
        'amount': np.random.lognormal(4.2, 1.5, N_SAMPLES),
        'merchant_category': np.random.choice([0, 1, 2, 3, 4], N_SAMPLES),
        'transaction_count_7d': np.random.poisson(6, N_SAMPLES),
        'card_type': np.random.choice([0, 1, 2, 3], N_SAMPLES),
        'card_age_days': np.random.exponential(650, N_SAMPLES),
        'card_limit': np.random.choice([1000, 2500, 5000, 10000, 25000], N_SAMPLES),
        'user_age': np.random.normal(38, 14, N_SAMPLES).clip(18, 90),
        'income_bracket': np.random.choice([0, 1, 2, 3], N_SAMPLES),
        'account_age_days': np.random.exponential(1000, N_SAMPLES),
        'hour_of_day': np.random.randint(0, 24, N_SAMPLES),
        'day_of_week': np.random.randint(0, 7, N_SAMPLES),
        'month': np.random.randint(1, 13, N_SAMPLES),
        'is_international': np.random.choice([0, 1], N_SAMPLES, p=[0.92, 0.08]),
        'distance_from_home': np.random.exponential(12, N_SAMPLES),
    }
    
    # Calculate fraud probability (MODERATE drift)
    fraud_prob = 0.07 + \
                 (data['amount'] > np.percentile(data['amount'], 90)) * 0.03 + \
                 data['is_international'] * 0.025 + \
                 (data['hour_of_day'] < 6) * 0.02
    
    data['is_fraud'] = (np.random.random(N_SAMPLES) < fraud_prob).astype(int)
    
    df = pd.DataFrame(data)
    
    print(f"  ✓ Generated {len(df):,} rows")
    print(f"  ✓ Fraud rate: {df['is_fraud'].mean():.2%}")
    print(f"  ✓ Features: {len(df.columns)}")
    
    # Save as Parquet
    output_dir = Path('custom_uploads')
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / 'custom_test_10K.parquet'
    
    print(f"\n[2/3] Saving to {output_file}...")
    df.to_parquet(output_file, compression='snappy', index=False)
    
    file_size = output_file.stat().st_size / 1024 / 1024
    print(f"  ✓ Saved: {file_size:.2f} MB")
    
    # Also create CSV version
    csv_file = output_dir / 'custom_test_10K.csv'
    print(f"\n[3/4] Creating CSV version...")
    df.to_csv(csv_file, index=False)
    
    csv_size = csv_file.stat().st_size / 1024 / 1024
    print(f"  ✓ Saved: {csv_size:.2f} MB")
    
    # Create Excel version for judges
    excel_file = output_dir / 'custom_test_10K.xlsx'
    print(f"\n[4/4] Creating Excel version for judges...")
    
    # Create Excel with formatting
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Write main data (first 1000 rows for quick viewing)
        df.head(1000).to_excel(writer, sheet_name='Data Sample', index=False)
        
        # Create summary sheet
        summary_data = {
            'Metric': [
                'Total Rows',
                'Total Columns',
                'Fraud Rate',
                'Mean Transaction Amount',
                'Median Transaction Amount',
                'Max Transaction Amount',
                'International Transactions',
                'Average Card Age (days)',
                'Average Account Age (days)',
                'Transactions per Week (avg)',
            ],
            'Value': [
                f"{len(df):,}",
                len(df.columns),
                f"{df['is_fraud'].mean():.2%}",
                f"${df['amount'].mean():.2f}",
                f"${df['amount'].median():.2f}",
                f"${df['amount'].max():.2f}",
                f"{df['is_international'].mean():.2%}",
                f"{df['card_age_days'].mean():.0f}",
                f"{df['account_age_days'].mean():.0f}",
                f"{df['transaction_count_7d'].mean():.1f}",
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Create fraud analysis sheet
        fraud_stats = df.groupby('is_fraud').agg({
            'amount': ['count', 'mean', 'median', 'max'],
            'is_international': 'mean',
            'transaction_count_7d': 'mean'
        }).round(2)
        fraud_stats.to_excel(writer, sheet_name='Fraud Analysis')
        
        # Create column descriptions sheet
        descriptions = {
            'Column': [
                'amount', 'merchant_category', 'transaction_count_7d', 'card_type',
                'card_age_days', 'card_limit', 'user_age', 'income_bracket',
                'account_age_days', 'hour_of_day', 'day_of_week', 'month',
                'is_international', 'distance_from_home', 'is_fraud'
            ],
            'Description': [
                'Transaction amount in dollars',
                'Merchant category (0-4)',
                'Number of transactions in last 7 days',
                'Card type (0=Debit, 1=Credit, 2=Premium, 3=Business)',
                'Age of card in days',
                'Credit card limit',
                'User age in years',
                'Income bracket (0=Low, 1=Medium, 2=High, 3=Very High)',
                'Account age in days',
                'Hour of transaction (0-23)',
                'Day of week (0=Monday, 6=Sunday)',
                'Month of transaction (1-12)',
                'International transaction flag (0=No, 1=Yes)',
                'Distance from home in miles',
                'Fraud label (0=Legitimate, 1=Fraud)'
            ],
            'Type': [
                'Continuous', 'Categorical', 'Count', 'Categorical',
                'Continuous', 'Categorical', 'Continuous', 'Categorical',
                'Continuous', 'Categorical', 'Categorical', 'Categorical',
                'Binary', 'Continuous', 'Binary (Target)'
            ]
        }
        desc_df = pd.DataFrame(descriptions)
        desc_df.to_excel(writer, sheet_name='Column Descriptions', index=False)
    
    excel_size = excel_file.stat().st_size / 1024 / 1024
    print(f"  ✓ Saved: {excel_size:.2f} MB")
    print(f"  ✓ Sheets: Data Sample, Summary, Fraud Analysis, Column Descriptions")
    
    # Summary
    print("\n" + "="*80)
    print("  CUSTOM FILES CREATED!")
    print("="*80)
    
    print(f"\n📁 Files Created:")
    print(f"   1. {output_file}")
    print(f"      Size: {file_size:.2f} MB")
    print(f"      Format: Parquet (recommended)")
    
    print(f"\n   2. {csv_file}")
    print(f"      Size: {csv_size:.2f} MB")
    print(f"      Format: CSV")
    
    print(f"\n   3. {excel_file}")
    print(f"      Size: {excel_size:.2f} MB")
    print(f"      Format: Excel (for judges)")
    
    print(f"\n📊 Dataset Details:")
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   Fraud Rate: {df['is_fraud'].mean():.2%}")
    print(f"   Mean Amount: ${df['amount'].mean():.2f}")
    print(f"   International: {df['is_international'].mean():.2%}")
    
    print(f"\n🎯 Drift Characteristics:")
    print(f"   Amount: Moderate drift (+25%)")
    print(f"   Fraud Rate: 7.5% (vs 6% baseline)")
    print(f"   International: 8% (vs 5% baseline)")
    
    print(f"\n📤 How to Upload:")
    print(f"   1. Open: http://localhost:8080")
    print(f"   2. Click: 📁 Upload Custom File")
    print(f"   3. Select: {output_file.name}")
    print(f"   4. Batch ID: custom_test_001")
    print(f"   5. Click: Upload")
    
    print(f"\n👨‍⚖️ For Judges:")
    print(f"   Open Excel file to view data:")
    print(f"   {excel_file}")
    print(f"   - Sheet 1: Data Sample (1000 rows)")
    print(f"   - Sheet 2: Summary Statistics")
    print(f"   - Sheet 3: Fraud Analysis")
    print(f"   - Sheet 4: Column Descriptions")
    
    print(f"\n✅ Files ready for upload!")
    print("="*80 + "\n")
    
    return output_file, csv_file, excel_file

if __name__ == "__main__":
    create_custom_file()
