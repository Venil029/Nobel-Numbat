# ------------------ Import all necessary packages ------------------
import os
import pandas as pd
import re
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import sqlite3
import plotly.express as px
from flask import Flask, render_template, render_template_string, request, flash, redirect, url_for, Response, jsonify, abort, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import text  
from sqlalchemy.orm import joinedload

# Import FST plotting functions from a separate module
from fst_plotting import plot_fst_comparison, get_fst_data

# ------------------ INITIALIZE FLASK APP ------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "genetics.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
os.makedirs("instance", exist_ok=True)

# ------------------ INITIALIZE EXTENSIONS ------------------
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ------------------ Database model ------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
# ------------------ Existing association table for pathways ------------------
snp_pathway_table = db.Table('snp_pathway',
    db.Column('snp_id', db.String, db.ForeignKey('snp.snp_id')),
    db.Column('pathway_id', db.String, db.ForeignKey('pathway.pathway_id'))
)
# ---------- Association table for SNPs and GO Terms ----------
snp_go_table = db.Table('snp_go',
    db.Column('snp_id', db.String, db.ForeignKey('snp.snp_id')),
    db.Column('go_id', db.String, db.ForeignKey('go_term.go_id'))
)
# ---------- Table name is "snp" in lowercase and Gene information stored here  --------------
class GeneticData(db.Model):
    __tablename__ = "snp"  
    snp_id = db.Column(db.String, primary_key=True)
    risk_allele = db.Column(db.String)
    chromosome = db.Column(db.String)
    position = db.Column(db.Integer)
    p_value = db.Column(db.Float)
    odds_ratio = db.Column(db.Float)
    ci = db.Column(db.String)
    trait = db.Column(db.String)
    mapped_gene = db.Column(db.String)  
    study_accession = db.Column(db.String)
    pubmed_id = db.Column(db.String)
    beb = db.Column(db.String)
    pjl = db.Column(db.String)
    reference = db.Column(db.String)
    ancestral = db.Column(db.String)
    delta_af = db.Column(db.Float)
    daf_beb = db.Column(db.Float)
    daf_pjl = db.Column(db.Float)
    phenotype = db.Column(db.String)
    t2dkp_p_value = db.Column(db.Float)
    beta = db.Column(db.Float)
    fst_beb = db.Column(db.Float)  
    fst_pjl = db.Column(db.Float)  
    
    # ---------- Relationship for pathways ----------
    pathways = db.relationship('Pathway', secondary=snp_pathway_table, backref="associated_snps", lazy=True)
    # ---------- Relationship for GO Terms ----------
    go_terms = db.relationship('GOTerm', secondary=snp_go_table, backref="associated_snps", lazy=True)


# ---------- Pathway model for database ----------
class Pathway(db.Model):
    __tablename__ = "pathway"
    pathway_id = db.Column(db.String, primary_key=True)
    pathway_name = db.Column(db.String)

# ---------- GOTerm model for GO Terms ----------
class GOTerm(db.Model):
    __tablename__ = "go_term"
    go_id = db.Column(db.String(50), primary_key=True)
    go_term = db.Column(db.String(100), nullable=False)

# ------------------ Helper function for GO term information ------------------
def get_go_terms(snp_id):
    """
    Returns a list of GO term descriptions for the given snp_id by joining the
    snp_go and go_term tables.
    """
    stmt = text("""
        SELECT g.go_term 
        FROM snp_go sg
        JOIN go_term g ON sg.go_id = g.go_id
        WHERE sg.snp_id = :snp_id
    """)
    result = db.session.execute(stmt, {"snp_id": snp_id}).fetchall()
    return [row[0] for row in result]

# ---------- Register the helper as a template global so it can be used in Jinja templates ---------------
app.jinja_env.globals.update(get_go_terms=get_go_terms)

# ------------------ Loads the user ------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------ app routes ------------------
@app.route('/')
def home():
    return render_template('home.html')
# ------------------ allows user to create a profile ------------------
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')
# ------------------ allows user to log out  ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        flash(' Invalid email or password.', 'danger')
    return render_template('login.html')
# ------------------ allows user to register  ------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            flash(' An account with this email or username already exists.', 'warning')
            return redirect(url_for('register'))
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash(' Your account has been created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')
# ------------------ allows user to log out ------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(' You have logged out!', 'info')
    return redirect(url_for('home'))

# ------------------ code for the search route ------------------
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    results = []
    if query:
        results = GeneticData.query.options(joinedload(GeneticData.go_terms)).filter(
            GeneticData.snp_id.ilike(f"%{query}%")
        ).all()
        if results:
            flash(f" Found {len(results)} result(s) for '{query}'.", "success")
        else:
            flash(f" No results found for '{query}'.", "danger")
    return render_template('search_results.html', results=results, query=query)
    
# ------------------ contains app routes for connection of database ------------------

@app.route('/genetic_data', methods=['GET'], endpoint='genetic_data_search')
def genetic_data_search():
    query = request.args.get('query', '').strip()
    results = []
    if query:
        if query.isdigit():
            results = GeneticData.query.options(joinedload(GeneticData.go_terms)).filter(
                (GeneticData.chromosome == query) | (GeneticData.position == int(query))
            ).all()
        elif len(query) == 1:
            results = GeneticData.query.options(joinedload(GeneticData.go_terms)).filter(
                GeneticData.risk_allele.ilike(query)
            ).all()
        else:
            results = GeneticData.query.options(joinedload(GeneticData.go_terms)).filter(
                (GeneticData.snp_id.ilike(f"%{query}%")) |
                (GeneticData.risk_allele.ilike(f"%{query}%")) |
                (GeneticData.mapped_gene.ilike(f"%{query}%"))
            ).all()
        if results:
            flash(f" Found {len(results)} result(s) for '{query}'.", "success")
        else:
            flash(f" No results found for '{query}'.", "danger")
    return render_template('genetic_data.html', results=results, query=query)
# ------------------ connects about subpage ------------------
@app.route('/about')
def about():
    return render_template('about.html')
# ------------------ connects populations subpage ------------------
@app.route('/populations')
def populations():
    return render_template('populations.html')
# ------------------ connects information on the bangladeshi population to the populations page ------------------
@app.route('/populations/bangladesh')
def bangladesh():
    return render_template('bangladesh.html')
# ------------------ connects information on the pakistani population to the populations page ------------------
@app.route('/populations/pakistan')
def pakistan():
    return render_template('pakistan.html')
# ------------------ connects the data visuliation page ------------------
@app.route('/data_options')
def data_options():
    return render_template('data_options.html')

# ------------------ Delta allele frequency visualisation route ------------------
@app.route('/delta_af')
def delta_af_view():
    try:
        conn = sqlite3.connect(db_path)
        query = "SELECT chromosome, delta_af, position, snp_id FROM snp"
        df = pd.read_sql(query, conn)
        conn.close()
    except Exception as e:
        return abort(500, description=f"Error fetching data: {e}")
    
    if df.empty:
        flash("No data available for Delta_AF plots.", "warning")
        return render_template("delta_af_viz.html", manhattan_html="<p>No data available.</p>", boxplot_html="<p>No data available.</p>")
    
    df['chromosome'] = df['chromosome'].astype(str)
    manhattan_fig = px.scatter(
        df, 
        x="position", 
        y="delta_af", 
        color="chromosome",
        hover_data=["snp_id"],
        title="Manhattan Plot of Delta_AF",
        labels={"delta_af": "Delta_AF", "position": "Genomic Position"}
    )
    boxplot_fig = px.box(
        df, 
        x="chromosome", 
        y="delta_af", 
        title="Delta_AF Distribution Across Chromosomes",
        labels={"delta_af": "Delta_AF", "chromosome": "Chromosome"}
    )
    manhattan_html = manhattan_fig.to_html(full_html=False)
    boxplot_html = boxplot_fig.to_html(full_html=False)
    return render_template("delta_af_viz.html", manhattan_html=manhattan_html, boxplot_html=boxplot_html)

# ------------------ BEB/PJL (DAF Comparison) visualisation route ------------------
@app.route('/beb_pjl')
def beb_pjl_view():
    return render_template('beb_pjl_view.html')

# ------------------ FST visualisation route ------------------
@app.route('/fst_view')
def fst_view():
    try:
        results = GeneticData.query.with_entities(
            GeneticData.chromosome,
            GeneticData.fst_beb,
            GeneticData.fst_pjl,
            GeneticData.snp_id,
            GeneticData.position
        ).all()
    except Exception as e:
        return abort(500, description=f"Error fetching FST data: {e}")
    
    df = pd.DataFrame(results, columns=["chromosome", "fst_beb", "fst_pjl", "snp_id", "position"])
    if df.empty:
        flash("No data available for FST plots.", "warning")
        return render_template("fst_view.html", fst_scatter_html="<p>No data available.</p>", fst_box_html="<p>No data available.</p>")
    
    df['chromosome'] = df['chromosome'].astype(str)
    fst_scatter_fig = px.scatter(
        df,
        x="position",
        y="fst_beb",
        color="chromosome",
        hover_data=["snp_id"],
        title="FST (BEB) by Genomic Position",
        labels={"fst_beb": "FST (BEB)", "position": "Genomic Position"}
    )
    fst_box_fig = px.box(
        df,
        x="chromosome",
        y="fst_pjl",
        title="FST (PJL) Distribution by Chromosome",
        labels={"fst_pjl": "FST (PJL)", "chromosome": "Chromosome"}
    )
    fst_scatter_html = fst_scatter_fig.to_html(full_html=False)
    fst_box_html = fst_box_fig.to_html(full_html=False)
    return render_template("fst_view.html", fst_scatter_html=fst_scatter_html, fst_box_html=fst_box_html)

# ------------------ summary stats visualisation ------------------
@app.route('/summary_stats')
def summary_stats_view():
    import Flask_derive_delta as fdd
    data = fdd.get_processed_data()
    histogram_plot = fdd.plot_daf_histogram(data)
    line_chart_plot = fdd.plot_daf_line_chart(data)
    delta_af_plot = fdd.plot_delta_af_bar_chart(data)
    pvalue_plot = fdd.plot_pvalues_by_chromosome(data)
    # Generate FST comparison plot using the hard-coded data from the separate module
    fst_comparison_plot = plot_fst_comparison(get_fst_data())
    return render_template('summary_stats_view.html',
                           histogram_plot=histogram_plot,
                           line_chart_plot=line_chart_plot,
                           delta_af_plot=delta_af_plot,
                           pvalue_plot=pvalue_plot,
                           fst_comparison_plot=fst_comparison_plot)

# ------------------ FST API endpoints ------------------
@app.route('/api/populations')
def api_populations():
    # FST visualisation for BEB and PJL
    return jsonify(["BEB", "PJL"])

@app.route('/api/snps/<population>')
def api_snps(population):
    population = population.upper()
    if population == "BEB":
        snps = GeneticData.query.filter(GeneticData.fst_beb.isnot(None)).with_entities(GeneticData.snp_id).all()
    elif population == "PJL":
        snps = GeneticData.query.filter(GeneticData.fst_pjl.isnot(None)).with_entities(GeneticData.snp_id).all()
    else:
        return jsonify({"error": "Invalid population"}), 400
    snp_list = [s[0] for s in snps]
    return jsonify(snp_list)

@app.route('/api/top_snps/<population>/<int:count>')
def api_top_snps(population, count):
    population = population.upper()
    if population == "BEB":
        query_obj = GeneticData.query.filter(GeneticData.fst_beb.isnot(None)).order_by(GeneticData.fst_beb.desc()).limit(count)
    elif population == "PJL":
        query_obj = GeneticData.query.filter(GeneticData.fst_pjl.isnot(None)).order_by(GeneticData.fst_pjl.desc()).limit(count)
    else:
        return jsonify({"error": "Invalid population"}), 400
    results = query_obj.all()
    result_list = []
    for r in results:
        fst_val = r.fst_beb if population == "BEB" else r.fst_pjl
        if fst_val is None:
            category = "No data"
        else:
            if fst_val < 0.05:
                category = "Little genetic diff."
            elif fst_val < 0.15:
                category = "Moderate genetic diff."
            elif fst_val < 0.25:
                category = "Great genetic diff."
            else:
                category = "Very great genetic diff."
        result_list.append({
            "SNP ID": r.snp_id,
            "FST": fst_val if fst_val is not None else 0,
            "Category": category,
            "Allele": r.risk_allele
        })
    return jsonify(result_list)

@app.route('/api/fst_data', methods=['POST'])
def api_fst_data():
    data = request.json
    population = data.get("population", "").upper()
    selected_snps = data.get("snps", [])
    if population not in ["BEB", "PJL"]:
        return jsonify({"error": "Invalid population"}), 400
    results = GeneticData.query.filter(GeneticData.snp_id.in_(selected_snps)).all()
    result_list = []
    for r in results:
        fst_val = r.fst_beb if population == "BEB" else r.fst_pjl
        if fst_val is None:
            category = "No data"
        else:
            if fst_val < 0.05:
                category = "Little genetic diff."
            elif fst_val < 0.15:
                category = "Moderate genetic diff."
            elif fst_val < 0.25:
                category = "Great genetic diff."
            else:
                category = "Very great genetic diff."
        result_list.append({
            "SNP ID": r.snp_id,
            "FST": fst_val if fst_val is not None else 0,
            "Category": category,
            "Allele": r.risk_allele
        })
    result_list = sorted(result_list, key=lambda x: x["FST"], reverse=True)
    return jsonify(result_list)

# ------------------ DAF API route ------------------
@app.route('/api/daf-data/<chromosome>', methods=['GET'])
def api_daf_data(chromosome):
    results = GeneticData.query.filter_by(chromosome=chromosome).all()
    if not results:
        return jsonify({"data": [], "summary": {}, "top_differences": []})
    data_list = []
    for row in results:
        daf_beb = row.daf_beb if row.daf_beb is not None else 0
        daf_pjl = row.daf_pjl if row.daf_pjl is not None else 0
        diff = abs(daf_beb - daf_pjl)
        data_list.append({
            "SNP_ID": row.snp_id,
            "Position": row.position,
            "Risk_Allele": row.risk_allele,
            "DAF_BEB": daf_beb,
            "DAF_PJL": daf_pjl,
            "difference": diff,
            "higher_in": "BEB" if daf_beb > daf_pjl else "PJL"
        })
    df_api = pd.DataFrame(data_list)
    summary = {
         "count": int(df_api.shape[0]),
         "avg_daf_beb": float(df_api["DAF_BEB"].mean()),
         "avg_daf_pjl": float(df_api["DAF_PJL"].mean()),
         "mean_difference": float(df_api["difference"].mean()),
         "higher_in_beb": int((df_api["DAF_BEB"] > df_api["DAF_PJL"]).sum()),
         "higher_in_pjl": int((df_api["DAF_BEB"] <= df_api["DAF_PJL"]).sum())
    }
    top_differences = df_api.sort_values(by='difference', ascending=False).head(5).to_dict(orient='records')
    return jsonify({"data": data_list, "summary": summary, "top_differences": top_differences})

# ------------------ allows user to download snps ------------------
@app.route('/download/<snp_id>')
def download_snp(snp_id):
    snp = GeneticData.query.get(snp_id)
    if not snp:
        flash("SNP not found.", "danger")
        return redirect(url_for('search'))
    content = (
        f"rsID: {snp.snp_id}\n"
        f"Risk Allele: {snp.risk_allele}\n"
        f"Gene: {snp.mapped_gene if snp.mapped_gene else '-'}\n"
        f"Trait: {snp.trait}\n"
        f"Phenotype: {snp.phenotype if snp.phenotype else '-'}\n"
        f"T2DKP P-value: {snp.t2dkp_p_value if snp.t2dkp_p_value is not None else '-'}\n"
        f"Beta: {snp.beta if snp.beta is not None else '-'}\n"
        f"P-Value: {snp.p_value}\n"
        f"Odds Ratio: {snp.odds_ratio}\n"
        f"delta_af: {snp.delta_af if snp.delta_af is not None else '-'}\n"
        f"daf_beb: {snp.daf_beb if snp.daf_beb is not None else '-'}\n"
        f"daf_pjl: {snp.daf_pjl if snp.daf_pjl is not None else '-'}\n"
        f"fst_beb: {snp.fst_beb if snp.fst_beb is not None else '-'}\n"
        f"fst_pjl: {snp.fst_pjl if snp.fst_pjl is not None else '-'}\n"
        f"Study Accession: {snp.study_accession}\n"
        f"PubMed ID: {snp.pubmed_id}\n"
    )
    # Existing pathway information
    if snp.pathways:
        pathway_lines = "\n".join([f" - {p.pathway_id}: {p.pathway_name}" for p in snp.pathways])
        content += f"Pathways:\n{pathway_lines}\n"
    else:
        content += "Pathways: -\n"
    
    # Include GO Term information
    go_terms = get_go_terms(snp.snp_id)
    if go_terms:
        content += "GO Terms:\n" + "\n".join([f" - {term}" for term in go_terms]) + "\n"
    else:
        content += "GO Terms: -\n"
    
    content += (
        "\nSummary Statistics:\n"
        f"SNP: {snp.snp_id}\n"
        f"delta_af: {snp.delta_af if snp.delta_af is not None else '-'}\n"
        f"daf_beb: {snp.daf_beb if snp.daf_beb is not None else '-'}\n"
        f"daf_pjl: {snp.daf_pjl if snp.daf_pjl is not None else '-'}\n"
        f"fst_beb: {snp.fst_beb if snp.fst_beb is not None else '-'}\n"
        f"fst_pjl: {snp.fst_pjl if snp.fst_pjl is not None else '-'}\n"
    )
    country = request.args.get('country', '').strip().lower()
    # Append metrics info if country is pakistan or bangladesh
    if country == "pakistan":
        metrics = (
            "\nMetric\tΔAF\tDAF\tREFERENCE\tANCESTRAL\n"
            "Average\t0.5605\t0.5031\t0.5134\t0.5011\n"
            "St Dev\t0.1165\t0.3086\t0.2936\t0.2852\n"
        )
        content += metrics
    elif country == "bangladesh":
        metrics = (
            "\nMetric\tΔAF\tDAF\tREFERENCE\tANCESTRAL\n"
            "Average\t0.5605\t0.5017\t0.5159\t0.5013\n"
            "St Dev\t0.1165\t0.3115\t0.2963\t0.2864\n"
        )
        content += metrics

    if country == "pakistan":
        filename = f"{snp.snp_id}_pakistan.txt"
    elif country == "bangladesh":
        filename = f"{snp.snp_id}_bangladesh.txt"
    else:
        filename = f"{snp.snp_id}.txt"
    response = Response(content, mimetype='text/plain')
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@app.route('/download_selected', methods=['POST'])
def download_selected():
    selected_ids = request.form.getlist('selected_snps')
    country = request.form.get('country', '').strip().lower()
    if not selected_ids:
        flash("No SNPs selected for download.", "warning")
        return redirect(url_for('genetic_data_search'))
    
    snps = GeneticData.query.filter(GeneticData.snp_id.in_(selected_ids)).all()
    content = ""
    for snp in snps:
        content += f"rsID: {snp.snp_id}\n"
        content += f"Risk Allele: {snp.risk_allele}\n"
        content += f"Gene: {snp.mapped_gene if snp.mapped_gene else '-'}\n"
        content += f"Trait: {snp.trait}\n"
        content += f"Phenotype: {snp.phenotype if snp.phenotype else '-'}\n"
        content += f"T2DKP P-value: {snp.t2dkp_p_value if snp.t2dkp_p_value is not None else '-'}\n"
        content += f"Beta: {snp.beta if snp.beta is not None else '-'}\n"
        content += f"P-Value: {snp.p_value}\n"
        content += f"Odds Ratio: {snp.odds_ratio}\n"
        content += f"delta_af: {snp.delta_af if snp.delta_af is not None else '-'}\n"
        content += f"daf_beb: {snp.daf_beb if snp.daf_beb is not None else '-'}\n"
        content += f"daf_pjl: {snp.daf_pjl if snp.daf_pjl is not None else '-'}\n"
        content += f"fst_beb: {snp.fst_beb if snp.fst_beb is not None else '-'}\n"
        content += f"fst_pjl: {snp.fst_pjl if snp.fst_pjl is not None else '-'}\n"
        content += f"Study Accession: {snp.study_accession}\n"
        content += f"PubMed ID: {snp.pubmed_id}\n"
        # Existing pathway information
        if snp.pathways:
            content += "Pathways:\n" + "\n".join([f" - {p.pathway_id}: {p.pathway_name}" for p in snp.pathways]) + "\n"
        else:
            content += "Pathways: -\n"
        # Add GO term information
        go_terms = get_go_terms(snp.snp_id)
        if go_terms:
            content += "GO Terms:\n" + "\n".join([f" - {term}" for term in go_terms]) + "\n"
        else:
            content += "GO Terms: -\n"
        content += "\n--------------------------------\n\n"
    
    if country == "pakistan":
        filename = "pakistan.txt"
    elif country == "bangladesh":
        filename = "bangladesh.txt"
    else:
        filename = "selected_snps.txt"
    
    if country:
        if country == "pakistan":
            metrics = (
                "\nMetric\tΔAF\tDAF\tREFERENCE\tANCESTRAL\n"
                "Average\t0.5605\t0.5031\t0.5134\t0.5011\n"
                "St Dev\t0.1165\t0.3086\t0.2936\t0.2852\n"
            )
        elif country == "bangladesh":
            metrics = (
                "\nMetric\tΔAF\tDAF\tREFERENCE\tANCESTRAL\n"
                "Average\t0.5605\t0.5017\t0.5159\t0.5013\n"
                "St Dev\t0.1165\t0.3115\t0.2963\t0.2864\n"
            )
        else:
            metrics = ""
        content += metrics

    response = Response(content, mimetype='text/plain')
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@app.route("/test_db")
def test_db():
    results = GeneticData.query.limit(5).all()
    if not results:
        return " No data found in the database!"
    output = "<h2>Test Data from SNP Table:</h2><ul>"
    for row in results:
        output += f"<li>{row.snp_id} | {row.trait} | {row.p_value} | fst_beb: {row.fst_beb} | fst_pjl: {row.fst_pjl}</li>"
    output += "</ul>"
    return output

@app.route("/init_db")
def init_db():
    with app.app_context():
        db.create_all()
    return " Database initialized successfully!"

# ---------- new route for FST visualisation ----------
@app.route('/fst_tool')
def fst_tool():
    # Ensure that your fst.html is in the templates/ folder.
    return render_template('fst.html')

# ---------- new route for SNP_GO column information ----------
@app.route('/snp_go_columns')
def snp_go_columns():
    """
    Returns the column information for the snp_go table as JSON.
    Expected columns: snp_id (VARCHAR(20)) and go_id (VARCHAR(50)).
    """
    inspector = db.inspect(db.engine)
    columns = inspector.get_columns('snp_go')
    return jsonify(columns)

# ---------- default route----------
@app.route('/default')
def default_callable():
    query_list = ["fst_plot"]
    return "Please type the query you want after / . Thank you." + str(query_list)

if __name__ == "__main__":
    try:
        with app.app_context():
            db.create_all()
            print(" Database tables created successfully.")
    except Exception as e:
        print(f" Error during database initialization: {str(e)}")
    app.run(debug=True)
