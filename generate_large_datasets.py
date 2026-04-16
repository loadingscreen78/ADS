"""
Large-Scale Synthetic Dataset Generator
Generates millions of rows for original and drifted datasets
Based on research papers: SHML, CARA, Multi-Model Awareness
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
from pathlib import Path

class LargeScaleDataGenerator:
    """
    Generates large-scale synthetic fraud detection datasets
    with controlled drift patterns
    """
    
    def __init__(self, n_samples=2_000_000, random_state=42):
        self.n_samples = n_samples
        self.random_state = random_state
        np.random.seed(random_state)
        
        print(f"[DataGen] Initializing generator for {n_samples:,} samples")
    
    def generate_original_dataset(self):
        """
        Generate original baseline dataset (no drift)
        2M rows, 15 features, 5% fraud rate
        """
        print(f"\n[DataGen] Generating ORIGINAL dataset ({self.n_samples:,} rows)...")
        
        # Initialize data dictionary
        data = {}
        
        # Transaction features
        print("  Generating transaction features...")
        data['amount'] = np.random.lognormal(mean=4.0, sigma=1.5, size=self.n_samples)
        data['merchant_category'] = np.random.choice(['retail', 'online', 'grocery', 'gas', 'restaurant'], 
                                                     size=self.n_samples, 
                                                     p=[0.3, 0.25, 0.2, 0.15, 0.1])
        data['transaction_count_7d'] = np.random.poisson(lam=5, size=self.n_samples)
        
        # Card features
        print("  Generating card features...")
        data['card_type'] = np.random.choice(['visa', 'mastercard', 'amex', 'discover'], 
                                             size=self.n_samples,
                                             p=[0.45, 0.35, 0.15, 0.05])
        data['card_age_days'] = np.random.exponential(scale=730, size=self.n_samples)  # ~2 years avg
        data['card_limit'] = np.random.choice([1000, 2500, 5000, 10000, 25000], 
                                              size=self.n_samples,
                                              p=[0.2, 0.3, 0.25, 0.15, 0.1])
        
        # User features
        print("  Generating user features...")
        data['user_age'] = np.random.normal(loc=40, scale=15, size=self.n_samples).clip(18, 90)
        data['income_bracket'] = np.random.choice(['low', 'medium', 'high', 'very_high'], 
                                                  size=self.n_samples,
                                                  p=[0.25, 0.40, 0.25, 0.10])
        data['account_age_days'] = np.random.exponential(scale=1095, size=self.n_samples)  # ~3 years avg
        
        # Temporal features
        print("  Generating temporal features...")
        data['hour_of_day'] = np.random.choice(range(24), size=self.n_samples,
                                               p=self._get_hour_distribution())
        data['day_of_week'] = np.random.choice(range(7), size=self.n_samples)
        data['month'] = np.random.choice(range(1, 13), size=self.n_samples)
        
        # Behavioral features
        print("  Generating behavioral features...")
        data['avg_transaction_amount'] = data['amount'] * np.random.uniform(0.8, 1.2, size=self.n_samples)
        data['transaction_velocity'] = np.random.exponential(scale=2.0, size=self.n_samples)  # transactions per day
        
        # Location features
        print("  Generating location features...")
        data['is_international'] = np.random.choice([0, 1], size=self.n_samples, p=[0.95, 0.05])
        data['distance_from_home'] = np.random.exponential(scale=10, size=self.n_samples)  # km
        
        # Generate fraud labels (5% fraud rate)
        print("  Generating fraud labels...")
        fraud_probability = self._calculate_fraud_probability(data)
        data['is_fraud'] = (np.random.random(self.n_samples) < fraud_probability).astype(int)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Encode categorical variables
        df = self._encode_categorical(df)
        
        print(f"  ✓ Generated {len(df):,} rows")
        print(f"  ✓ Fraud rate: {df['is_fraud'].mean():.2%}")
        print(f"  ✓ Features: {len(df.columns)}")
        
        return df
    
    def generate_drifted_dataset(self, drift_type='all', drift_severity=0.3):
        """
        Generate drifted dataset with controlled drift patterns
        
        Args:
            drift_type: 'covariate', 'concept', 'prior', or 'all'
            drift_severity: 0.0 to 1.0 (amount of drift)
        """
        print(f"\n[DataGen] Generating DRIFTED dataset ({self.n_samples:,} rows)...")
        print(f"  Drift type: {drift_type}")
        print(f"  Drift severity: {drift_severity:.1%}")
        
        # Start with original distribution
        data = {}
        
        # Transaction features (WITH DRIFT)
        print("  Generating transaction features (with drift)...")
        if drift_type in ['covariate', 'all']:
            # Covariate drift: distribution shifts
            data['amount'] = np.random.lognormal(mean=4.0 + drift_severity, sigma=1.5, size=self.n_samples)
            data['transaction_count_7d'] = np.random.poisson(lam=5 * (1 + drift_severity), size=self.n_samples)
        else:
            data['amount'] = np.random.lognormal(mean=4.0, sigma=1.5, size=self.n_samples)
            data['transaction_count_7d'] = np.random.poisson(lam=5, size=self.n_samples)
        
        data['merchant_category'] = np.random.choice(['retail', 'online', 'grocery', 'gas', 'restaurant'], 
                                                     size=self.n_samples, 
                                                     p=[0.25, 0.35, 0.15, 0.15, 0.1])  # Online increased
        
        # Card features (WITH DRIFT)
        print("  Generating card features (with drift)...")
        data['card_type'] = np.random.choice(['visa', 'mastercard', 'amex', 'discover'], 
                                             size=self.n_samples,
                                             p=[0.40, 0.40, 0.15, 0.05])  # Mastercard increased
        data['card_age_days'] = np.random.exponential(scale=730 * (1 - drift_severity * 0.3), size=self.n_samples)
        data['card_limit'] = np.random.choice([1000, 2500, 5000, 10000, 25000], 
                                              size=self.n_samples,
                                              p=[0.15, 0.25, 0.30, 0.20, 0.10])  # Higher limits
        
        # User features (WITH DRIFT)
        print("  Generating user features (with drift)...")
        data['user_age'] = np.random.normal(loc=40 - drift_severity * 5, scale=15, size=self.n_samples).clip(18, 90)  # Younger users
        data['income_bracket'] = np.random.choice(['low', 'medium', 'high', 'very_high'], 
                                                  size=self.n_samples,
                                                  p=[0.20, 0.35, 0.30, 0.15])  # Higher income
        data['account_age_days'] = np.random.exponential(scale=1095 * (1 - drift_severity * 0.2), size=self.n_samples)
        
        # Temporal features (WITH DRIFT)
        print("  Generating temporal features (with drift)...")
        data['hour_of_day'] = np.random.choice(range(24), size=self.n_samples,
                                               p=self._get_hour_distribution(shifted=True))
        data['day_of_week'] = np.random.choice(range(7), size=self.n_samples)
        data['month'] = np.random.choice(range(1, 13), size=self.n_samples)
        
        # Behavioral features (WITH DRIFT)
        print("  Generating behavioral features (with drift)...")
        data['avg_transaction_amount'] = data['amount'] * np.random.uniform(0.9, 1.3, size=self.n_samples)
        data['transaction_velocity'] = np.random.exponential(scale=2.5, size=self.n_samples)  # More frequent
        
        # Location features (WITH DRIFT)
        print("  Generating location features (with drift)...")
        data['is_international'] = np.random.choice([0, 1], size=self.n_samples, p=[0.90, 0.10])  # More international
        data['distance_from_home'] = np.random.exponential(scale=15, size=self.n_samples)  # Further from home
        
        # Generate fraud labels (WITH DRIFT)
        print("  Generating fraud labels (with drift)...")
        if drift_type in ['concept', 'prior', 'all']:
            # Concept drift: fraud patterns change
            # Prior drift: fraud rate increases
            fraud_probability = self._calculate_fraud_probability(data, drifted=True, drift_severity=drift_severity)
        else:
            fraud_probability = self._calculate_fraud_probability(data)
        
        data['is_fraud'] = (np.random.random(self.n_samples) < fraud_probability).astype(int)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Encode categorical variables
        df = self._encode_categorical(df)
        
        print(f"  ✓ Generated {len(df):,} rows")
        print(f"  ✓ Fraud rate: {df['is_fraud'].mean():.2%}")
        print(f"  ✓ Features: {len(df.columns)}")
        print(f"  ✓ Drift applied: {drift_type} ({drift_severity:.1%})")
        
        return df
    
    def _get_hour_distribution(self, shifted=False):
        """Get realistic hour-of-day distribution"""
        if shifted:
            # Shifted distribution (drift)
            probs = np.array([0.01, 0.01, 0.01, 0.01, 0.01, 0.02,  # 0-5
                             0.03, 0.04, 0.05, 0.06, 0.06, 0.06,  # 6-11
                             0.07, 0.07, 0.06, 0.06, 0.06, 0.06,  # 12-17
                             0.07, 0.08, 0.07, 0.05, 0.03, 0.02]) # 18-23
        else:
            # Normal distribution
            probs = np.array([0.01, 0.01, 0.01, 0.01, 0.01, 0.02,  # 0-5
                             0.03, 0.04, 0.05, 0.06, 0.06, 0.06,  # 6-11
                             0.06, 0.06, 0.05, 0.05, 0.05, 0.06,  # 12-17
                             0.07, 0.07, 0.06, 0.04, 0.03, 0.02]) # 18-23
        return probs / probs.sum()
    
    def _calculate_fraud_probability(self, data, drifted=False, drift_severity=0.3):
        """Calculate fraud probability based on features"""
        n = len(data['amount'])
        base_prob = 0.05  # 5% base fraud rate
        
        if drifted:
            base_prob = 0.05 + drift_severity * 0.03  # Increase to ~8%
        
        # Risk factors
        prob = np.full(n, base_prob)
        
        # High amount increases risk
        prob += (data['amount'] > np.percentile(data['amount'], 90)) * 0.03
        
        # International transactions
        prob += data['is_international'] * 0.02
        
        # Late night transactions
        prob += (data['hour_of_day'] < 6) * 0.02
        
        # High velocity
        prob += (data['transaction_velocity'] > 5) * 0.02
        
        # Far from home
        prob += (data['distance_from_home'] > 50) * 0.02
        
        if drifted:
            # New fraud patterns in drifted data
            prob += (data['merchant_category'] == 'online') * 0.03  # Online fraud increases
            prob += (data['card_age_days'] < 90) * 0.02  # New cards more risky
        
        return np.clip(prob, 0, 0.5)  # Cap at 50%
    
    def _encode_categorical(self, df):
        """Encode categorical variables"""
        categorical_cols = ['merchant_category', 'card_type', 'income_bracket']
        
        for col in categorical_cols:
            if col in df.columns:
                df[col] = pd.Categorical(df[col]).codes
        
        return df
    
    def save_dataset(self, df, filename, output_dir='data/large_scale'):
        """Save dataset to parquet format"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filepath = output_path / filename
        
        print(f"\n[DataGen] Saving to {filepath}...")
        df.to_parquet(filepath, compression='snappy', index=False)
        
        file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB
        print(f"  ✓ Saved {len(df):,} rows")
        print(f"  ✓ File size: {file_size:.1f} MB")
        print(f"  ✓ Compression: snappy")
        
        return filepath

def main():
    """Generate both original and drifted datasets"""
    print("="*80)
    print("  LARGE-SCALE DATASET GENERATION")
    print("  Based on Research Papers: SHML, CARA, Multi-Model Awareness")
    print("="*80)
    
    # Configuration
    N_SAMPLES = 2_000_000  # 2 million rows
    
    # Initialize generator
    generator = LargeScaleDataGenerator(n_samples=N_SAMPLES)
    
    # Generate original dataset
    print("\n" + "="*80)
    print("  PHASE 1: ORIGINAL DATASET (Baseline)")
    print("="*80)
    df_original = generator.generate_original_dataset()
    filepath_original = generator.save_dataset(df_original, 'original_2M.parquet')
    
    # Generate drifted dataset
    print("\n" + "="*80)
    print("  PHASE 2: DRIFTED DATASET (Test)")
    print("="*80)
    df_drifted = generator.generate_drifted_dataset(drift_type='all', drift_severity=0.3)
    filepath_drifted = generator.save_dataset(df_drifted, 'drifted_2M.parquet')
    
    # Summary
    print("\n" + "="*80)
    print("  GENERATION COMPLETE!")
    print("="*80)
    print(f"\nOriginal Dataset:")
    print(f"  File: {filepath_original}")
    print(f"  Rows: {len(df_original):,}")
    print(f"  Fraud Rate: {df_original['is_fraud'].mean():.2%}")
    print(f"  Features: {len(df_original.columns)}")
    
    print(f"\nDrifted Dataset:")
    print(f"  File: {filepath_drifted}")
    print(f"  Rows: {len(df_drifted):,}")
    print(f"  Fraud Rate: {df_drifted['is_fraud'].mean():.2%}")
    print(f"  Features: {len(df_drifted.columns)}")
    
    print(f"\nDrift Characteristics:")
    print(f"  Type: All (Covariate + Concept + Prior)")
    print(f"  Severity: 30%")
    print(f"  Fraud Rate Change: {df_original['is_fraud'].mean():.2%} → {df_drifted['is_fraud'].mean():.2%}")
    
    # Feature drift analysis
    print(f"\nFeature Drift Analysis:")
    for col in ['amount', 'transaction_count_7d', 'card_age_days']:
        orig_mean = df_original[col].mean()
        drift_mean = df_drifted[col].mean()
        change = ((drift_mean - orig_mean) / orig_mean) * 100
        print(f"  {col}: {orig_mean:.2f} → {drift_mean:.2f} ({change:+.1f}%)")
    
    print("\n" + "="*80)
    print("  Ready for Self-Healing ML Pipeline!")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
