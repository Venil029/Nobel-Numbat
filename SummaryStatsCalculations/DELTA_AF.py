import pandas as pd

# Load the CSV file from stats.csv
df = pd.read_csv('deltaaf.csv', sep=',')  # Make sure to use the correct separator if needed

# Strip whitespace from column names
df.columns = df.columns.str.strip()

# Check the columns to ensure correct names
print("Columns in the DataFrame:", df.columns)

# Calculate the absolute difference in allele frequencies (ΔAF)
# Use the correct column names based on your provided data
df['Delta_AF'] = abs(df['BEB'] - df['PJL'])

# Save the ΔAF values to a CSV file
df[['SNP_ID', 'BEB', 'PJL', 'Delta_AF']].to_csv("Delta_AF_results.csv", index=False)

# Define a function to classify selection based on Delta_AF values
def classify_selection(delta_af):
    if delta_af > 0.1:  # You can adjust this threshold as needed
        return 'Positive Selection'
    elif delta_af < -0.1:  # You can adjust this threshold as needed
        return 'Negative Selection'
    else:
        return 'No Selection'

# Apply the classification function to create a new column
df['Selection Type'] = df['Delta_AF'].apply(classify_selection)

# Filter for positive Delta_AF values
positive_values = df[df['Delta_AF'] > 0]

# Save the positive values with selection types to a new CSV file
if not positive_values.empty:
    positive_values.to_csv('positive_delta_af_values_with_selection.csv', index=False)
    print("Positive values with selection types have been saved to 'positive_delta_af_values_with_selection.csv'.")
else:
    print("There are no positive values in Delta_AF.")
