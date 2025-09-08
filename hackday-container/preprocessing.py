import os
import pandas as pd

def preprocess_data(input_file: str = "datasets/resume-dataset.csv", output_file: str  = "datasets/processed-resume-dataset.csv", data_size:int = 10) -> None:
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Preprocessing data from {input_file} and saving to {output_file}")

    # Load the data
    df = pd.read_csv(input_file)

    # Drop the 'Resume_html' column if it exists
    if 'Resume_html' in df.columns:
        df.drop(columns=['Resume_html'], inplace=True)

    print("Dropping dataset size")

    df.head(data_size)

    # Save the cleaned data to a new CSV file
    df.to_csv(output_file, index=False)

    print("Converted to CSV")

preprocess_data()