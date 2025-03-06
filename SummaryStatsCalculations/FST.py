import pandas as pd

# This loads the CSV file which contains the required population genetic data which includes the SNP ID and two populations and their allele frequency
data = pd.read_csv('DATA.csv')

# Function to parse allele frequencies from a string representation as well as returning a dictionary connecting the alleles to their frequencies
def parse_frequencies(freq_str):
    if pd.isna(freq_str) or not isinstance(freq_str, str):
        return {}
    try:
        return {allele_freq.split(':')[0].strip(): float(allele_freq.split(':')[1].strip()) 
                for allele_freq in freq_str.split(',')}
    except Exception as e:
        print(f"Error parsing frequencies: {freq_str} - {e}")
        return {}

#This function calculates the FST between the two populations using the formula FST = (HT - HS)/HT
def calculate_fst(p1, p2):
    p_bar = (p1 + p2) / 2  #This takes the average allele frequency 
    h_s = (p1 * (1 - p1) + p2 * (1 - p2)) / 2  #This takes the average heterozygosity within the popualation
    h_t = p_bar * (1 - p_bar) #This provides the total heterozygosity

    if h_t == 0:  #This avoids division by zero, paticularly when the allele is fixed
        return 0
    fst = (h_t - h_s) / h_t
    return fst

#This list stores FST results
fst_values = []

#This iterates through each shared SNP in the data set and calculates the FST by employing the calculate_fst function 
for _, row in data.iterrows():
    try:
        #This parses the allele frequencies of the populations which were Europe and Punjabi Lahore however for PJL was switched out for Bengali population for their calculation
        eur_freqs = parse_frequencies(row['EUR'])
        pjl_freqs = parse_frequencies(row['PJL'])
#This uses the calculate_fst function for each shared allele, however it is only calculates the FST if the allele is present in both populations
        for allele in eur_freqs:
            if allele in pjl_freqs:  # Only calculate FST if the allele is present in both populations
                fst = calculate_fst(eur_freqs[allele], pjl_freqs[allele])
                
                # This categorises the genetic differentiation based on FST thresholds as described by Wrights interpretation guidlines 
                if fst < 0.05:
                    category = "Little genetic diff."
                elif 0.05 <= fst < 0.15:
                    category = "Moderate genetic diff."
                elif 0.15 <= fst < 0.25:
                    category = "Great genetic diff."
                else:
                    category = "Very great genetic diff."
                
                # This stores the results
                fst_values.append({
                    'SNP ID': row['SNP ID'],
                    'Allele': allele,
                    'FST': round(fst, 5),  
                    'Category': category
                })
    except Exception as e:
        print(f"Error processing SNP {row.get('SNP ID', 'Unknown')}: {e}")

# This converts results to a dataFrame
fst_df = pd.DataFrame(fst_values)

# This saves the results to CSV
fst_df.to_csv('Output.csv', index=False)
