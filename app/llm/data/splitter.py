import pandas as pd
from pathlib import Path
from sklearn.model_selection import KFold

from app.llm.utils.logger import Logger

class Splitter:
    def __init__(self, data_path: str, output_dir: str, k_folds: int):
        self.data_path = Path(data_path)
        self.output_dir = Path(output_dir)
        self.k_folds = k_folds
        self.logger = Logger(__name__)

        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _read_data(self):
        if self.data_path.suffix == ".csv":
            return pd.read_csv(self.data_path)
        elif self.data_path.suffix == ".json":
            return pd.read_json(self.data_path)
        elif self.data_path.suffix == ".xlsx":
            return pd.read_excel(self.data_path)
        elif self.data_path.suffix == ".parquet":
            return pd.read_parquet(self.data_path)
        else:
            raise ValueError(f"Unsupported data file format: {self.data_path.suffix}")

    def split(self):
        df = self._read_data()
        kf = KFold(n_splits=self.k_folds, shuffle=True, random_state=42)

        for fold, (train_index, test_index) in enumerate(kf.split(df)):
            train_df = df.iloc[train_index]
            test_df = df.iloc[test_index]

            fold_dir = self.output_dir / f"fold_{fold}"
            fold_dir.mkdir(exist_ok=True)

            train_df.to_csv(fold_dir / "train.csv", index=False)
            test_df.to_csv(fold_dir / "test.csv", index=False)
            self.logger.info(f"Fold {fold} saved to {fold_dir}")