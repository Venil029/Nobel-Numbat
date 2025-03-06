import pandas as pd
import re

# 📂 Load the CSV dataset
file_path = r"C:\Users\VISHNU BELLIAPPA\Downloads\FINAL.csv"  # Update with your file path
df = pd.read_csv(file_path)

# 🔹 Clean column names (remove spaces)
df.columns = [col.strip().replace(" ", "_") for col in df.columns]

# 🔹 Function to extract allele frequencies from formatted strings
def extract_frequency(allele_freq_str, allele):
    """Extracts the frequency of a given allele from a formatted string like 'A: 0.802, G: 0.198'."""
    try:
        match = re.findall(rf"{allele}:\s*([\d\.]+)", str(allele_freq_str))
        return float(match[0]) if match else None
    except:
        return None

# 🎯 Function to Compute Derived Allele Frequency (DAF) for BEB and PJL
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

# 🔹 Apply DAF calculation function separately for BEB and PJL
df["DAF_BEB"], df["DAF_PJL"] = zip(*df.apply(calculate_daf, axis=1))

# 🛠 Save Updated File
output_path = r"C:\Users\VISHNU BELLIAPPA\Downloads\FINAL_with_DAF_BEB_PJL.csv"
df.to_csv(output_path, index=False)

# ✅ Print the first few rows to verify the results
print(df[["SNP_ID", "Risk_Allele", "DAF_BEB", "DAF_PJL"]].head())

# ✅ Display confirmation message
print(f"✅ Derived Allele Frequency (DAF) calculations completed successfully.")
print(f"📂 Updated file saved at: {output_path}")
