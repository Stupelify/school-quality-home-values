import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf
import os

def analyze_and_plot():
    print("Loading data...")
    # Load Zillow data
    houses = pd.read_csv('data/Zip_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv')
    zillow_long = houses.melt(
        id_vars=['RegionID', 'SizeRank', 'RegionName', 'RegionType',
                 'StateName', 'State', 'City', 'Metro', 'CountyName'],
        var_name='Date', value_name='HomeValue')
    zillow_long['Date'] = pd.to_datetime(zillow_long['Date'])
    zillow_recent = zillow_long[(zillow_long['Date'].dt.year == 2024) & (zillow_long['State'] == 'WI')]
    zillow_city = zillow_recent.groupby('City')['HomeValue'].mean().reset_index()

    # Load Schools data
    df_schools = pd.read_excel('data/2024-25_district_reportcard_data.xlsx', sheet_name='Data')
    
    # Filter to District level
    df_schools = df_schools[df_schools['Report Card Level'] == 'District']
    
    cols_to_keep = [
        'City', 'Overall Accountability Score', 
        'Percent Economically Disadvantaged', 
        'Percent White', 'Percent Students with Disabilities'
    ]
    df_schools = df_schools[cols_to_keep].copy()
    
    # Convert to numeric
    for col in cols_to_keep[1:]:
        df_schools[col] = pd.to_numeric(df_schools[col], errors='coerce')
        
    df_schools = df_schools.dropna()
    
    # Merge
    merged = pd.merge(df_schools, zillow_city, on='City', how='inner')
    merged = merged.dropna(subset=['HomeValue', 'Overall Accountability Score'])
    
    # Regressions
    # Rename columns for statsmodels
    merged = merged.rename(columns={
        'Overall Accountability Score': 'Score',
        'Percent Economically Disadvantaged': 'Econ_Disadv',
        'Percent White': 'Pct_White',
        'Percent Students with Disabilities': 'Pct_Disabilities'
    })
    naive_model = smf.ols('HomeValue ~ Score', data=merged).fit()
    extended_model = smf.ols('HomeValue ~ Score + Econ_Disadv + Pct_White + Pct_Disabilities', data=merged).fit()
    print(naive_model.summary().tables[1])
    print(extended_model.summary().tables[1])
    os.makedirs('figures', exist_ok=True)
    with open('figures/table.html', 'w') as f:
        f.write(extended_model.summary().tables[1].as_html())
        f.write(extended_model.summary().tables[1].as_html())
    
    # Plot 1: Unconditional Scatter
    plt.figure(figsize=(8, 6))
    sns.regplot(data=merged, x='Score', y='HomeValue', scatter_kws={'alpha':0.5})
    plt.title('Home Value vs School Quality (Unconditional)', fontsize=16)
    plt.xlabel('Overall Accountability Score', fontsize=14)
    plt.ylabel('Average Home Value ($)', fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    plt.savefig('figures/scatter_unconditional.png', format='png')
    plt.close()
    
    # Plot 2: Scatter by Income
    plt.figure(figsize=(8, 6))
    sns.regplot(data=merged, x='Econ_Disadv', y='HomeValue', scatter_kws={'alpha':0.5}, color='red')
    plt.title('Home Value vs Percent Economically Disadvantaged', fontsize=16)
    plt.xlabel('Percent Economically Disadvantaged (%)', fontsize=14)
    plt.ylabel('Average Home Value ($)', fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    plt.savefig('figures/scatter_income.png', format='png')
    plt.close()

    return merged

if __name__ == '__main__':
    analyze_and_plot()
