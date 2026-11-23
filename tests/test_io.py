import pytest
import pandas as pd
from ditwah_weather.io import load_all

def test_load_all_success(tmp_path):
    dankotuwa_file = tmp_path / "dankotuwa_weather.csv"
    colombo_file = tmp_path / "colombo_weather.csv"
    nuwara_file = tmp_path / "nuwara_eliya_weather.csv"

    dankotuwa_file.write_text("date,precipitation_sum,temperature_2m_max\n2025-11-26,100.5,30.0\n")
    colombo_file.write_text("date,precipitation_sum,temperature_2m_max\n2025-11-26,80.0,31.0\n")
    nuwara_file.write_text("date,precipitation_sum,temperature_2m_max\n2025-11-26,90.0,20.0\n")

    df = load_all(tmp_path)

    assert len(df) == 3
    assert "city" in df.columns
    assert set(df["city"].unique()) == {"Dankotuwa", "Colombo", "Nuwara Eliya"}
    assert pd.api.types.is_datetime64_any_dtype(df["date"])

def test_load_all_no_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_all(tmp_path)