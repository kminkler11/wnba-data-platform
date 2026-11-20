from pathlib import Path

import pandas as pd

SEASON = "2026"

DATA_PATH = Path(
    f"data/processed/player_season_stats_{SEASON}.csv"
)


def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Processed dataset not found: {DATA_PATH}"
        )
    return pd.read_csv(DATA_PATH)


def test_unique_player_season():
    df = load_data()

    assert not df.duplicated(
        ["PLAYER_ID", "SEASON"]
    ).any(), "Duplicate player-season records found"


def test_no_missing_player_ids():
    df = load_data()

    assert df["PLAYER_ID"].notna().all(), (
        "Missing player IDs found"
    )


def test_no_negative_stats():
    df = load_data()

    columns = [
        "GP", "MIN", "PTS", "REB",
        "AST", "FGM", "FGA"
    ]

    assert (df[columns] >= 0).all().all(), (
        "Negative statistics found"
    )


def test_points_reconcile():
    df = load_data()

    calculated = (
        2 * (df["FGM"] - df["FG3M"])
        + 3 * df["FG3M"]
        + df["FTM"]
    )

    assert (calculated == df["PTS"]).all(), (
        "Point totals do not reconcile"
    )


def test_rebounds_reconcile():
    df = load_data()

    calculated = df["OREB"] + df["DREB"]

    assert (calculated == df["REB"]).all(), (
        "Rebound totals do not reconcile"
    )


def test_shooting_percentages():
    df = load_data()

    for made, attempted, pct in [
        ("FGM", "FGA", "FG_PCT"),
        ("FG3M", "FG3A", "FG3_PCT"),
        ("FTM", "FTA", "FT_PCT")
    ]:
        expected = (
            df[made] /
            df[attempted].replace(0, float("nan"))
        ).fillna(0)

        assert (
            (df[pct] - expected).abs() < 0.000001
        ).all(), f"{pct} does not reconcile"
