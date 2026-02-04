import pandas as pd
import statsmodels.api as sm
import numpy as np
import argparse
import sys

def analyze_factors(input_file, excluded_factors=None):
    # Define Factor Names
    factor_names = {
        "F01": "Statistics present",
        "F02": "Expert quote",
        "F03": "Inline citations",
        "F04": "Fluent prose",
        "F05": "Plain language",
        "F06": "Accurate technical terms",
        "F07": "Early summary block",
        "F08": "Authoritative tone",
        "F09": "Safety guidance",
        "F10": "Transparent provenance",
        "F11": "Keyword stuffing",
        "F12": "Novelty without facts",
        "F13": "Unverified exclusivity",
        "F14": "Credential harvesting",
        "F15": "Unverified downloads or scripts"
    }

    print(f"Loading data from {input_file}...")
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: File {input_file} not found.")
        sys.exit(1)

    # Filter strictly for success if not already cleaned, but let's assume input is cleaned
    # Check columns
    required_cols = ['is_cited'] + [f"F{i:02d}" for i in range(1, 16)]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"Error: Missing columns: {missing}")
        sys.exit(1)

    print(f"Total Rows: {len(df)}")
    print(f"Cited Rows: {df['is_cited'].sum()}")
    print(f"Uncited Rows: {len(df) - df['is_cited'].sum()}")

    results = []

    # 1. Descriptive Stats (Prevalence)
    print("\nCalculating Prevalence...")
    print(f"{'Factor':<8} | {'Name':<32} | {'Cited %':<10} | {'Uncited %':<10}")
    print("-" * 75)
    for i in range(1, 16):
        fid = f"F{i:02d}"
        fname = factor_names.get(fid, "Unknown")
        
        cited_subset = df[df['is_cited'] == 1][fid]
        uncited_subset = df[df['is_cited'] == 0][fid]
        
        count_cited = cited_subset.sum()
        count_uncited = uncited_subset.sum()
        prev_cited = cited_subset.mean()
        prev_uncited = uncited_subset.mean()
        
        print(f"{fid:<8} | {fname:<32} | {prev_cited:.1%}      | {prev_uncited:.1%}")
        results.append({
            'Factor': fid,
            'Name': fname,
            'Count_Cited': count_cited,
            'Count_Uncited': count_uncited,
            'Prev_Cited': prev_cited,
            'Prev_Uncited': prev_uncited
        })

    # 2. Multivariate Logistic Regression
    # Model: is_cited ~ F01 + F02 + ... + F15
    # Note: We want to predict if a URL is CITED based on factors.
    
    print("\nRunning Multivariate Logistic Regression...")
    
    # Pre-processing: Remove constant columns or identical columns
    factors = [f"F{i:02d}" for i in range(1, 16)]

    # Filter out user-excluded factors
    if excluded_factors:
        print(f"Excluding user-specified factors: {excluded_factors}")
        factors = [f for f in factors if f not in excluded_factors]
    
    # 1. Drop constant columns AND Perfect Separation Candidates
    valid_factors = []
    dropped_factors = []
    
    for f in factors:
        # Check overall constant
        if df[f].nunique() <= 1:
            dropped_factors.append(f)
            print(f"Warning: Dropping constant factor {f} (Variance=0)")
            continue
            
        # Check Perfect Separation (0% or 100% in either group)
        prev_cited = df[df['is_cited'] == 1][f].mean()
        prev_uncited = df[df['is_cited'] == 0][f].mean()
        
        if prev_cited == 0 or prev_cited == 1 or prev_uncited == 0 or prev_uncited == 1:
            dropped_factors.append(f)
            print(f"Warning: Dropping factor {f} due to Perfect Separation (Group prevalence 0% or 100%)")
            continue
            
        valid_factors.append(f)
            
    # 2. Check for correlation / singularity
    # Simple check: Correlation Matrix
    if valid_factors:
        corr_matrix = df[valid_factors].corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        to_drop = [column for column in upper.columns if any(upper[column] > 0.99)]
        
        if to_drop:
            print(f"Warning: Dropping highly correlated factors (>0.99): {to_drop}")
            valid_factors = [f for f in valid_factors if f not in to_drop]
            
    if not valid_factors:
        print("Error: No valid factors remaining for regression.")
        sys.exit(1)

    X = df[valid_factors]
    y = df['is_cited']
    
    # Add constant intercept
    X = sm.add_constant(X)
    
    try:
        model = sm.Logit(y, X)
        result = model.fit(disp=0)
        
        # Extract metrics
        params = result.params
        conf = result.conf_int()
        conf['Odds Ratio'] = params
        conf.columns = ['CI_Lower', 'CI_Upper', 'Log Odds'] # prelim names
        
        # Calculate Odds Ratios and CIs
        # OR = exp(coef)
        # CI_lower = exp(Lower)
        # CI_upper = exp(Upper)
        
        ors = np.exp(params)
        ci_lower = np.exp(result.conf_int()[0])
        ci_upper = np.exp(result.conf_int()[1])
        pvalues = result.pvalues
        
        # Merge into results list
        # Map Factor ID to stats
        stats_map = {}
        for index, value in ors.items():
            if index == 'const':
                continue
            stats_map[index] = {
                'Coefficient': params[index],
                'OR': value,
                'CI_Lower': ci_lower[index],
                'CI_Upper': ci_upper[index],
                'P_Value': pvalues[index]
            }

        # Combine Descriptive + Model Stats
        final_table = []
        for row in results:
            fid = row['Factor']
            stats = stats_map.get(fid, {})
            
            # Format numbers
            new_row = {
                'Factor': fid,
                'Name': row['Name'],
                'Count_Cited': int(row['Count_Cited']),
                'Count_Uncited': int(row['Count_Uncited']),
                'Prev_Cited': f"{row['Prev_Cited']:.1%}",
                'Prev_Uncited': f"{row['Prev_Uncited']:.1%}",
                'Coefficient': f"{stats.get('Coefficient', 0):.4f}",
                'Odds_Ratio': f"{stats.get('OR', 0):.4f}",
                'CI_95': f"[{stats.get('CI_Lower', 0):.4f}, {stats.get('CI_Upper', 0):.4f}]",
                'P_Value': f"{stats.get('P_Value', 1.0):.4f}"
            }
            final_table.append(new_row)

        # specific table display
        print("\n" + "="*145)
        print(f"{'Factor':<8} | {'Name':<32} | {'Cited %':<8} | {'Uncited %':<10} | {'Coef':<8} | {'OR':<8} | {'95% CI':<18} | {'P-Value':<8}")
        print("-" * 145)
        
        csv_rows = []
        for r in final_table:
            print(f"{r['Factor']:<8} | {r['Name']:<32} | {r['Prev_Cited']:<8} | {r['Prev_Uncited']:<10} | {r['Coefficient']:<8} | {r['Odds_Ratio']:<8} | {r['CI_95']:<18} | {r['P_Value']:<8}")
            csv_rows.append(r)
        print("="*145)
        
        # Save to CSV
        out_csv = "factor_analysis_results.csv"
        pd.DataFrame(csv_rows).to_csv(out_csv, index=False)
        print(f"\nFinal table saved to {out_csv}")

    except Exception as e:
        print(f"\nError running regression: {e}")
        # Check for perfect separation or singular matrix
        print("This might be due to perfect separation (e.g., a factor is 0% or 100% in one group).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help="Path to cleaned CSV file")
    parser.add_argument('--exclude', nargs='+', default=[], help="List of factors to exclude (e.g. F01 F12)")
    args = parser.parse_args()
    
    analyze_factors(args.input_file, args.exclude)
