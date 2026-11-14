# Energy Insight ⚡
### Smart Household Energy Analytics & Forecasting Platform

Energy Insight is an interactive data analytics project that explores household electricity consumption through data cleaning, exploratory analysis, statistical methods, forecasting, anomaly detection, and interactive visualisation.

Built using Python and Streamlit, the project transforms historical electricity consumption readings into an accessible dashboard for exploring usage patterns, understanding energy costs, and examining potential consumption trends.

---

## Project Overview

The project uses the **Individual Household Electric Power Consumption** dataset from the UCI Machine Learning Repository.

The dataset contains approximately 2.07 million minute-level measurements collected from a single household in France between December 2006 and November 2010.

The objective is to demonstrate how raw time-series data can be processed, analysed, stored, and presented through an interactive analytical application.

## Dashboard Features

### 1. Overview
- Key electricity consumption indicators.
- Summary statistics for selected periods.
- Daily and hourly consumption patterns.
- Interactive date filtering.

### 2. Consumption Analysis
- Hourly, daily, and monthly consumption trends.
- Usage pattern comparisons.
- Visual exploration of household electricity demand.

### 3. Cost Analysis
- Estimated electricity expenditure.
- Cost comparisons across selected periods.
- Interactive tariff-based calculations.

### 4. Forecasting & Anomaly Detection
- Baseline time-series forecasting models.
- Historical forecast evaluation.
- Prediction intervals.
- Detection and exploration of unusual consumption patterns.

### 5. Data Explorer
- Explore processed consumption records.
- Filter data by date and other available dimensions.
- Inspect data quality and completeness.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming | Python |
| Data manipulation | Pandas, NumPy |
| Data visualisation | Plotly |
| Database | SQLite |
| Dashboard | Streamlit |
| Analysis | Jupyter Notebook |
| Development | VS Code, Git |

## Project Structure

```text
enery-usage-analyser/
│
├── dashboard/
│   ├── app.py
│   ├── charts.py
│   └── components.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── docs/
│   └── images/
│
├── notebooks/
│   └── analysis.ipynb
│
├── reports/
│
├── src/
│   ├── analysis.py
│   ├── anomaly_detection.py
│   ├── clean_data.py
│   ├── database.py
│   ├── forecasting.py
│   ├── test_backend.py
│   └── validate_data.py
│
├── .gitignore
├── README.md
└── requirements.txt
```

## Data Source

**Individual Household Electric Power Consumption**

Source: [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption)

Dataset characteristics:
- Approximately 2.07 million measurements.
- One household in France.
- Observation period: December 2006 – November 2010.
- Original measurement frequency: one minute.
- Includes active and reactive power, voltage, current, and three sub-metering measurements.

The original dataset is approximately 127 MB and is not included in this repository.

## Methodology

The project follows a data processing and analysis workflow:

1. **Data Cleaning:** Process raw measurements, handle missing values, and prepare timestamps.
2. **Data Validation:** Examine data completeness and consistency.
3. **Database Management:** Store and retrieve processed consumption records using SQLite.
4. **Exploratory Data Analysis:** Investigate consumption patterns across different time periods.
5. **Statistical Analysis:** Calculate summary metrics and explore household usage behaviour.
6. **Forecasting:** Implement and compare baseline time-series forecasting approaches.
7. **Anomaly Detection:** Identify unusual consumption patterns.
8. **Visualisation:** Present analytical results through an interactive Streamlit dashboard.

## Running the Project Locally

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd enery-usage-analyser
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Prepare the data

Download the original dataset from the UCI Machine Learning Repository and place the raw file in:

```text
data/raw/household_power_consumption.txt
```

Follow the project's data-processing instructions to generate the processed SQLite database.

### 5. Launch the dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard will open in your browser.

*Note: The database preparation instructions will be finalised after verifying the current database setup and processing scripts.*

## Limitations

- The dataset represents only one household and cannot represent electricity consumption patterns across all households.
- The observations are historical and do not necessarily reflect present-day energy usage.
- Forecasting results are based on historical patterns and should not be interpreted as guaranteed future consumption.
- Cost estimates depend on the electricity tariff selected.
- Anomaly detection identifies unusual patterns; an unusual observation does not necessarily indicate an actual fault or problem.

## Future Scope

Potential extensions include:
- Exploring additional forecasting approaches.
- Improving anomaly detection and evaluation.
- Integrating data from multiple households.
- Adding more detailed consumption comparisons.
- Exploring more advanced interactive analytical features.

## Author

**Ashish Kaur**

[GitHub](YOUR_GITHUB_PROFILE_URL) · [LinkedIn](YOUR_LINKEDIN_URL)