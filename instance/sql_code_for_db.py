#run this first to make template for tables

import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect("sql9.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")


# SQL script to create tables (use 'IF NOT EXISTS' to avoid errors)
sql_script = """CREATE TABLE snp (
    snp_id VARCHAR(20) PRIMARY KEY,
    risk_allele CHAR(50),
    chromosome VARCHAR(5),
    position INTEGER,
    p_value REAL,
    odds_ratio REAL,
    ci VARCHAR(20),
    trait VARCHAR(100),
    mapped_gene VARCHAR(50),
    study_accession VARCHAR(50),
    pubmed_id VARCHAR(20),
    beb VARCHAR(100),
    pjl VARCHAR(100),
    reference CHAR(1),
    ancestral CHAR(1),
    delta_af REAL,
    daf_beb REAL,
    daf_pjl REAL,
    phenotype VARCHAR(50),
    t2dkp_p_value REAL,
    beta REAL,
    fst_beb REAL,
    fst_pjl REAL
);
CREATE TABLE candidate_gene (
    gene_name VARCHAR(50) PRIMARY KEY
);
CREATE TABLE pathway (
    pathway_id VARCHAR(50) PRIMARY KEY,
    pathway_name VARCHAR(100)
);
CREATE TABLE snp_pathway (
    snp_id VARCHAR(20),
    pathway_id VARCHAR(50),
    PRIMARY KEY (snp_id, pathway_id),
    FOREIGN KEY (snp_id) REFERENCES snp(snp_id),
    FOREIGN KEY (pathway_id) REFERENCES pathway(pathway_id)
);
CREATE TABLE go_term (
    go_id VARCHAR(50) PRIMARY KEY,
    go_term VARCHAR(100)
);
CREATE TABLE snp_go (
    snp_id VARCHAR(20),
    go_id VARCHAR(50),
    PRIMARY KEY (snp_id, go_id),
    FOREIGN KEY (snp_id) REFERENCES snp(snp_id),
    FOREIGN KEY (go_id) REFERENCES go_term(go_id)
);
"""
# Execute the SQL script to create the tables
cursor.executescript(sql_script)

# Commit changes
conn.commit() 
conn.close()



#then run this to fill the tables with the data

import sqlite3
import pandas as pd

# Connect to SQLite database
conn = sqlite3.connect("sql9.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")


# Load Excel file
file_path = "data_sql_fst.xlsx"
df = pd.read_excel(file_path, sheet_name=None)  # Read all sheets

### 3️⃣ Insert Data into SNP Table ###
snp_data = df['snp']
snp_data = snp_data.fillna('')  # Replace NaN with empty strings

for _, row in snp_data.iterrows():
    cursor.execute("""
        INSERT INTO snp (
            snp_id, risk_allele, chromosome, position, p_value, odds_ratio, ci,
            trait, mapped_gene, study_accession, pubmed_id, beb, pjl, reference,
            ancestral, delta_af, daf_beb, daf_pjl, phenotype, t2dkp_p_value, beta, fst_beb, fst_pjl
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tuple(row))

### 4️⃣ Insert Data into Candidate Gene Table ###
gene_data = df['candidate_gene']
gene_data = gene_data.fillna('')
for gene in gene_data['gene_name']:
    cursor.execute("INSERT OR IGNORE INTO candidate_gene (gene_name) VALUES (?)", (gene,))

### 5️⃣ Insert Data into Pathway Table ###
pathway_data = df['pathway']
pathway_data = pathway_data.fillna('')
for _, row in pathway_data.iterrows():
    cursor.execute("INSERT OR IGNORE INTO pathway (pathway_id, pathway_name) VALUES (?, ?)", 
                   (row['pathway_id'], row['pathway_name']))

### 6️⃣ Insert Data into SNP-Pathway Table (Separate Loop) ###
snp_pathway_data = df['snp_pathway']
snp_pathway_data = snp_pathway_data.fillna('')
for _, row in snp_pathway_data.iterrows():
    cursor.execute("INSERT OR IGNORE INTO snp_pathway (snp_id, pathway_id) VALUES (?, ?)", 
                   (row['snp_id'], row['pathway_id']))

### 7️⃣ Insert Data into GO Term Table ###
go_data = df['go_term']
go_data = go_data.fillna('')
for _, row in go_data.iterrows():
    cursor.execute("INSERT OR IGNORE INTO go_term (go_id, go_term) VALUES (?, ?)", 
                   (row['go_id'], row['go_term']))

### 8️⃣ Insert Data into SNP-GO Table ###
snp_go_data = df['snp_go']
snp_go_data = snp_go_data.fillna('')
for _, row in snp_go_data.iterrows():
    cursor.execute("INSERT OR IGNORE INTO snp_go (snp_id, go_id) VALUES (?, ?)", 
                   (row['snp_id'], row['go_id']))

# Commit changes and close connection
conn.commit()
conn.close()

print("Data inserted successfully!")




#not necessary but if you want to check if data there, which as we now know is a good idea

import sqlite3
import pandas as pd

# Connect to SQLite database
conn = sqlite3.connect("sql9.db")
cursor = conn.cursor()

# Function to print first N rows of a table
def print_table(table_name, num_rows=5):
    print(f"\n🔹 First {num_rows} rows of {table_name}:")
    cursor.execute(f"SELECT * FROM {table_name} LIMIT {num_rows}")
    rows = cursor.fetchall()
    
    for row in rows:
        print(row)

# Print first few rows of each table
print_table("snp")
print_table("candidate_gene")
print_table("pathway")
print_table("snp_pathway")
print_table("go_term")
print_table("snp_go")

# Close connection
conn.commit()  # Save all changes
conn.close()
