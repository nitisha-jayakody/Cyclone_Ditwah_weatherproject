import pandas as pd
from pathlib import Path

def load_all(data_dir: str | Path) -> pd.DataFrame:
    """
    Loads all city weather CSV files from the directory into a single DataFrame.
    
    Args:
        data_dir: Path to the directory containing the '*_weather.csv' files.
        
    Returns:
        A tidy pandas DataFrame with all cities' data and a new 'city' column.
        
    Raises:
        FileNotFoundError: If the directory is missing or contains no CSVs.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Directory not found: {data_dir}")
        
    csv_files = list(data_path.glob("*_weather.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No '*_weather.csv' files found in {data_dir}")
        
    df_list = []
    for file in csv_files:
        df = pd.read_csv(file)
        # Extract city name from filename (e.g., 'dankotuwa' from 'dankotuwa_weather.csv')
        df['city'] = file.stem.replace("_weather", "").capitalize()
        df_list.append(df)
        
    combined_df = pd.concat(df_list, ignore_index=True)
    
    if 'date' in combined_df.columns:
        combined_df['date'] = pd.to_datetime(combined_df['date'])
        
    return combined_df