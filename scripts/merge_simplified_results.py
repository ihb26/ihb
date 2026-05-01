import glob
from pathlib import Path
from typing import Final

import click
import pandas as pd


DIR_DATA: Final[Path] = Path(__file__).parent.parent / "ihbenchmark-vis" / "data"
PATH_OUT: Final[Path] = DIR_DATA / "merged.parquet"


@click.command()
@click.option(
    "--force/--no-force",
    "-f/-nf",
    default=False,
    show_default=True,
    help="Overwrite the merged file if it already exists"
)
def main(force: bool) -> None:
    if PATH_OUT.exists() and (not force):
        print(f"Path {PATH_OUT} already exists and --force not set - skipping")
        return

    dfs: list[pd.DataFrame] = []
    for path_str in glob.glob(str(DIR_DATA / "*.csv")):
        if path_str.split("/")[-1].startswith("__"):
            print(f"Skipping: {path_str}")
            continue
        df = pd.read_csv(path_str)
        # Original System-User runs didn't have this column
        if "user_prompt_type" not in df.columns:
            df["user_prompt_type"] = df["attack_type"]
        dfs.append(df)
    df_full = pd.concat(dfs)
    df_full.to_parquet(PATH_OUT, index=False)


if __name__ == "__main__":
    main()
