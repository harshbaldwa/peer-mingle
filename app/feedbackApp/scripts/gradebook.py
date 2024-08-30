import pandas as pd


def create_gradebook(filepath):
    df = pd.read_csv(filepath)
    df = df.iloc[:, :4]
    df["dummy"] = ""
    df.loc[0, "dummy"] = "Manual Posting"
    df.to_csv(filepath, index=False)
