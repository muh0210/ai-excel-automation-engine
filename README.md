# 🚀 AI Excel Automation Engine v2.0

> **Premium Data Automation Platform** — Upload any Excel/CSV file and get instant cleaning, deep profiling, AI insights, ML anomaly detection, statistical tests, 15+ interactive charts, and professional reports.

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Plotly](https://img.shields.io/badge/Plotly-239120?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)

🔗 **[Live Demo](https://ai-excel-automation-engin-f3sfb7asi9nbulpvdhfexg.streamlit.app/)**

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧹 **Smart Cleaning** | Auto-removes duplicates, fills missing values, fixes data types, standardizes column names |
| 🔬 **Data Profiler** | Column-by-column statistics, missing patterns, cardinality analysis, memory usage, constant detection |
| 📊 **KPI Dashboard** | Totals, averages, growth %, trend metrics for every numeric column |
| 📈 **15+ Chart Types** | Line, bar, scatter, pie, heatmap, box, violin, radar, sunburst, pareto, waterfall, scatter matrix & more |
| 🧠 **AI Insights** | Pareto patterns, cross-column dependencies, outlier narratives, recommendations — 20+ insight types |
| 🚨 **ML Anomaly Detection** | Z-Score, IQR, **Isolation Forest**, **Local Outlier Factor** — statistical + ML-based |
| 📐 **Statistical Tests** | Linear regression, ANOVA, normality (Shapiro-Wilk), chi-square, percentile analysis |
| 💬 **Natural Language Query** | "group by region and sum sales", "compare profit between North and South", "what correlates with sales?" |
| 📊 **Pivot Tables** | Interactive pivot table builder with custom aggregation |
| 📄 **Pro Reports** | PDF with table of contents, severity-colored insights + multi-sheet Excel with formatting |
| 🎯 **Demo Datasets** | One-click demo data — E-Commerce, Employee, Finance — no file needed |

---

## 🏗️ Architecture

```
User Upload / Demo Data
        ↓
   Data Loader → Cleaning Engine → Data Profiler
        ↓               ↓               ↓
   Analysis Engine   AI Insight Engine   Anomaly Detection (ML + Statistical)
        ↓               ↓               ↓
   Visualization Engine (15+ charts)   Statistical Testing (Regression, ANOVA)
        ↓               ↓               ↓
        └───────→ Streamlit Dashboard ←──┘
                        ↓
            Auto Report Export (PDF/Excel)
```

---

## 📁 Project Structure

```
ai-excel-automation-engine/
├── data/                           # Sample datasets (4 files)
│   ├── sample_ecommerce_sales.xlsx
│   ├── sample_employee_data.xlsx
│   ├── sample_financial_report.xlsx
│   └── sample_student_grades.csv
├── utils/
│   ├── __init__.py
│   ├── loader.py                   # File upload & format detection
│   ├── cleaner.py                  # Data preprocessing pipeline
│   ├── profiler.py                 # Deep data profiling [NEW]
│   ├── analyzer.py                 # Statistical analysis, Pareto, moving averages
│   ├── visualizer.py               # 15+ Plotly chart types
│   ├── insights.py                 # AI business insight engine (20+ types)
│   ├── anomaly.py                  # Z-Score, IQR, Isolation Forest, LOF
│   ├── statistics.py               # Regression, ANOVA, normality, chi-square [NEW]
│   ├── transformer.py              # Pivot tables, calculated columns [NEW]
│   └── reporter.py                 # PDF (with TOC) & Excel report generation
├── app.py                          # Main Streamlit application
├── generate_sample.py              # Sample data generator
├── test_pipeline.py                # Integration tests
├── requirements.txt
├── .streamlit/config.toml          # Dark theme configuration
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
git clone https://github.com/muh0210/ai-excel-automation-engine.git
cd ai-excel-automation-engine
pip install -r requirements.txt
python generate_sample.py    # Optional: generate demo data
streamlit run app.py
```

The app opens at `http://localhost:8501`

---

## 💡 Usage

1. **Upload** any `.xlsx`, `.xls`, or `.csv` file — or click a **Demo** button
2. **Review** automatic cleaning and data profiling results
3. **Explore** the KPI dashboard with growth metrics
4. **Analyze** across 15+ interactive chart types and 7 visualization tabs
5. **Read** 20+ AI-generated insights about your data
6. **Detect** anomalies with statistical (Z-Score/IQR) or ML (Isolation Forest/LOF) methods
7. **Run** statistical tests — linear regression, ANOVA, normality, pivot tables
8. **Query** in natural language — group, compare, correlate, filter
9. **Export** professional PDF or Excel reports

### Natural Language Queries

```
"show top 5 by sales"                    "average of profit"
"group by region and sum sales"          "compare sales between North and South"
"what correlates with profit?"           "filter where sales between 100 and 500"
"sort by quantity descending"            "what percentage of sales is from Online"
"count unique category"                  "describe sales"
```

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| **Frontend** | Streamlit, Custom CSS (glassmorphism, animations) |
| **Data** | Pandas, NumPy |
| **Charts** | Plotly (15+ chart types) |
| **ML** | scikit-learn (Isolation Forest, LOF) |
| **Stats** | SciPy (regression, ANOVA, normality, chi-square) |
| **PDF** | fpdf2 |
| **Excel** | openpyxl, xlsxwriter |

---

## 👤 Author

**Muhammad Rajput**
- 📧 muhrajpoot1921@gmail.com
- 🐙 [github.com/muh0210](https://github.com/muh0210)

---

## 📜 License

This project is open source and available under the [MIT License](LICENSE).
