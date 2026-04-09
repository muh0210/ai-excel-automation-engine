"""
VALIDATION LAYER — Central Data Validation Middleware
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Provides consistent validation for all modules:
  • DataFrame existence & shape checks
  • Column existence & type verification
  • Minimum row requirements
  • Consistent error reporting via ValidationError
"""

import pandas as pd


class ValidationError(Exception):
    """Raised when input data fails validation checks."""

    def __init__(self, message, context=None):
        self.context = context or {}
        super().__init__(message)


def validate_dataframe(df, name="DataFrame"):
    """Ensure df is a non-empty pandas DataFrame with at least one column."""
    if df is None:
        raise ValidationError(f"{name} is None — no data provided.")
    if not isinstance(df, pd.DataFrame):
        raise ValidationError(f"{name} is not a DataFrame (got {type(df).__name__}).")
    if df.empty:
        raise ValidationError(f"{name} is empty (0 rows).")
    if df.shape[1] == 0:
        raise ValidationError(f"{name} has no columns.")
    return True


def validate_columns_exist(df, columns, name="DataFrame"):
    """Verify that all requested columns exist in the DataFrame."""
    if isinstance(columns, str):
        columns = [columns]
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValidationError(
            f"Column(s) not found in {name}: {missing}",
            context={"missing": missing, "available": list(df.columns)},
        )
    return True


def validate_numeric_columns(df, columns, name="DataFrame"):
    """Verify that the specified columns are numeric."""
    validate_columns_exist(df, columns, name)
    if isinstance(columns, str):
        columns = [columns]
    non_numeric = [c for c in columns if not pd.api.types.is_numeric_dtype(df[c])]
    if non_numeric:
        raise ValidationError(
            f"Column(s) are not numeric in {name}: {non_numeric}",
            context={"non_numeric": non_numeric},
        )
    return True


def validate_min_rows(df, min_rows=5, name="DataFrame"):
    """Ensure the DataFrame has at least min_rows non-empty rows."""
    if len(df) < min_rows:
        raise ValidationError(
            f"{name} has only {len(df)} row(s), need at least {min_rows}.",
            context={"rows": len(df), "required": min_rows},
        )
    return True


def safe_validate(func):
    """
    Decorator that catches ValidationError and returns {'error': str} dict.

    Use on functions that need to return error dicts for the UI layer
    instead of raising exceptions.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as ve:
            return {"error": str(ve)}
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper
