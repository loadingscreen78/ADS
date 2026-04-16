# src/utils/data_generator.py

import numpy as np
import os

# Use cuDF if GPU available, else pandas
try:
    import cudf as pd_lib
    GPU = True
except ImportError:
    import pandas as pd_lib
    GPU = False

import pandas as pd  # always need real pandas for some ops


class DataGenerator:
    """
    Generates synthetic credit card transaction data.
    Used to simulate real production data for testing.
    Features mimic real fraud detection datasets.
    """

    FEATURES = [
        "amount",           # Transaction amount in USD
        "hour_of_day",      # 0-23
        "day_of_week",      # 0-6
        "merchant_category",# 0-9 (encoded)
        "user_age_bucket",  # 0-5 (encoded age ranges)
        "transaction_count_7d",  # rolling 7-day count
        "avg_amount_30d",   # rolling 30-day average amount
        "distance_from_home",    # km from home location
        "is_international",      # 0 or 1
        "card_present",          # 0 or 1
    ]

    def generate_reference(self, n_rows: int = 100_000, seed: int = 42) -> pd.DataFrame:
        """
        Generate REFERENCE (training) distribution.
        This is what the model was trained on.
        Saved to disk as the baseline for drift detection.
        """
        np.random.seed(seed)
        data = {
            "amount":                np.random.exponential(scale=50,  size=n_rows).clip(1, 5000),
            "hour_of_day":           np.random.randint(0, 24,         size=n_rows).astype(float),
            "day_of_week":           np.random.randint(0, 7,          size=n_rows).astype(float),
            "merchant_category":     np.random.randint(0, 10,         size=n_rows).astype(float),
            "user_age_bucket":       np.random.randint(0, 6,          size=n_rows).astype(float),
            "transaction_count_7d":  np.random.poisson(lam=5,         size=n_rows).astype(float),
            "avg_amount_30d":        np.random.normal(loc=45, scale=20, size=n_rows).clip(1, 1000),
            "distance_from_home":    np.random.exponential(scale=10,  size=n_rows).clip(0, 500),
            "is_international":      np.random.binomial(1, p=0.08,    size=n_rows).astype(float),
            "card_present":          np.random.binomial(1, p=0.75,    size=n_rows).astype(float),
        }
        # Add binary label: ~3% fraud rate
        fraud_prob = (
            0.001 * data["amount"] / 100 +
            0.3 * data["is_international"] +
            0.1 * (1 - data["card_present"])
        )
        data["is_fraud"] = (np.random.random(n_rows) < fraud_prob.clip(0, 1)).astype(int)
        return pd.DataFrame(data)

    def generate_drifted(self, n_rows: int = 50_000, drift_level: str = "moderate") -> pd.DataFrame:
        """
        Generate DRIFTED production data.
        drift_level: 'none', 'moderate', 'severe'

        Simulates what happens when real-world behavior changes —
        e.g., post-pandemic spending shifts, new fraud patterns.
        """
        base = self.generate_reference(n_rows, seed=99)

        if drift_level == "none":
            return base

        elif drift_level == "moderate":
            # Simulate: amounts increased, more international transactions
            base["amount"] = base["amount"] * 1.4 + np.random.normal(0, 10, n_rows)
            base["is_international"] = np.random.binomial(1, p=0.18, size=n_rows).astype(float)
            base["merchant_category"] = np.random.randint(3, 10, size=n_rows).astype(float)

        elif drift_level == "severe":
            # Simulate: major behavioral shift — like a global event
            base["amount"] = np.random.exponential(scale=150, size=n_rows).clip(1, 10000)
            base["is_international"] = np.random.binomial(1, p=0.45, size=n_rows).astype(float)
            base["hour_of_day"] = np.random.choice([22, 23, 0, 1, 2], size=n_rows).astype(float)
            base["transaction_count_7d"] = np.random.poisson(lam=15, size=n_rows).astype(float)

        return base

    def save_reference(self, df: pd.DataFrame, path: str = "data/reference/reference.parquet"):
        """Save reference distribution to Parquet."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_parquet(path, index=False)
        print(f"[OK] Reference saved: {path} ({len(df):,} rows, {len(df.columns)} features)")

    def save_production_batch(self, df: pd.DataFrame, batch_id: str,
                               path: str = "data/production/"):
        """Save a production batch to Parquet."""
        os.makedirs(path, exist_ok=True)
        out = os.path.join(path, f"batch_{batch_id}.parquet")
        df.to_parquet(out, index=False)
        print(f"[OK] Production batch saved: {out}")
        return out


# ── RUN THIS FIRST ──────────────────────────────────────────────────
if __name__ == "__main__":
    gen = DataGenerator()

    print("Generating reference distribution (100K rows)...")
    ref = gen.generate_reference(n_rows=100_000)
    gen.save_reference(ref)

    print("\nGenerating clean production batch (no drift)...")
    clean = gen.generate_drifted(n_rows=50_000, drift_level="none")
    gen.save_production_batch(clean, batch_id="001_clean")

    print("\nGenerating moderate drift batch...")
    moderate = gen.generate_drifted(n_rows=50_000, drift_level="moderate")
    gen.save_production_batch(moderate, batch_id="002_moderate")

    print("\nGenerating severe drift batch...")
    severe = gen.generate_drifted(n_rows=50_000, drift_level="severe")
    gen.save_production_batch(severe, batch_id="003_severe")

    print("\nData generation complete.")
    print(f"Reference columns: {list(ref.columns)}")
    print(f"Reference shape: {ref.shape}")
    print(f"Fraud rate: {ref['is_fraud'].mean():.2%}")
