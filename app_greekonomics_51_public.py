import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker 
import seaborn as sns
import re
import eurostat

sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'axes.facecolor': '#F7F7F7',
    'figure.facecolor': 'white',
    'axes.edgecolor': '#D3D3D3',
    'axes.labelweight': 'bold',
    'axes.labelsize': 12,
    'axes.titlesize': 16,
    'axes.titleweight': 'bold',
    'xtick.color': 'black',
    'ytick.color': 'black',
})

colors_financial = {
    "EL": "#1B3C69",
    "EU27_2020": "#4A4A4A",
    "Bottom_10_Avg": "#901628"
}

list_of_countries = ["EL", "EU27_2020"]
selected_countries = ["BG", "HU", "LV", "HR", "PL", "LT", "SK", "EE", "CZ", "RO"]

def plot_indicator(dataset_id, title, subtitle, y_label, unit_filter=None, filter_col=None, geo_filter=None, y_format=None):
   
    df = eurostat.get_data_df(dataset_id)

    df.columns = [col.lower() for col in df.columns]

    geo_col = next((col for col in df.columns if 'geo' in col and 'time' in col), None)
    if geo_col:
        df = df.rename(columns={geo_col: 'geo'})
    else:
        raise KeyError("Couldn't find the geo/time column.")

    year_columns = [col for col in df.columns if col.startswith('20') or col.startswith('19')]

    df_long = pd.melt(df,
                    id_vars=['geo'],
                    value_vars=year_columns,
                    var_name='time',
                    value_name='values')

    df_long['time'] = df_long['time'].astype(int)

    df_long = df_long.dropna(subset=['values'])

    bottom_10_avg = (
        df_long[df_long['geo'].isin(selected_countries)]
        .groupby('time')['values']
        .mean()
        .reset_index()
        .assign(geo='Bottom_10_Avg')
    )

    combined = pd.concat([
        df_long[df_long['geo'].isin(list_of_countries)],
        bottom_10_avg
    ], ignore_index=True)

    combined = combined.drop_duplicates(subset=['geo', 'time'])

    combined = combined.sort_values(by=['geo', 'time'])

    combined = combined[combined['values'].notna()]
    combined = combined[combined['values'] > 0]

    print("Preview of df_long:")
    print(df_long.head())
    print("Unique GEOs:", df_long['geo'].unique())
    print("Time range:", df_long['time'].min(), "-", df_long['time'].max())

    print("All available GEOs:", df_long['geo'].unique())

    plt.figure(figsize=(12, 6))
    for geo in combined['geo'].unique():
        data = combined[combined['geo'] == geo].copy()
        data = data.sort_values('time')

        label = {
            "EL": "Greece",
            "EU27_2020": "EU27 (2020)",
            "Bottom_10_Avg": "Bottom 10 Avg"
        }.get(geo, geo)

        linestyle = 'dashed' if geo == 'Bottom_10_Avg' else 'solid'
        plt.plot(data['time'], data['values'], label=label, linestyle=linestyle,
                color=colors_financial.get(geo, 'gray'), alpha=0.9)
        plt.scatter(data['time'], data['values'], color=colors_financial.get(geo, 'gray'), edgecolor='white', zorder=3)


    plt.title(f"{title}\n{subtitle}")
    plt.xlabel("Year")
    plt.ylabel(y_label)
    if y_format:
        plt.gca().yaxis.set_major_formatter(y_format)
    plt.legend()
    plt.grid(True, linestyle='-', linewidth=0.5)
    plt.tight_layout()
    plt.show()

industry_colors = {
    "Ακίνητα": "#1B3C69",
    "Μεταποιητική Βιομηχανία": "#A6192E",
    "Δημόσια Διοίκηση και Άμυνα": "#2E7D32",
    "Μεταφορές και Αποθήκευση": "#4A4A4A",
    "Χονδρικό και Λιανικό Εμπόριο": "#6D8299",
    "Γεωργία, Δασοκομία και Αλιεία": "#D4A017",
    "Πληροφορική και Επικοινωνίες": "#8B5E3C"
}

def plot_sectoral_investment(country_code):
    df = eurostat.get_data_df("nama_10_a64_p5")
    df.columns = [col.lower() for col in df.columns]

    geo_col = next((col for col in df.columns if 'geo' in col and 'time' in col), None)
    if geo_col:
        df = df.rename(columns={geo_col: 'geo'})
    else:
        raise KeyError("Couldn't find the geo/time column.")

    year_columns = [col for col in df.columns if col.startswith('20') or col.startswith('19')]
    df_long = pd.melt(df, id_vars=['geo', 'nace_r2', 'unit', 'asset10'], value_vars=year_columns,
                      var_name='time', value_name='values')
    df_long['time'] = df_long['time'].astype(int)
    df_long = df_long.dropna(subset=['values'])

    df_long = df_long[(df_long['geo'] == country_code) &
                      (df_long['unit'] == 'CLV15_MEUR') &
                      (df_long['asset10'] == 'N11G')]

    greek_labels = {
        "A": "Γεωργία, Δασοκομία και Αλιεία",
        "C": "Μεταποιητική Βιομηχανία",
        "L": "Ακίνητα",
        "O": "Δημόσια Διοίκηση και Άμυνα",
        "H": "Μεταφορές και Αποθήκευση",
        "G": "Χονδρικό και Λιανικό Εμπόριο",
        "J": "Πληροφορική και Επικοινωνίες"
    }
    df_long['nace_label'] = df_long['nace_r2'].map(greek_labels)
    df_long = df_long[df_long['nace_label'].notna()]

    top_sectors = df_long.groupby('nace_label')['values'].sum().nlargest(7).index.tolist()
    df_long = df_long[df_long['nace_label'].isin(top_sectors)]

    plt.figure(figsize=(12, 6))
    for label in df_long['nace_label'].unique():
        sub = df_long[df_long['nace_label'] == label]
        plt.plot(sub['time'], sub['values'], label=label,
                 color=industry_colors.get(label, 'gray'))
        plt.scatter(sub['time'], sub['values'], color=industry_colors.get(label, 'gray'), edgecolor='white')

    plt.title(f"Επενδύσεις ανά Κλάδο (7 κορυφαίοι), Χώρα: {country_code}")
    plt.xlabel("Έτος")
    plt.ylabel("CLV15_MEUR")
    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.show()

# List of plots to generate
plot_configs = [
    ("tepsr_wc310", "Real Gross Disposable Income Per Capita", "Index (2008 = 100)", "Index (2008 = 100)", "CP_MNAC", None, None),
    ("sdg_10_10", "Real GDP Per Capita (PPS)", "Purchasing Power Standards (Base Year 2020)", "PPS", None, "na_item", "EXP_PPS_EU27_2020_HAB"),
    ("tipsna40", "Real GDP Per Capita", "EUR (2015 constant prices)", "EUR (2015)", "CLV15_EUR_HAB", None, None),
    ("tipsgo10", "General Government Gross Debt", "'%' of GDP", "'%' GDP", "PC_GDP", None, None, ticker.PercentFormatter()),
    ("tipsbp20", "Current Account Balance", "% of GDP", "% GDP", "PC_GDP", "bop_item", "CA", ticker.PercentFormatter()),
    ("tipsun20", "Youth Unemployment Rate (15-24)", "% of Labour Force", "% Labour Force", None, "age", "Y15-24", ticker.PercentFormatter()),
    ("tipsun20", "Total Unemployment Rate (15-74)", "% of Labour Force", "% Labour Force", None, "age", "Y15-74", ticker.PercentFormatter()),
    ("lfsa_eoqgan", "Over-Qualification Rate", "% of Employees", "% Employees", None, "citizen", "TOTAL", ticker.PercentFormatter()),
    ("tipslc10", "People at Risk of Poverty or Social Exclusion", "% of Population", "% Population", "PC", None, None, ticker.PercentFormatter()),
    ("nama_10_lp_ulc", "Compensation of Employees Per Hour Worked", "Nominal Values", "EUR", "EUR", "na_item", "D1_SAL_HW"),
    ("nama_10_a64_p5", "Sectoral Investment (EL)", "Top 7 industries by capital stock", "CLV15_MEUR", None, None, None)
]

# Generate plots
for cfg in plot_configs:
    if cfg[0] == "nama_10_a64_p5":
        plot_sectoral_investment("EL")
    else:
        plot_indicator(*cfg)
