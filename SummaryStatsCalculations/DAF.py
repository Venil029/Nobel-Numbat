#import pandas for handling data and re module for pattern matching
import pandas as pd
import re

# Load the dataset from final csv
file_path = r"final.csv"  
df = pd.read_csv(file_path)

# clean the column names by removing white spaces
df.columns = [col.strip().replace(" ", "_") for col in df.columns]

# extract the allele frequency from the table format
def extract_frequency(allele_freq_str, allele):
    """Extracts the frequency of a given allele from a formatted string like 'A: 0.802, G: 0.198'."""
    try:
        match = re.findall(rf"{allele}:\s*([\d\.]+)", str(allele_freq_str))
        return float(match[0]) if match else None
    except:
        return None

# function to calculate derived allele frequency for BEB and PJL populations
def calculate_daf(row):
    try:
        derived_allele = row["Risk_Allele"]  # Risk allele is considered derived

        # Extract derived allele frequency for each population
        BEB_daf = extract_frequency(row["BEB"], derived_allele)
        PJL_daf = extract_frequency(row["PJL"], derived_allele)

        return BEB_daf, PJL_daf  # Return DAF values separately
    except Exception as e:
        print(f"Error processing SNP {row['SNP_ID']}: {e}")
        return None, None

# apply calculation for each row
df["DAF_BEB"], df["DAF_PJL"] = zip(*df.apply(calculate_daf, axis=1))

# save the calculations to csv file format
output_path = r"FINAL_with_DAF_BEB_PJL.csv"
df.to_csv(output_path, index=False)

# print the first few rows of results to check calculation has worked
print(df[["SNP_ID", "Risk_Allele", "DAF_BEB", "DAF_PJL"]].head())

