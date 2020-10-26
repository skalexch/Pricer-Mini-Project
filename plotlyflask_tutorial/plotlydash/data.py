"""Prepare data for Plotly Dash."""
import pandas as pd
import numpy as np


def create_dataframe(path):
    """Create Pandas DataFrame from local CSV."""
    df = pd.read_csv(path)
    return df
