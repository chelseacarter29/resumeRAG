import pandas as pd 

def preprocess_data(input_file: str, output_file: str, data_size:int = 10) -> None:
    """
    Preprocess the input CSV file and save the cleaned data to the output CSV file.

    Parameters:
    - input_file: str - Path to the input CSV file.
    - output_file: str - Path to save the cleaned CSV file.
    """
    # Load the data
    df = pd.read_csv(input_file)

    # Drop duplicates
    df.drop_duplicates(inplace=True)

    # Handle missing values by filling them with the mean of the column
    df.fillna(df.mean(), inplace=True)

    df.head(data_size)

    # Save the cleaned data to a new CSV file
    df.to_csv(output_file, index=False)

