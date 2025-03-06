#import os to handle file paths, pandas to handle structured data, re to extract allele frequency data, matplotlib for plotting, 
#seaborn for statistical plots, io for in memory files, base64 to encode plots in website and sqlite3 to connect to database for queries
import os
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import sqlite3

# connect to the database
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "genetics.db")
conn = sqlite3.connect(db_path)#open connection to SQLite database

# load SNP data from database
query = "SELECT * FROM snp"
df = pd.read_sql_query(query, conn)
conn.close()

# clean column
df.columns = [col.strip().replace(" ", "_").lower() for col in df.columns]
#extract allele frequency data
def extract_frequency(allele_freq_str, allele):
    """
    Extracts the frequency of a given allele from a formatted string like 'A: 0.802, G: 0.198'.
    Returns None if not found.
    """
    try:
        match = re.findall(rf"{allele}:\s*([\d\.]+)", str(allele_freq_str))
        return float(match[0]) if match else None
    except Exception as e:
        print(f"Error extracting frequency: {e}")
        return None
#function to compute derived allele frequency 
def calculate_daf(row):
    """
    Computes the Derived Allele Frequency (DAF) for beb and pjl populations.
    Returns daf_beb and daf_pjl.
    """
    try:
        derived_allele = row["risk_allele"]
        beb_daf = extract_frequency(row["beb"], derived_allele)
        pjl_daf = extract_frequency(row["pjl"], derived_allele)
        return beb_daf, pjl_daf
    except Exception as e:
        print(f"Error processing SNP {row.get('snp_id', 'Unknown')}: {e}")
        return None, None

# Apply the DAF calculation to each row
df[["daf_beb", "daf_pjl"]] = df.apply(calculate_daf, axis=1, result_type="expand")
df["daf_beb"] = pd.to_numeric(df["daf_beb"], errors="coerce")
df["daf_pjl"] = pd.to_numeric(df["daf_pjl"], errors="coerce")

# Calculate the absolute difference (delta_af)
df["delta_af"] = abs(df["daf_beb"].fillna(0) - df["daf_pjl"].fillna(0))
df.loc[df["daf_beb"].isna() | df["daf_pjl"].isna(), "delta_af"] = None

# Define the correct order for chromosomes
chromosome_order = [str(i) for i in range(1, 23)] + ["X", "Y"]
df["chromosome"] = df["chromosome"].astype(str).str.strip()
df["chromosome"] = pd.Categorical(df["chromosome"], categories=chromosome_order, ordered=True)
#function to return processed data
def get_processed_data():
    """Returns the processed DataFrame."""
    return df
#function to plot histogram 
def plot_daf_histogram(df):
    df_filtered = df.dropna(subset=["daf_beb", "daf_pjl"])
    df_aggregated = df_filtered.groupby("chromosome").agg(
        daf_beb_mean=("daf_beb", "mean"),
        daf_pjl_mean=("daf_pjl", "mean")
    ).reset_index()
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df_aggregated, x="chromosome", y="daf_beb_mean", color="blue", alpha=0.5, label="beb")
    sns.barplot(data=df_aggregated, x="chromosome", y="daf_pjl_mean", color="orange", alpha=0.5, label="pjl")
    plt.xlabel("Chromosome")
    plt.ylabel("Mean Derived Allele Frequency (DAF)")
    plt.title("Mean daf_beb and daf_pjl by Chromosome")
    plt.legend(title="Population")
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode('utf8')
#fucntion to plot line chart
def plot_daf_line_chart(df):
    df_filtered = df.dropna(subset=["daf_beb", "daf_pjl"])
    df_aggregated = df_filtered.groupby("chromosome").agg(
        daf_beb_mean=("daf_beb", "mean"),
        daf_pjl_mean=("daf_pjl", "mean")
    ).reset_index()
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=df_aggregated, x="chromosome", y="daf_beb_mean", color="blue", label="beb", marker="o")
    sns.lineplot(data=df_aggregated, x="chromosome", y="daf_pjl_mean", color="orange", label="pjl", marker="o")
    plt.xlabel("Chromosome")
    plt.ylabel("Mean Derived Allele Frequency (DAF)")
    plt.title("Mean daf_beb and daf_pjl by Chromosome (Line Chart)")
    plt.legend(title="Population")
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode('utf8')
#function to plot bar chart
def plot_delta_af_bar_chart(df):
    df_filtered = df.dropna(subset=["delta_af"])
    df_aggregated = df_filtered.groupby("chromosome").agg(
        delta_af_mean=("delta_af", "mean")
    ).reset_index()
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df_aggregated, x="chromosome", y="delta_af_mean", color="green", alpha=0.5)
    plt.xlabel("Chromosome")
    plt.ylabel("Mean Absolute Difference in Allele Frequencies (ΔAF)")
    plt.title("Mean ΔAF by Chromosome")
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode('utf8')

def plot_pvalues_by_chromosome(df):
    """
    Plots p-values grouped by chromosome and annotates SNPs with p-value < 1e-58.
    """
    # Ensure the DataFrame has the required columns
    if not all(col in df.columns for col in ["chromosome", "p_value", "snp_id"]):
        raise ValueError("The database table does not contain the required columns ('chromosome', 'p_value', 'snp_id').")

    # Clean the chromosome column (remove spaces and ensure it's a string)
    df["chromosome"] = df["chromosome"].astype(str).str.strip()

    # Define the correct order for chromosomes
    chromosome_order = [str(i) for i in range(1, 23)] + ["X", "Y"]
    df["chromosome"] = pd.Categorical(df["chromosome"], categories=chromosome_order, ordered=True)

    # Sort the DataFrame by chromosome
    df = df.sort_values(by="chromosome")

    # Plot the p-values grouped by chromosome
    plt.figure(figsize=(16, 6))
    ax = sns.stripplot(
        data=df,
        x="chromosome",
        y="p_value",
        jitter=True,  # Add jitter for better visualization of overlapping points
        alpha=0.5,  # Make points semi-transparent
        palette="viridis",  # Use a color palette for better distinction
        s=6  # Adjust point size
    )

    # Customize the plot
    plt.xlabel("Chromosome")
    plt.ylabel("p-value")
    plt.title("p-values Grouped by Chromosome")
    plt.yscale("log")  # Use a log scale for the y-axis to better visualize small p-values

    # Highlight and annotate SNPs with p-value < 1e-58
    significant_snps = df[df["p_value"] < 1e-58]
    if not significant_snps.empty:
        sns.stripplot(
            data=significant_snps,
            x="chromosome",
            y="p_value",
            color="red",  
            jitter=True,
            alpha=1.0,  
            s=20,  
            ax=ax
        )

        # Annotate significant SNPs with their snp id
        for _, row in significant_snps.iterrows():
            chrom_pos = chromosome_order.index(row["chromosome"])
            ax.text(
                chrom_pos, 
                row["p_value"],  
                row["snp_id"],  
                fontsize=10,
                color="black",
                ha="center",
                va="bottom",
                bbox=dict(facecolor="yellow", alpha=0.5, edgecolor="black", boxstyle="round") 
            )

    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode('utf8')
