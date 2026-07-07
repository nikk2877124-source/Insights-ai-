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


def test_analyze_data_types_classifies_columns():
    df = pd.DataFrame(
        {
            "Age": [30, 35, 40],
            "Salary": [1000.0, 2000.0, 3000.0],
            "Department": ["Sales", "HR", "IT"],
            "Active": [True, False, True],
            "JoiningDate": pd.to_datetime(["2020-01-01", "2020-02-01", "2020-03-01"]),
        }
    )

    result = ProfilingService().analyze_data_types(df)

    assert "Age" in result["numeric_columns"]
    assert "Salary" in result["numeric_columns"]
    assert "Department" in result["categorical_columns"]
    assert "Active" in result["boolean_columns"]
    assert "JoiningDate" in result["datetime_columns"]
    assert result["column_types"]["Age"] == "int64"


def test_analyze_statistics_uses_numeric_columns_only():
    df = pd.DataFrame({"Age": [10, 20, 30, None], "Name": ["A", "B", "C", "D"]})

    result = ProfilingService().analyze_statistics(df)

    assert "Age" in result
    assert "Name" not in result
    assert result["Age"]["count"] == 3
    assert result["Age"]["mean"] == 20.0


def test_analyze_memory_returns_bytes_and_mb():
    df = pd.DataFrame({"A": [1, 2, 3], "B": [1.5, 2.5, 3.5]})

    result = ProfilingService().analyze_memory(df)

    assert result["memory_usage_bytes"] > 0
    assert result["memory_usage_mb"] > 0


def test_detect_mixed_types_finds_mixed_value_columns():
    df = pd.DataFrame({"Age": [10, 12, "Unknown"]})

    result = ProfilingService().detect_mixed_types(df)

    assert result["mixed_type_columns"] == ["Age"]


def test_generate_profile_includes_iteration_3_sections():
    df = pd.DataFrame({"Age": [10, 20, 30], "Name": ["A", "B", "C"]})

    result = ProfilingService().generate_profile(df)

    assert "data_types" in result
    assert "statistics" in result
    assert "memory_usage" in result
    assert "mixed_types" in result


def test_detect_outliers_counts_values_outside_iqr_bounds():
    df = pd.DataFrame({"Salary": [100, 110, 120, 130, 1000]})

    result = ProfilingService().detect_outliers(df)

    assert result["Salary"]["outlier_count"] == 1
    assert result["total_outliers"] == 1


def test_calculate_quality_score_returns_grade_and_status():
    profile = {
        "missing_values": {"columns": {"Salary": {"percentage": 6.0}}},
        "duplicates": {"duplicate_percentage": 3.0},
        "mixed_types": {"mixed_type_columns": ["Name"]},
        "outliers": {"Salary": {"percentage": 2.0}},
        "basic_info": {"total_columns": 2},
        "data_types": {"object_columns": ["Name"]},
    }

    result = ProfilingService().calculate_quality_score(profile)

    assert result["score"] <= 100
    assert result["grade"] in {"A", "B", "C", "D", "F"}


def test_generate_dataset_health_handles_issues():
    profile = {
        "missing_values": {"columns": {"Salary": {"count": 2}}},
        "duplicates": {"duplicate_rows": 1},
        "mixed_types": {"mixed_type_columns": ["Age"]},
        "outliers": {"Salary": {"outlier_count": 1}},
    }

    result = ProfilingService().generate_dataset_health(profile)

    assert result["status"] in {"Good", "Fair", "Needs Attention"}
    assert len(result["major_issues"]) >= 1
