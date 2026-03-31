"""
Generate comprehensive sample/dummy data files for demo purposes.
Creates multiple example files covering different data scenarios.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)
os.makedirs('data', exist_ok=True)

# ══════════════════════════════════════════════════════════════════════
# FILE 1: E-Commerce Sales Data (most comprehensive)
# ══════════════════════════════════════════════════════════════════════
n = 250

start_date = datetime(2023, 1, 1)
dates = [start_date + timedelta(days=int(x)) for x in np.sort(np.random.randint(0, 730, n))]

products = ['Laptop Pro 15"', 'Wireless Mouse', 'USB-C Hub', 'Mechanical Keyboard',
            'Monitor 27" 4K', 'Webcam HD', 'Headset Pro', 'SSD 1TB', 'RAM 16GB', 'Bluetooth Speaker']

categories = {
    'Laptop Pro 15"': 'Electronics', 'Wireless Mouse': 'Accessories',
    'USB-C Hub': 'Accessories', 'Mechanical Keyboard': 'Peripherals',
    'Monitor 27" 4K': 'Electronics', 'Webcam HD': 'Peripherals',
    'Headset Pro': 'Audio', 'SSD 1TB': 'Storage',
    'RAM 16GB': 'Storage', 'Bluetooth Speaker': 'Audio'
}

price_map = {
    'Laptop Pro 15"': 1299.99, 'Wireless Mouse': 29.99, 'USB-C Hub': 49.99,
    'Mechanical Keyboard': 149.99, 'Monitor 27" 4K': 449.99, 'Webcam HD': 79.99,
    'Headset Pro': 199.99, 'SSD 1TB': 89.99, 'RAM 16GB': 64.99, 'Bluetooth Speaker': 59.99
}

regions = ['North', 'South', 'East', 'West']
channels = ['Online', 'Retail Store', 'Wholesale']
customer_types = ['New', 'Returning', 'VIP']

product_list = np.random.choice(products, n)
category_list = [categories[p] for p in product_list]
region_list = np.random.choice(regions, n)
channel_list = np.random.choice(channels, n, p=[0.5, 0.35, 0.15])
customer_list = np.random.choice(customer_types, n, p=[0.4, 0.45, 0.15])
unit_prices = [price_map[p] for p in product_list]

# Quantity with seasonal variation
base_qty = np.random.randint(1, 25, n)
quantity = base_qty

# Sales = price × quantity with some noise
sales = np.array([price_map[p] * q for p, q in zip(product_list, quantity)])
noise = np.random.normal(0, 50, n)
sales = np.maximum(sales + noise, 10).round(2)

# Profit margin varies by channel
margin_base = {'Online': 0.25, 'Retail Store': 0.18, 'Wholesale': 0.10}
margins = np.array([margin_base[c] + np.random.uniform(-0.05, 0.10) for c in channel_list])
profit = (sales * margins).round(2)

# Discount
discounts = np.random.choice([0, 5, 10, 15, 20, 25], n, p=[0.3, 0.25, 0.2, 0.12, 0.08, 0.05])

# Ratings
ratings = np.round(np.clip(np.random.normal(4.0, 0.7, n), 1, 5), 1)

df_sales = pd.DataFrame({
    'Date': dates,
    'Product': product_list,
    'Category': category_list,
    'Region': region_list,
    'Sales_Channel': channel_list,
    'Customer_Type': customer_list,
    'Unit_Price': unit_prices,
    'Quantity': quantity,
    'Sales': sales,
    'Discount_%': discounts,
    'Profit': profit,
    'Rating': ratings
})

# Inject anomalies (unusually high sales)
for idx in [42, 87, 155, 210]:
    if idx < len(df_sales):
        df_sales.loc[idx, 'Sales'] = df_sales.loc[idx, 'Sales'] * 5
        df_sales.loc[idx, 'Profit'] = df_sales.loc[idx, 'Profit'] * 5

# Inject missing values
for _ in range(12):
    df_sales.loc[np.random.randint(0, n), 'Sales'] = np.nan
for _ in range(8):
    df_sales.loc[np.random.randint(0, n), 'Region'] = np.nan
for _ in range(5):
    df_sales.loc[np.random.randint(0, n), 'Rating'] = np.nan
for _ in range(6):
    df_sales.loc[np.random.randint(0, n), 'Profit'] = np.nan

# Inject duplicates
dup_rows = df_sales.sample(8, random_state=99)
df_sales = pd.concat([df_sales, dup_rows], ignore_index=True)

df_sales.to_excel('data/sample_ecommerce_sales.xlsx', index=False)
print(f"✅ sample_ecommerce_sales.xlsx: {df_sales.shape[0]} rows × {df_sales.shape[1]} cols")
print(f"   Missing: {df_sales.isnull().sum().sum()} | Duplicates: {df_sales.duplicated().sum()}")


# ══════════════════════════════════════════════════════════════════════
# FILE 2: Employee Performance Data
# ══════════════════════════════════════════════════════════════════════
n2 = 150

departments = ['Engineering', 'Marketing', 'Sales', 'HR', 'Finance', 'Operations']
positions = ['Junior', 'Mid-Level', 'Senior', 'Lead', 'Manager', 'Director']
offices = ['New York', 'London', 'Tokyo', 'Berlin', 'Sydney']

emp_ids = [f'EMP-{str(i).zfill(4)}' for i in range(1, n2 + 1)]
names = [f'Employee_{i}' for i in range(1, n2 + 1)]
dept_list = np.random.choice(departments, n2)
position_list = np.random.choice(positions, n2, p=[0.25, 0.30, 0.20, 0.12, 0.08, 0.05])
office_list = np.random.choice(offices, n2)

# Salary depends on position
salary_base = {'Junior': 45000, 'Mid-Level': 65000, 'Senior': 85000,
               'Lead': 100000, 'Manager': 120000, 'Director': 150000}
salaries = [salary_base[p] + np.random.randint(-5000, 15000) for p in position_list]

# Performance score 1-10
performance = np.round(np.clip(np.random.normal(7.0, 1.5, n2), 1, 10), 1)

# Years at company
years = np.random.randint(0, 20, n2)

# Projects completed
projects = np.random.randint(1, 30, n2)

# Satisfaction score
satisfaction = np.round(np.clip(np.random.normal(7.5, 1.2, n2), 1, 10), 1)

# Training hours
training = np.random.randint(0, 100, n2)

join_dates = [datetime(2010, 1, 1) + timedelta(days=int(np.random.randint(0, 5000))) for _ in range(n2)]

df_emp = pd.DataFrame({
    'Employee_ID': emp_ids,
    'Name': names,
    'Department': dept_list,
    'Position': position_list,
    'Office': office_list,
    'Join_Date': join_dates,
    'Salary': salaries,
    'Performance_Score': performance,
    'Years_at_Company': years,
    'Projects_Completed': projects,
    'Satisfaction_Score': satisfaction,
    'Training_Hours': training
})

# Inject some issues
for _ in range(5):
    df_emp.loc[np.random.randint(0, n2), 'Salary'] = np.nan
for _ in range(4):
    df_emp.loc[np.random.randint(0, n2), 'Department'] = np.nan
dup_emp = df_emp.sample(4, random_state=42)
df_emp = pd.concat([df_emp, dup_emp], ignore_index=True)

df_emp.to_excel('data/sample_employee_data.xlsx', index=False)
print(f"\n✅ sample_employee_data.xlsx: {df_emp.shape[0]} rows × {df_emp.shape[1]} cols")
print(f"   Missing: {df_emp.isnull().sum().sum()} | Duplicates: {df_emp.duplicated().sum()}")


# ══════════════════════════════════════════════════════════════════════
# FILE 3: Student Grades & Attendance (CSV format)
# ══════════════════════════════════════════════════════════════════════
n3 = 100

subjects = ['Mathematics', 'Physics', 'Chemistry', 'English', 'Computer Science']
grades = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F']

student_ids = [f'STU-{str(i).zfill(3)}' for i in range(1, n3 + 1)]
student_names = [f'Student_{i}' for i in range(1, n3 + 1)]
subject_list = np.random.choice(subjects, n3)
grade_list = np.random.choice(grades, n3, p=[0.08, 0.15, 0.20, 0.22, 0.15, 0.10, 0.06, 0.04])

marks = np.round(np.clip(np.random.normal(72, 15, n3), 0, 100), 1)
attendance_pct = np.round(np.clip(np.random.normal(82, 12, n3), 30, 100), 1)
study_hours = np.round(np.clip(np.random.normal(5, 2, n3), 0.5, 14), 1)

semester = np.random.choice(['Fall 2023', 'Spring 2024', 'Fall 2024'], n3)

df_students = pd.DataFrame({
    'Student_ID': student_ids,
    'Student_Name': student_names,
    'Subject': subject_list,
    'Semester': semester,
    'Marks': marks,
    'Grade': grade_list,
    'Attendance_%': attendance_pct,
    'Study_Hours_Per_Week': study_hours
})

# Inject missing
for _ in range(6):
    df_students.loc[np.random.randint(0, n3), 'Marks'] = np.nan
for _ in range(3):
    df_students.loc[np.random.randint(0, n3), 'Attendance_%'] = np.nan

df_students.to_csv('data/sample_student_grades.csv', index=False)
print(f"\n✅ sample_student_grades.csv: {df_students.shape[0]} rows × {df_students.shape[1]} cols")
print(f"   Missing: {df_students.isnull().sum().sum()}")


# ══════════════════════════════════════════════════════════════════════
# FILE 4: Monthly Financial Data
# ══════════════════════════════════════════════════════════════════════
months = pd.date_range(start='2022-01-01', end='2024-12-01', freq='MS')
n4 = len(months)

revenue = np.cumsum(np.random.normal(50000, 8000, n4)) + 200000
revenue = np.maximum(revenue, 50000).round(2)
expenses = revenue * np.random.uniform(0.55, 0.75, n4)
expenses = expenses.round(2)
net_profit = (revenue - expenses).round(2)
customers = np.cumsum(np.random.randint(50, 200, n4)) + 1000
marketing_spend = np.random.uniform(5000, 25000, n4).round(2)
employee_count = np.clip(np.cumsum(np.random.choice([-2, -1, 0, 1, 2, 3], n4)) + 50, 30, 200)

df_finance = pd.DataFrame({
    'Month': months,
    'Revenue': revenue,
    'Expenses': expenses,
    'Net_Profit': net_profit,
    'Total_Customers': customers,
    'New_Customers': np.random.randint(30, 180, n4),
    'Marketing_Spend': marketing_spend,
    'Employee_Count': employee_count,
    'Customer_Satisfaction': np.round(np.clip(np.random.normal(8.0, 0.8, n4), 5, 10), 1)
})

df_finance.to_excel('data/sample_financial_report.xlsx', index=False)
print(f"\n✅ sample_financial_report.xlsx: {df_finance.shape[0]} rows × {df_finance.shape[1]} cols")


# ══════════════════════════════════════════════════════════════════════
# Also keep the original simple file (updated with more data)
# ══════════════════════════════════════════════════════════════════════
# Remove old sample if exists
old_file = 'data/sample_sales.xlsx'
if os.path.exists(old_file):
    os.remove(old_file)

print("\n" + "=" * 60)
print("📁 SAMPLE FILES CREATED:")
print("=" * 60)
print("1. sample_ecommerce_sales.xlsx  - E-Commerce (258 rows, 12 cols)")
print("   → Products, Categories, Regions, Channels, Sales, Profit, Ratings")
print("   → Has duplicates, missing values, and anomalies built in")
print("")
print("2. sample_employee_data.xlsx    - HR/Employee (154 rows, 12 cols)")
print("   → Departments, Positions, Salaries, Performance, Satisfaction")
print("   → Has missing salaries and duplicate records")
print("")
print("3. sample_student_grades.csv    - Education (100 rows, 8 cols)")
print("   → Subjects, Marks, Grades, Attendance, Study Hours")
print("   → CSV format to demo CSV support")
print("")
print("4. sample_financial_report.xlsx - Finance (36 rows, 9 cols)")
print("   → Monthly Revenue, Expenses, Profit, Customers, Marketing")
print("   → Clean time-series data — great for trend analysis")
print("=" * 60)
