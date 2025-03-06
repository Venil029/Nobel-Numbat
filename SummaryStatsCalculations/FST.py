import pandas as pd

# Load the CSV file
data = pd.read_csv('FINAL.csv')

# Function to parse allele frequencies from a string (handles missing values)
def parse_frequencies(freq_str):
    if pd.isna(freq_str) or not isinstance(freq_str, str):
        return {}
    try:
        return {allele_freq.split(':')[0].strip(): float(allele_freq.split(':')[1].strip()) 
                for allele_freq in freq_str.split(',')}
    except Exception as e:
        print(f"Error parsing frequencies: {freq_str} - {e}")
        return {}

# Function to calculate FST between two populations
def calculate_fst(p1, p2):
    """
    Calculate FST between two populations given their allele frequencies.
    """
    p_bar = (p1 + p2) / 2  
    h_s = (p1 * (1 - p1) + p2 * (1 - p2)) / 2  
    h_t = p_bar * (1 - p_bar)  

    if h_t == 0:  # Avoid division by zero
        return 0
    fst = (h_t - h_s) / h_t
    return fst

# List to store FST results
fst_values = []

# Process each row in the dataset
for _, row in data.iterrows():
    try:
        beb_freqs = parse_frequencies(row['BEB'])
        pjl_freqs = parse_frequencies(row['PJL'])

        for allele in beb_freqs:
            if allele in pjl_freqs:  # Only calculate FST if the allele is present in both populations
                fst = calculate_fst(beb_freqs[allele], pjl_freqs[allele])
                
                # Categorize genetic differentiation based on FST
                if fst < 0.05:
                    category = "Little genetic diff."
                elif 0.05 <= fst < 0.15:
                    category = "Moderate genetic diff."
                elif 0.15 <= fst < 0.25:
                    category = "Great genetic diff."
                else:
                    category = "Very great genetic diff."
                
                # Append the result
                fst_values.append({
                    'SNP ID': row['SNP ID'],
                    'Allele': allele,
                    'FST': round(fst, 5),  # Round for cleaner output
                    'Category': category
                })
    except Exception as e:
        print(f"Error processing SNP {row.get('SNP ID', 'Unknown')}: {e}")

# Convert results to a DataFrame
fst_df = pd.DataFrame(fst_values)

# Sort results in ascending order of FST
fst_df = fst_df.sort_values(by='FST', ascending=True)

# Save results to CSV
fst_df.to_csv('fst_results_sorted.csv', index=False)

print("FST calculation complete. Results saved to 'fst_results_sorted.csv'.")
