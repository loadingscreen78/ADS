"""
File Upload Handler
Handles batch data uploads for drift detection and retraining
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional
import json
from datetime import datetime

class FileUploadHandler:
    """
    Handles file uploads for batch processing
    Supports: Parquet, CSV
    """
    
    def __init__(self, upload_dir: str = "data/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        self.supported_formats = ['.parquet', '.csv']
        self.max_file_size = 500 * 1024 * 1024  # 500MB
        
        print(f"[FileHandler] Initialized")
        print(f"  Upload dir: {self.upload_dir}")
        print(f"  Supported formats: {', '.join(self.supported_formats)}")
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        """
        Validate uploaded file
        
        Returns:
            (is_valid, message)
        """
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.supported_formats:
            return False, f"Unsupported format. Use: {', '.join(self.supported_formats)}"
        
        # Check file size
        if file_size > self.max_file_size:
            max_mb = self.max_file_size / (1024 * 1024)
            return False, f"File too large. Max size: {max_mb:.0f}MB"
        
        return True, "Valid"
    
    def load_file(self, filepath: str) -> Tuple[Optional[pd.DataFrame], str]:
        """
        Load file into DataFrame
        
        Returns:
            (dataframe, message)
        """
        try:
            filepath = Path(filepath)
            file_ext = filepath.suffix.lower()
            
            print(f"[FileHandler] Loading {filepath.name}...")
            
            if file_ext == '.parquet':
                df = pd.read_parquet(filepath)
            elif file_ext == '.csv':
                df = pd.read_csv(filepath)
            else:
                return None, f"Unsupported format: {file_ext}"
            
            print(f"  ✓ Loaded {len(df):,} rows, {len(df.columns)} columns")
            
            return df, "Success"
            
        except Exception as e:
            return None, f"Error loading file: {str(e)}"
    
    def extract_metadata(self, df: pd.DataFrame, filename: str) -> Dict:
        """
        Extract metadata from DataFrame
        """
        metadata = {
            "filename": filename,
            "upload_time": datetime.now().isoformat(),
            "n_rows": len(df),
            "n_columns": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "memory_mb": df.memory_usage(deep=True).sum() / (1024 * 1024),
            "missing_values": df.isnull().sum().to_dict(),
        }
        
        # Check for target column
        if 'is_fraud' in df.columns:
            metadata["has_target"] = True
            metadata["fraud_rate"] = float(df['is_fraud'].mean())
            metadata["class_distribution"] = df['is_fraud'].value_counts().to_dict()
        else:
            metadata["has_target"] = False
        
        # Numeric column statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        metadata["numeric_stats"] = {}
        for col in numeric_cols:
            metadata["numeric_stats"][col] = {
                "mean": float(df[col].mean()),
                "std": float(df[col].std()),
                "min": float(df[col].min()),
                "max": float(df[col].max()),
            }
        
        return metadata
    
    def save_metadata(self, metadata: Dict, batch_id: str):
        """Save metadata to JSON"""
        metadata_path = self.upload_dir / f"{batch_id}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"  ✓ Metadata saved: {metadata_path.name}")
    
    def process_upload(self, filepath: str, batch_id: str) -> Tuple[Optional[pd.DataFrame], Dict, str]:
        """
        Complete upload processing pipeline
        
        Returns:
            (dataframe, metadata, message)
        """
        # Load file
        df, message = self.load_file(filepath)
        if df is None:
            return None, {}, message
        
        # Extract metadata
        metadata = self.extract_metadata(df, Path(filepath).name)
        metadata["batch_id"] = batch_id
        
        # Save metadata
        self.save_metadata(metadata, batch_id)
        
        print(f"[FileHandler] Processing complete")
        print(f"  Batch ID: {batch_id}")
        print(f"  Rows: {metadata['n_rows']:,}")
        print(f"  Columns: {metadata['n_columns']}")
        if metadata.get("has_target"):
            print(f"  Fraud Rate: {metadata['fraud_rate']:.2%}")
        
        return df, metadata, "Success"


# Test
if __name__ == "__main__":
    handler = FileUploadHandler()
    
    # Test with generated dataset
    test_file = "data/large_scale/original_100K.parquet"
    if Path(test_file).exists():
        df, metadata, msg = handler.process_upload(test_file, "test_batch_001")
        print(f"\nTest Result: {msg}")
        print(f"Metadata keys: {list(metadata.keys())}")
