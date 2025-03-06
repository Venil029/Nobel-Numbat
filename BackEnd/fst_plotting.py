# fst_plotting.py 
#import matplotlib for creating plots, io to handle in-memory image files, base64 to encode images and pandas for handling data
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd

#function to create bar plot comparing FST values for BEB and PJL population
def plot_fst_comparison(df):
    """
    Plots a bar graph comparing mean FST values for PJL and BEB populations by chromosome.
    """
    plt.figure(figsize=(12, 6))
    x = df['Chromosome']
    width = 0.35  

    # Plot PJL data
    plt.bar(x - width/2, df['PJL_Mean_FST'], width, color='blue', alpha=0.5, label='PJL')
    
    # Plot BEB data
    plt.bar(x + width/2, df['BEB_Mean_FST'], width, color='orange', alpha=0.5, label='BEB')

    plt.xlabel("Chromosome")#x-axis label
    plt.ylabel("Mean FST")#y-axis label
    plt.title("Comparison of Mean FST Values for PJL and BEB Populations by Chromosome")#title of plot
    plt.legend(title="Population")#legend to differentiate between the two populations
    plt.xticks(df['Chromosome'])#tick labels define 
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)#add grid in background for readability
    
    img = io.BytesIO()#save the plot to an in memory buffer as PNG image
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()
    return base64.b64encode(img.getvalue()).decode('utf8')

#function to generate a dataframe containing FST data values for chromosomes 1-22
def get_fst_data():
    """
    Returns a DataFrame with hard-coded FST data for PJL and BEB populations.
    """
    data = [
        {"Chromosome": 1, "PJL_Mean_FST": 0.013465, "BEB_Mean_FST": 0.0186022727272727},
        {"Chromosome": 2, "PJL_Mean_FST": 0.018143, "BEB_Mean_FST": 0.035323},
        {"Chromosome": 3, "PJL_Mean_FST": 0.0159151428571429, "BEB_Mean_FST": 0.0248765714285714},
        {"Chromosome": 4, "PJL_Mean_FST": 0.0171753333333333, "BEB_Mean_FST": 0.0183413333333333},
        {"Chromosome": 5, "PJL_Mean_FST": 0.0165718181818182, "BEB_Mean_FST": 0.0171740909090909},
        {"Chromosome": 6, "PJL_Mean_FST": 0.01578, "BEB_Mean_FST": 0.0192},
        {"Chromosome": 7, "PJL_Mean_FST": 0.0162, "BEB_Mean_FST": 0.0201},
        {"Chromosome": 8, "PJL_Mean_FST": 0.0169, "BEB_Mean_FST": 0.0183},
        {"Chromosome": 9, "PJL_Mean_FST": 0.0175, "BEB_Mean_FST": 0.0197},
        {"Chromosome": 10, "PJL_Mean_FST": 0.0158, "BEB_Mean_FST": 0.0188},
        {"Chromosome": 11, "PJL_Mean_FST": 0.0162, "BEB_Mean_FST": 0.0195},
        {"Chromosome": 12, "PJL_Mean_FST": 0.0167, "BEB_Mean_FST": 0.0186},
        {"Chromosome": 13, "PJL_Mean_FST": 0.0157, "BEB_Mean_FST": 0.0189},
        {"Chromosome": 14, "PJL_Mean_FST": 0.0155, "BEB_Mean_FST": 0.0191},
        {"Chromosome": 15, "PJL_Mean_FST": 0.0160, "BEB_Mean_FST": 0.0193},
        {"Chromosome": 16, "PJL_Mean_FST": 0.0172, "BEB_Mean_FST": 0.0208},
        {"Chromosome": 17, "PJL_Mean_FST": 0.0165, "BEB_Mean_FST": 0.0201},
        {"Chromosome": 18, "PJL_Mean_FST": 0.0153, "BEB_Mean_FST": 0.0183},
        {"Chromosome": 19, "PJL_Mean_FST": 0.0179, "BEB_Mean_FST": 0.0204},
        {"Chromosome": 20, "PJL_Mean_FST": 0.0164, "BEB_Mean_FST": 0.0195},
        {"Chromosome": 21, "PJL_Mean_FST": 0.0155, "BEB_Mean_FST": 0.0181},
        {"Chromosome": 22, "PJL_Mean_FST": 0.0168, "BEB_Mean_FST": 0.0198}
    ]
    return pd.DataFrame(data) #convert the list into pandas dataframe 
