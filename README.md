# 🚀 AI Excel Automation Engine

> **Premium Data Automation** — Upload any Excel/CSV file and get instant cleaning, AI insights, interactive charts, anomaly detection, and professional reports.

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Plotly](https://img.shields.io/badge/Plotly-239120?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧹 **Smart Cleaning** | Auto-removes duplicates, fills missing values, fixes data types, standardizes column names |
| 📊 **KPI Dashboard** | Instant total, average, growth %, and trend metrics for every numeric column |
| 📈 **Interactive Charts** | Line, bar, scatter, pie, heatmap, box plot — all Plotly-powered with premium dark theme |
| 🧠 **AI Insights** | Converts raw data into human-readable business narratives — trends, correlations, anomalies |
| 🚨 **Anomaly Detection** | Z-Score & IQR methods to flag unusual data patterns with visual markers |
| 💬 **Natural Language Query** | Ask questions in plain English — "show top 5 by sales", "average of profit" |
| 📄 **Auto Reports** | Download professional PDF & multi-sheet Excel reports instantly |

---

## 🏗️ Architecture

```
User Upload → Data Loader → Cleaning Engine → Analysis Engine → AI Insight Engine
                                                     ↓                    ↓
                                            Visualization Engine    Anomaly Detection
                                                     ↓                    ↓
                                              Streamlit Dashboard ← ← ← ←
                                                     ↓
                                             Auto Report Export (PDF/Excel)
```

---

## 📁 Project Structure

```
excel-ai/
├── data/
│   └── sample_sales.xlsx       # Demo dataset
├── outputs/                     # Generated reports
├── utils/
│   ├── __init__.py
│   ├── loader.py               # File upload & format detection
│   ├── cleaner.py              # Data preprocessing pipeline
│   ├── analyzer.py             # Statistical analysis & KPIs
│   ├── visualizer.py           # Plotly chart generation
│   ├── insights.py             # AI business insight engine
│   ├── anomaly.py              # Anomaly detection (Z-Score/IQR)
│   └── reporter.py             # PDF & Excel report generation
├── app.py                       # Main Streamlit application
├── requirements.txt
├── .streamlit/
│   └── config.toml             # Dark theme configuration
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/muh0210/ai-excel-automation-engine.git
cd ai-excel-automation-engine

# Install dependencies
pip install -r requirements.txt

# Generate sample data (optional)
python generate_sample.py

# Run the application
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`

---

## 💡 Usage

1. **Upload** any `.xlsx`, `.xls`, or `.csv` file
2. **Review** the automatic cleaning results and data quality metrics
3. **Explore** the KPI dashboard with totals, averages, and growth %
4. **Analyze** interactive charts across 5 different visualization types
5. **Read** AI-generated insights about your data patterns
6. **Detect** anomalies with adjustable sensitivity
7. **Query** your data in natural language
8. **Export** professional PDF or Excel reports

### Natural Language Queries

```
"show top 5 by sales"
"filter where region is North"
"average of profit"
"sort by quantity descending"
"show columns"
"count unique category"
"describe sales"
```

---

## 🌐 Deployment

### Streamlit Cloud (Recommended)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Set `app.py` as the main file
5. Deploy!

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Data**: Pandas, NumPy
- **Charts**: Plotly
- **PDF**: fpdf2
- **Excel**: openpyxl, xlsxwriter

---

## 👤 Author

**Muhammad Rajput**
- 📧 muhrajpoot1921@gmail.com
- 🐙 [github.com/muh0210](https://github.com/muh0210)

---

## 📜 License

This project is open source and available under the [MIT License](LICENSE).
