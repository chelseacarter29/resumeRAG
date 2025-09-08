import os
import pandas as pd

def preprocess_data(input_file: str = "datasets/resume-dataset.csv", output_file: str  = "datasets/processed-resume-dataset.csv", text_output_file: str = "datasets/processed-resume-dataset.txt", data_size:int = 25) -> None:
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Preprocessing data from {input_file} and saving to {output_file}")

    # Load the data
    df = pd.read_csv(input_file)

    # Print unique items in the 'Category' column
    if 'Category' in df.columns:
        unique_categories = df['Category'].unique()
        print("Unique categories:", unique_categories)
    else:
        print("Column 'Category' not found in the dataset.")

    # Drop the 'Resume_html' column if it exists
    if 'Resume_html' in df.columns:
        df.drop(columns=['Resume_html'], inplace=True)

    print("Dropping dataset size")

    # Filter the dataset for the category 'INFORMATION-TECHNOLOGY'
    df = df[df['Category'] == 'INFORMATION-TECHNOLOGY']
    print(f"Filtered dataset to {len(df)} entries with category 'INFORMATION-TECHNOLOGY'")
    df.head(data_size)


    # Extract Resume_str column into a text file
    if 'Resume_str' in df.columns:
        with open(text_output_file, 'w') as text_file:
            for idx, resume in enumerate(df['Resume_str'], start=1):
                text_file.write("START OF RESUME\n")
                text_file.write(f"name: person_{idx}\n")
                text_file.write(f"{resume}\n")
                text_file.write("END OF RESUME\n\n")
        print(f"Resumes extracted to {text_output_file}")
    else:
        print("Column 'Resume_str' not found in the dataset.")

    # Save the cleaned data to a new CSV file
    df.to_csv(output_file, index=False)

    print("Converted to CSV")



preprocess_data()