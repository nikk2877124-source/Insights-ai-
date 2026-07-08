import pandas as pd

from app.services.cleaning_session_service import _apply_operation


def test_apply_operation_uses_prompt_to_infer_mean_fill():
    df = pd.DataFrame({"age": [1, None, 3], "name": ["A", "B", "C"]})

    cleaned_df, metadata = _apply_operation(
        df,
        "",
        "fill missing values with mean in column=age",
    )

    assert cleaned_df["age"].isna().sum() == 0
    assert metadata["column"] == "age"
