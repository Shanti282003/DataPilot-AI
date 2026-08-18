import io
import chardet
import pandas as pd
from typing import Tuple, Dict, Any


class FileDetector:
    """
    Safely inspects raw file bytes to detect:
    1. File character encoding (utf-8, latin-1, etc.)
    2. Delimiter / separator (comma, semicolon, tab, pipe)
    """

    SUPPORTED_DELIMITERS = [",", ";", "\t", "|"]

    @staticmethod
    def detect_encoding(file_bytes: bytes) -> str:
        """Detect file character encoding using chardet on the first 50KB sample."""
        sample = file_bytes[:50000]
        detected = chardet.detect(sample)
        encoding = detected.get("encoding", "utf-8")
        return encoding if encoding else "utf-8"

    @classmethod
    def detect_delimiter(cls, file_content: str) -> str:
        """Sniff delimiter by testing which separator produces the most consistent column count."""
        lines = [line.strip() for line in file_content.splitlines() if line.strip()][:10]
        if not lines:
            return ","

        best_delimiter = ","
        max_consistent_cols = 0

        for sep in cls.SUPPORTED_DELIMITERS:
            col_counts = [len(line.split(sep)) for line in lines]
            # Check if all top lines have the same number of columns with this separator
            if len(set(col_counts)) == 1 and col_counts[0] > 1:
                if col_counts[0] > max_consistent_cols:
                    max_consistent_cols = col_counts[0]
                    best_delimiter = sep

        return best_delimiter

    @classmethod
    def load_dataframe_from_bytes(cls, file_bytes: bytes, filename: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Safely loads raw bytes into a Pandas DataFrame.
        Returns the DataFrame and a metadata dictionary about the file.
        """
        # Step 1: Detect Encoding
        encoding = cls.detect_encoding(file_bytes)

        # Step 2: Decode raw bytes to text safely
        try:
            text_content = file_bytes.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            text_content = file_bytes.decode("latin-1", errors="replace")
            encoding = "latin-1"

        # Step 3: Sniff Delimiter
        delimiter = cls.detect_delimiter(text_content)

        # Step 4: Parse with Pandas
        df = pd.read_csv(
            io.StringIO(text_content),
            sep=delimiter,
            encoding=encoding,
            skipinitialspace=True
        )

        metadata = {
            "filename": filename,
            "encoding": encoding,
            "delimiter": delimiter,
            "raw_size_bytes": len(file_bytes),
            "rows_loaded": len(df),
            "columns_loaded": len(df.columns)
        }

        return df, metadata