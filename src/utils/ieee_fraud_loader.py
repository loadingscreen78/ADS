"""
IEEE Fraud Detection Dataset Loader
Downloads and prepares the IEEE fraud detection dataset for drift monitoring.
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
import zipfile


class IEEEFraudLoader:
    """
    Loads and prepares IEEE Fraud Detection dataset.
    Dataset: https://www.kaggle.com/c/ieee-fraud-detection
    
    This dataset contains real-world credit card transactions with:
    - Transaction features (amount, product code, card info, etc.)
    - Identity features (device info, network info, etc.)
    - Binary fraud label (isFraud)
    """
    
    def __init__(self, data_dir: str = "data/ieee_fraud"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def check_dataset_exists(self) -> bool:
        """Check if dataset files exist."""
        required_files = [
            "train_transaction.csv",
            "train_identity.csv"
        ]
        return all((self.data_dir / f).exists() for f in required_files)
    
    def load_and_prepare(self, sample_size: int = 100000) -> pd.DataFrame:
        """
        Load IEEE fraud dataset and prepare for drift detection.
        
        Args:
            sample_size: Number of rows to sample (for memory efficiency)
            
        Returns:
            DataFrame with selected features for drift monitoring
        """
        print(f"[IEEE] Loading dataset from {self.data_dir}")
        
        if not self.check_dataset_exists():
            print("[ERROR] Dataset not found!")
            print("Please download from: https://www.kaggle.com/c/ieee-fraud-detection/data")
            print("Or run: kaggle competitions download -c ieee-fraud-detection")
            print(f"Extract files to: {self.data_dir}")
            raise FileNotFoundError("IEEE fraud dataset not found")
        
        # Load transaction data
        print("[IEEE] Loading transaction data...")
        df_trans = pd.read_parquet(self.data_dir / "train_transaction.csv", 
                                    nrows=sample_size)
        
        # Select key features for drift monitoring
        # These are the most important features that show drift over time
        feature_cols = [
            'TransactionAmt',      # Transaction amount
            'ProductCD',           # Product code
            'card1', 'card2', 'card3', 'card4', 'card5', 'card6',  # Card info
            'addr1', 'addr2',      # Address
            'dist1', 'dist2',      # Distance
            'P_emaildomain',       # Purchaser email domain
            'R_emaildomain',       # Recipient email domain
            'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12', 'C13', 'C14',  # Counts
            'D1', 'D2', 'D3', 'D4', 'D5', 'D10', 'D15',  # Timedeltas
            'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9',  # Match
            'V12', 'V13', 'V36', 'V37', 'V38', 'V53', 'V54', 'V56', 'V62', 'V70', 'V76', 'V78', 'V82', 'V83', 'V87', 'V90', 'V91', 'V94', 'V96', 'V97',  # Vesta features
            'isFraud'              # Target label
        ]
        
        # Keep only columns that exist
        available_cols = [col for col in feature_cols if col in df_trans.columns]
        df = df_trans[available_cols].copy()
        
        # Encode categorical features
        print("[IEEE] Encoding categorical features...")
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            if col != 'isFraud':
                df[col] = pd.Categorical(df[col]).codes
        
        # Handle missing values
        print("[IEEE] Handling missing values...")
        df = df.fillna(df.median(numeric_only=True))
        
        # Add time-based features for drift simulation
        df['TransactionDT_hour'] = (df['TransactionDT'] / 3600) % 24
        df['TransactionDT_day'] = (df['TransactionDT'] / 86400) % 7
        
        print(f"[IEEE] Loaded {len(df):,} transactions with {len(df.columns)} features")
        print(f"[IEEE] Fraud rate: {df['isFraud'].mean():.2%}")
        
        return df
    
    def create_time_windows(self, df: pd.DataFrame, n_windows: int = 10) -> list:
        """
        Split data into time windows to simulate weekly batches.
        This creates the temporal drift that we'll detect with LSTM.
        
        Args:
            df: Full dataset
            n_windows: Number of time windows (weeks)
            
        Returns:
            List of DataFrames, one per time window
        """
        print(f"[IEEE] Creating {n_windows} time windows...")
        
        # Sort by transaction time
        df = df.sort_values('TransactionDT').reset_index(drop=True)
        
        # Split into equal-sized windows
        window_size = len(df) // n_windows
        windows = []
        
        for i in range(n_windows):
            start_idx = i * window_size
            end_idx = start_idx + window_size if i < n_windows - 1 else len(df)
            window_df = df.iloc[start_idx:end_idx].copy()
            windows.append(window_df)
            print(f"  Window {i+1}: {len(window_df):,} transactions, "
                  f"fraud rate: {window_df['isFraud'].mean():.2%}")
        
        return windows
    
    def save_windows(self, windows: list, output_dir: str = "data/ieee_windows"):
        """Save time windows as separate parquet files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for i, window_df in enumerate(windows):
            filepath = output_path / f"week_{i+1:02d}.parquet"
            window_df.to_parquet(filepath, index=False)
            print(f"[IEEE] Saved window {i+1} to {filepath}")
        
        # Save first window as reference
        ref_path = Path("data/reference/ieee_reference.parquet")
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        windows[0].to_parquet(ref_path, index=False)
        print(f"[IEEE] Saved reference distribution to {ref_path}")


if __name__ == "__main__":
    loader = IEEEFraudLoader()
    
    try:
        # Load dataset
        df = loader.load_and_prepare(sample_size=200000)
        
        # Create weekly windows
        windows = loader.create_time_windows(df, n_windows=10)
        
        # Save windows
        loader.save_windows(windows)
        
        print("\n[IEEE] Dataset preparation complete!")
        print("Ready for drift detection and LSTM forecasting.")
        
    except FileNotFoundError as e:
        print(f"\n{e}")
        print("\nTo download the dataset:")
        print("1. Install Kaggle CLI: pip install kaggle")
        print("2. Set up Kaggle API credentials: https://www.kaggle.com/docs/api")
        print("3. Run: kaggle competitions download -c ieee-fraud-detection")
        print("4. Extract to: data/ieee_fraud/")
