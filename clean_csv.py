#reads in csv file and 
import pandas as pd

input_file = "in/test.csv"
title_column = "Title"
desc_column = "Description"

df = pd.read_csv(input_file, dtype=str)

df[title_column] = df[title_column].str.replace(r"[\r\n]+", " ", regex=True)
df[desc_column] = df[desc_column].str.replace(r"[\r\n]+", " ", regex=True)

df.to_csv(input_file[:-4] + '_cleaned.csv', index=False)