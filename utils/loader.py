"""
MODULE 1: DATA LOADER
━━━━━━━━━━━━━━━━━━━━━
Handles file upload, format detection, sheet selection, and initial preview.
Supports .xlsx, .xls, and .csv files with robust error handling.
"""

import pandas as pd
import os


def load_file(file):
    """
    Load an Excel or CSV file and return the dataframe with metadata.

    Args:
        file: Streamlit UploadedFile object or file path string

    Returns:
        dict: {
            'dataframe': pd.DataFrame,
            'shape': tuple,
            'columns': list,
            'dtypes': dict,
            'sheet_names': list or None,
            'file_name': str,
            'file_size_kb': float
        }
    """
    try:
        # Determine file name and extension
        if hasattr(file, 'name'):
            file_name = file.name
            file_size_kb = round(file.size / 1024, 2)
        else:
            file_name = os.path.basename(str(file))
            file_size_kb = round(os.path.getsize(str(file)) / 1024, 2)

        ext = os.path.splitext(file_name)[1].lower()

        # Load based on extension
        if ext in ['.xlsx', '.xls']:
            xls = pd.ExcelFile(file)
            sheet_names = xls.sheet_names
            # Load first sheet by default
            df = pd.read_excel(xls, sheet_name=sheet_names[0])
        elif ext == '.csv':
            df = pd.read_csv(file)
            sheet_names = None
        else:
            raise ValueError(f"Unsupported file format: {ext}. Please upload .xlsx, .xls, or .csv files.")

        return {
            'dataframe': df,
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'sheet_names': sheet_names,
            'file_name': file_name,
            'file_size_kb': file_size_kb
        }

    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error loading file: {str(e)}")


def load_specific_sheet(file, sheet_name):
    """Load a specific sheet from an Excel file."""
    try:
        df = pd.read_excel(file, sheet_name=sheet_name)
        return df
    except Exception as e:
        raise RuntimeError(f"Error loading sheet '{sheet_name}': {str(e)}")


def get_file_preview(df, n_rows=5):
    """Get a quick preview of the dataframe."""
    return {
        'head': df.head(n_rows),
        'shape': df.shape,
        'memory_usage_kb': round(df.memory_usage(deep=True).sum() / 1024, 2),
        'null_counts': df.isnull().sum().to_dict(),
        'numeric_columns': list(df.select_dtypes(include='number').columns),
        'categorical_columns': list(df.select_dtypes(include=['object', 'category']).columns),
        'datetime_columns': list(df.select_dtypes(include='datetime').columns)
    }
