import pandas as pd

from app.services.profiling_service import ProfilingService


def test_analyze_missing_values_reports_counts_and_percentages():
    df = pd.DataFrame(
        {
            "Salary": [1000.0, None, 2000.0],
            "Age": [30, 25, None],
        }
    )

    result = ProfilingService().analyze_missing_values(df)

    assert result["total_missing_values"] == 2
    assert result["columns"]["Salary"]["count"] == 1
    assert result["columns"]["Salary"]["percentage"] == 33.3
    assert result["columns"]["Age"]["count"] == 1
    assert result["columns"]["Age"]["percentage"] == 33.3


def test_analyze_duplicates_reports_duplicate_rows_and_percentage():
    df = pd.DataFrame({"name": ["A", "A", "B", "C"]})

    result = ProfilingService().analyze_duplicates(df)

    assert result["duplicate_rows"] == 1
    assert result["duplicate_percentage"] == 25.0


def test_generate_profile_includes_missing_and_duplicate_sections():
    df = pd.DataFrame({"Product": ["A", "A", "A"], "Price": [10.0, None, 10.0]})

    result = ProfilingService().generate_profile(df)

    assert "basic_info" in result
    assert "missing_values" in result
    assert "duplicates" in result
    assert result["basic_info"]["total_rows"] == 3
    assert result["missing_values"]["total_missing_values"] == 1
    assert result["duplicates"]["duplicate_rows"] == 1


def test_empty_dataset_is_handled_safely():
    df = pd.DataFrame(columns=["City", "Score"])

    missing_result = ProfilingService().analyze_missing_values(df)
    duplicate_result = ProfilingService().analyze_duplicates(df)
    profile_result = ProfilingService().generate_profile(df)

    assert missing_result["total_missing_values"] == 0
    assert missing_result["columns"]["City"]["count"] == 0
    assert duplicate_result["duplicate_rows"] == 0
    assert duplicate_result["duplicate_percentage"] == 0.0
    assert profile_result["basic_info"]["total_rows"] == 0
