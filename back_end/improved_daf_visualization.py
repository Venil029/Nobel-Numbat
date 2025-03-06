import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import text

# Set better styling defaults for all plots
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12
plt.rcParams['legend.fontsize'] = 12
plt.rcParams['figure.titlesize'] = 18

# Use a colorblind-friendly palette
COLORS = {
    "PJL": "#0173B2",  # Blue
    "BEB": "#DE8F05"   # Orange
}

# Create a Blueprint for the DAF visualization routes
daf_bp = Blueprint('daf', __name__)

def get_snp_daf_data(snp_ids):
    """
    Retrieves DAF data for the specified SNPs for PJL and BEB populations.
    
    Args:
        snp_ids (list): List of SNP IDs to query.
    
    Returns:
        pandas.DataFrame: DataFrame with columns: SNP, Population, DAF.
    """
    # Convert list to string format for the SQL query
    snp_list_str = "', '".join(snp_ids)
    
    # SQL query to get DAF values for the specified SNPs.
    # Modify this query to match your actual database schema.
    query = text(f"""
        SELECT 
            snp_id AS SNP, 
            population AS Population, 
            daf_value AS DAF
        FROM 
            daf_results
        WHERE 
            snp_id IN ('{snp_list_str}')
            AND population IN ('PJL', 'BEB')
    """)
    
    try:
        # Execute the query (replace this dummy data with your actual query)
        # For example, if using SQLAlchemy's db.session:
        # result = db.session.execute(query)
        # data = [dict(row) for row in result]
        data = []
        for snp_id in snp_ids:
            # Generate realistic DAF values (typically between 0 and 1)
            pjl_daf = np.random.beta(2, 5)
            beb_daf = np.random.beta(2, 5)
            data.append({"SNP": snp_id, "Population": "PJL", "DAF": pjl_daf})
            data.append({"SNP": snp_id, "Population": "BEB", "DAF": beb_daf})
        return pd.DataFrame(data)
    
    except Exception as e:
        print(f"Database query error: {e}")
        return pd.DataFrame()

def get_available_snps():
    """Gets a list of all available SNPs in the database."""
    # For demonstration, using dummy data
    return [f"rs{i}" for i in range(10001, 10050)]

def generate_histogram(data, column, title=None, bins=15, kde=True, hue=None, palette=None):
    """
    Generate a histogram from the data with improved clarity.
    
    Returns:
        str: Base64 encoded image.
    """
    plt.figure(figsize=(12, 8))
    ax = plt.gca()
    
    if hue:
        if palette is None:
            palette = [COLORS["PJL"], COLORS["BEB"]]
        sns.histplot(
            data=data, 
            x=column, 
            hue=hue, 
            bins=bins, 
            kde=kde, 
            palette=palette,
            alpha=0.6,
            element="step",
            stat="density",
            common_norm=False
        )
        legend = plt.legend(title="Population", loc="upper right", frameon=True)
        legend.get_frame().set_facecolor('white')
        legend.get_frame().set_alpha(0.9)
    else:
        color = COLORS["PJL"] if "PJL" in data["Population"].unique() else COLORS["BEB"]
        sns.histplot(
            data=data, 
            x=column, 
            bins=bins, 
            kde=kde, 
            color=color,
            alpha=0.7,
            stat="density"
        )
        mean_val = data[column].mean()
        plt.axvline(x=mean_val, color='darkred', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.3f}')
        plt.legend(frameon=True)
    
    if title:
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Derived Allele Frequency (DAF)", fontsize=14, fontweight='bold')
    plt.ylabel("Density", fontsize=14, fontweight='bold')
    plt.xlim(0, 1)
    plt.grid(True, linestyle='--', alpha=0.7)
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.spines['left'].set_linewidth(1.5)
    ax.spines['bottom'].set_linewidth(1.5)
    plt.tick_params(axis='both', which='major', labelsize=12, width=1.5, length=6)
    if not hue:
        stats_text = (
            f"n = {len(data)}\n"
            f"Mean = {data[column].mean():.3f}\n"
            f"Median = {data[column].median():.3f}\n"
            f"Std Dev = {data[column].std():.3f}"
        )
        plt.annotate(stats_text, xy=(0.02, 0.98), xycoords='axes fraction',
                     bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="gray", alpha=0.8),
                     va='top', ha='left')
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close()
    buf.seek(0)
    img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img_str

# Blueprint routes
@daf_bp.route('/snp_daf', methods=['GET'])
def snp_daf_form():
    available_snps = get_available_snps()
    return render_template('snp_daf.html', available_snps=available_snps)

@daf_bp.route('/generate_daf_histogram', methods=['POST'])
def generate_daf_histogram():
    selected_snps = request.form.getlist('snps')
    if not selected_snps:
        return jsonify({"error": "No SNPs selected"}), 400
    daf_data = get_snp_daf_data(selected_snps)
    if daf_data.empty:
        return jsonify({"error": "No data available for selected SNPs"}), 404
    histograms = []
    for population in ["PJL", "BEB"]:
        pop_data = daf_data[daf_data["Population"] == population]
        if pop_data.empty:
            continue
        img_str = generate_histogram(
            data=pop_data, 
            column="DAF", 
            title=f"DAF Distribution for {population} Population",
            bins=15
        )
        histograms.append({"population": population, "image": img_str})
    combined_img_str = generate_histogram(
        data=daf_data, 
        column="DAF", 
        hue="Population", 
        title="DAF Distribution Comparison: PJL vs BEB",
        bins=15
    )
    snp_daf_figures = []
    for snp in selected_snps:
        snp_data = daf_data[daf_data["SNP"] == snp]
        if len(snp_data) < 2:
            continue
        plt.figure(figsize=(8, 6))
        ax = sns.barplot(data=snp_data, x="Population", y="DAF", palette=[COLORS["PJL"], COLORS["BEB"]], errorbar=None)
        for i, bar in enumerate(ax.patches):
            value = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2.0, value + 0.02, f'{value:.3f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
        avg_daf = daf_data["DAF"].mean()
        plt.axhline(y=avg_daf, color='darkred', linestyle='--', linewidth=1.5, alpha=0.7)
        plt.annotate(f'Average DAF: {avg_daf:.3f}', xy=(0.02, avg_daf + 0.02), xycoords=('axes fraction', 'data'), fontsize=10, color='darkred')
        plt.title(f"DAF Values for {snp}", fontsize=16, fontweight='bold', pad=20)
        plt.ylabel("Derived Allele Frequency (DAF)", fontsize=14, fontweight='bold')
        plt.xlabel("Population", fontsize=14, fontweight='bold')
        plt.ylim(0, min(1, max(snp_data["DAF"]) * 1.3))
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        curr_ax = plt.gca()
        curr_ax.spines['top'].set_visible(False)
        curr_ax.spines['right'].set_visible(False)
        curr_ax.spines['left'].set_linewidth(1.5)
        curr_ax.spines['bottom'].set_linewidth(1.5)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150)
        plt.close()
        buf.seek(0)
        snp_img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        snp_daf_figures.append({"snp": snp, "image": snp_img_str})
    return jsonify({
        "histograms": histograms,
        "combined": combined_img_str,
        "snp_figures": snp_daf_figures
    })
