#calculate the delta allele frequency for BEB and PJL populations 
# import pandas library needed to handle the format of the csv data in python
import pandas as pd

# Load the dataset from a csv file containing derived allele frequency for BEB and PJL populations
df = pd.read_csv('deltaaf.csv', sep=',')

#remove any extra spaces to prevent errors 
df.columns = df.columns.str.strip()

# print the column names to confirm they have been loaded
print("Columns in the DataFrame:", df.columns)

# Calculate the delta allele frequencies between BEB and PJL populations
df['Delta_AF'] = abs(df['BEB'] - df['PJL'])

# Save the delta allele frequency values to Delta_AF_results.csv
df[['SNP_ID', 'BEB', 'PJL', 'Delta_AF']].to_csv("Delta_AF_results.csv", index=False)
