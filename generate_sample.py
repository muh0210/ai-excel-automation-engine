"""
Generate comprehensive sample/dummy data files for demo purposes.
Creates multiple example files covering different data scenarios,
INCLUDING joinable file pairs for the Smart Join feature.
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

base_qty = np.random.randint(1, 25, n)
quantity = base_qty

sales = np.array([price_map[p] * q for p, q in zip(product_list, quantity)])
noise = np.random.normal(0, 50, n)
sales = np.maximum(sales + noise, 10).round(2)

margin_base = {'Online': 0.25, 'Retail Store': 0.18, 'Wholesale': 0.10}
margins = np.array([margin_base[c] + np.random.uniform(-0.05, 0.10) for c in channel_list])
profit = (sales * margins).round(2)

discounts = np.random.choice([0, 5, 10, 15, 20, 25], n, p=[0.3, 0.25, 0.2, 0.12, 0.08, 0.05])
ratings = np.round(np.clip(np.random.normal(4.0, 0.7, n), 1, 5), 1)

df_sales = pd.DataFrame({
    'Date': dates, 'Product': product_list, 'Category': category_list,
    'Region': region_list, 'Sales_Channel': channel_list,
    'Customer_Type': customer_list, 'Unit_Price': unit_prices,
    'Quantity': quantity, 'Sales': sales, 'Discount_%': discounts,
    'Profit': profit, 'Rating': ratings
})

for idx in [42, 87, 155, 210]:
    if idx < len(df_sales):
        df_sales.loc[idx, 'Sales'] = df_sales.loc[idx, 'Sales'] * 5
        df_sales.loc[idx, 'Profit'] = df_sales.loc[idx, 'Profit'] * 5

for _ in range(12): df_sales.loc[np.random.randint(0, n), 'Sales'] = np.nan
for _ in range(8):  df_sales.loc[np.random.randint(0, n), 'Region'] = np.nan
for _ in range(5):  df_sales.loc[np.random.randint(0, n), 'Rating'] = np.nan
for _ in range(6):  df_sales.loc[np.random.randint(0, n), 'Profit'] = np.nan

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

salary_base = {'Junior': 45000, 'Mid-Level': 65000, 'Senior': 85000,
               'Lead': 100000, 'Manager': 120000, 'Director': 150000}
salaries = [salary_base[p] + np.random.randint(-5000, 15000) for p in position_list]

performance = np.round(np.clip(np.random.normal(7.0, 1.5, n2), 1, 10), 1)
years = np.random.randint(0, 20, n2)
projects = np.random.randint(1, 30, n2)
satisfaction = np.round(np.clip(np.random.normal(7.5, 1.2, n2), 1, 10), 1)
training = np.random.randint(0, 100, n2)
join_dates = [datetime(2010, 1, 1) + timedelta(days=int(np.random.randint(0, 5000))) for _ in range(n2)]

df_emp = pd.DataFrame({
    'Employee_ID': emp_ids, 'Name': names, 'Department': dept_list,
    'Position': position_list, 'Office': office_list, 'Join_Date': join_dates,
    'Salary': salaries, 'Performance_Score': performance,
    'Years_at_Company': years, 'Projects_Completed': projects,
    'Satisfaction_Score': satisfaction, 'Training_Hours': training
})

for _ in range(5): df_emp.loc[np.random.randint(0, n2), 'Salary'] = np.nan
for _ in range(4): df_emp.loc[np.random.randint(0, n2), 'Department'] = np.nan
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
    'Student_ID': student_ids, 'Student_Name': student_names,
    'Subject': subject_list, 'Semester': semester, 'Marks': marks,
    'Grade': grade_list, 'Attendance_%': attendance_pct,
    'Study_Hours_Per_Week': study_hours
})

for _ in range(6): df_students.loc[np.random.randint(0, n3), 'Marks'] = np.nan
for _ in range(3): df_students.loc[np.random.randint(0, n3), 'Attendance_%'] = np.nan

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
    'Month': months, 'Revenue': revenue, 'Expenses': expenses,
    'Net_Profit': net_profit, 'Total_Customers': customers,
    'New_Customers': np.random.randint(30, 180, n4),
    'Marketing_Spend': marketing_spend, 'Employee_Count': employee_count,
    'Customer_Satisfaction': np.round(np.clip(np.random.normal(8.0, 0.8, n4), 5, 10), 1)
})

df_finance.to_excel('data/sample_financial_report.xlsx', index=False)
print(f"\n✅ sample_financial_report.xlsx: {df_finance.shape[0]} rows × {df_finance.shape[1]} cols")


# ══════════════════════════════════════════════════════════════════════
# FILE 5: SMART JOIN PAIR — Orders + Customers
#   Upload orders first, then customers as 2nd file → auto-join on Customer_ID
# ══════════════════════════════════════════════════════════════════════
n5 = 200

cust_ids = [f'CUST-{str(i).zfill(4)}' for i in range(1, 81)]
order_cust = np.random.choice(cust_ids, n5)
order_dates = [datetime(2024, 1, 1) + timedelta(days=int(x)) for x in np.sort(np.random.randint(0, 365, n5))]
order_products = np.random.choice(['Widget A', 'Widget B', 'Gadget X', 'Gadget Y', 'Service Plan'], n5)
order_amounts = np.round(np.random.uniform(25, 2500, n5), 2)
order_status = np.random.choice(['Completed', 'Pending', 'Cancelled', 'Refunded'], n5, p=[0.65, 0.15, 0.12, 0.08])
payment_method = np.random.choice(['Credit Card', 'PayPal', 'Bank Transfer', 'Cash'], n5, p=[0.45, 0.25, 0.20, 0.10])

df_orders = pd.DataFrame({
    'Order_ID': [f'ORD-{str(i).zfill(5)}' for i in range(1, n5+1)],
    'Customer_ID': order_cust,
    'Order_Date': order_dates,
    'Product': order_products,
    'Amount': order_amounts,
    'Status': order_status,
    'Payment_Method': payment_method,
})

# Inject some missing values and placeholders
for _ in range(8): df_orders.loc[np.random.randint(0, n5), 'Amount'] = np.nan
for _ in range(5): df_orders.loc[np.random.randint(0, n5), 'Status'] = ''
for _ in range(3): df_orders.loc[np.random.randint(0, n5), 'Payment_Method'] = 'N/A'

df_orders.to_excel('data/sample_orders.xlsx', index=False)
print(f"\n✅ sample_orders.xlsx: {df_orders.shape[0]} rows × {df_orders.shape[1]} cols (SMART JOIN — primary file)")
print(f"   Missing: {df_orders.isnull().sum().sum()} | Placeholders: 8 injected")

# Customer master table (join target)
cust_names = [f'Customer {chr(65 + i//26)}{chr(65 + i%26)}' for i in range(80)]
cust_regions = np.random.choice(['North America', 'Europe', 'Asia Pacific', 'Latin America', 'Middle East'], 80)
cust_tiers = np.random.choice(['Bronze', 'Silver', 'Gold', 'Platinum'], 80, p=[0.35, 0.30, 0.25, 0.10])
cust_signup = [datetime(2020, 1, 1) + timedelta(days=int(np.random.randint(0, 1500))) for _ in range(80)]
cust_lifetime = np.round(np.random.uniform(100, 50000, 80), 2)
cust_email = [f'{name.lower().replace(" ", ".")}@example.com' for name in cust_names]

df_customers = pd.DataFrame({
    'Customer_ID': cust_ids,
    'Customer_Name': cust_names,
    'Email': cust_email,
    'Region': cust_regions,
    'Tier': cust_tiers,
    'Signup_Date': cust_signup,
    'Lifetime_Value': cust_lifetime,
    'Credit_Limit': np.round(np.random.uniform(1000, 25000, 80), 2),
})

df_customers.to_excel('data/sample_customers.xlsx', index=False)
print(f"✅ sample_customers.xlsx: {df_customers.shape[0]} rows × {df_customers.shape[1]} cols (SMART JOIN — second file)")


# ══════════════════════════════════════════════════════════════════════
# FILE 6: SMART JOIN PAIR — Products + Inventory
#   Upload products first, then inventory as 2nd file → auto-join on SKU
# ══════════════════════════════════════════════════════════════════════
n6 = 60
skus = [f'SKU-{str(i).zfill(4)}' for i in range(1, n6+1)]

df_products = pd.DataFrame({
    'SKU': skus,
    'Product_Name': [f'Product {chr(65+i//26)}{chr(65+i%26)}' for i in range(n6)],
    'Category': np.random.choice(['Electronics', 'Clothing', 'Food', 'Home', 'Sports'], n6),
    'Brand': np.random.choice(['BrandA', 'BrandB', 'BrandC', 'BrandD', 'BrandE'], n6),
    'Cost_Price': np.round(np.random.uniform(5, 200, n6), 2),
    'Retail_Price': np.round(np.random.uniform(15, 500, n6), 2),
    'Weight_kg': np.round(np.random.uniform(0.1, 15, n6), 2),
    'Supplier': np.random.choice(['Supplier 1', 'Supplier 2', 'Supplier 3', 'Supplier 4'], n6),
})

df_products.to_excel('data/sample_products.xlsx', index=False)
print(f"\n✅ sample_products.xlsx: {df_products.shape[0]} rows × {df_products.shape[1]} cols (SMART JOIN — primary file)")

# Inventory table (join target) — uses same SKUs but different columns
warehouses = ['Warehouse A', 'Warehouse B', 'Warehouse C']
inv_rows = []
for sku in skus[:50]:  # only 50 of 60 SKUs in stock (tests partial match)
    for wh in np.random.choice(warehouses, np.random.randint(1, 4), replace=False):
        inv_rows.append({
            'SKU': sku,
            'Warehouse': wh,
            'Qty_In_Stock': int(np.random.randint(0, 500)),
            'Reorder_Level': int(np.random.randint(10, 100)),
            'Last_Restock_Date': (datetime(2024, 6, 1) + timedelta(days=int(np.random.randint(-180, 0)))).strftime('%Y-%m-%d'),
        })

df_inventory = pd.DataFrame(inv_rows)
df_inventory.to_csv('data/sample_inventory.csv', index=False)
print(f"✅ sample_inventory.csv: {df_inventory.shape[0]} rows × {df_inventory.shape[1]} cols (SMART JOIN — second file)")
print(f"   Note: Only 50/60 SKUs have inventory → tests partial-match join quality scoring")


# ══════════════════════════════════════════════════════════════════════
# FILE 7: Simple Budget vs Actual (Finance module demo)
# ══════════════════════════════════════════════════════════════════════
budget_categories = [
    'Marketing', 'Engineering', 'Sales', 'Operations', 'HR',
    'R&D', 'Legal', 'IT Support', 'Admin', 'Customer Service',
    'Facilities', 'Training'
]

budget_amounts = [120000, 350000, 200000, 150000, 95000, 280000, 75000, 110000, 60000, 130000, 85000, 45000]
# Actuals vary ± 30% from budget
actual_amounts = [round(b * np.random.uniform(0.70, 1.35)) for b in budget_amounts]

df_budget = pd.DataFrame({
    'Department': budget_categories,
    'Budget_Amount': budget_amounts,
    'Actual_Amount': actual_amounts,
    'Quarter': np.random.choice(['Q1', 'Q2', 'Q3', 'Q4'], len(budget_categories)),
    'Fiscal_Year': '2024',
    'Manager': [f'Manager_{chr(65+i)}' for i in range(len(budget_categories))],
})

# Add tax column for tax/VAT audit demo
df_budget['Tax_Amount'] = np.round(np.array(actual_amounts) * np.random.uniform(0.05, 0.18, len(budget_categories)), 2)
# Inject one zero-tax anomaly
df_budget.loc[3, 'Tax_Amount'] = 0
# Inject one negative tax (credit/refund)
df_budget.loc[7, 'Tax_Amount'] = -500

df_budget.to_excel('data/sample_budget_vs_actual.xlsx', index=False)
print(f"\n✅ sample_budget_vs_actual.xlsx: {df_budget.shape[0]} rows × {df_budget.shape[1]} cols (Finance module demo)")
print(f"   Budget variance + Tax/VAT audit features")


# ══════════════════════════════════════════════════════════════════════
# FILE 8: Messy Data (edge-case stress test)
#   Lots of missing markers, mixed types, placeholder values
# ══════════════════════════════════════════════════════════════════════
n8 = 80

df_messy = pd.DataFrame({
    'ID': range(1, n8+1),
    'Name': [np.random.choice(['Alice', 'Bob', '', 'N/A', '-', 'Charlie', 'Diana', None, '  ', 'Eve']) for _ in range(n8)],
    'Score': [np.random.choice([85, 92, None, 'N/A', '', '-', 78, 95, 0, 63]) for _ in range(n8)],
    'City': [np.random.choice(['New York', 'London', 'n/a', 'missing', 'Tokyo', '', None, '---', 'Berlin']) for _ in range(n8)],
    'Amount': np.round(np.random.uniform(-50, 5000, n8), 2),
    'Status': [np.random.choice(['Active', 'Inactive', 'NULL', 'none', '', 'Pending', '-']) for _ in range(n8)],
    'Date': [np.random.choice(['2024-01-15', '2024-03-22', '', 'N/A', '2024-06-01', None, '2024-09-10']) for _ in range(n8)],
    'Rating': [np.random.choice([4.5, 3.2, None, 'nil', '', 4.8, 2.1, 'not available']) for _ in range(n8)],
})

df_messy.to_csv('data/sample_messy_data.csv', index=False)
print(f"\n✅ sample_messy_data.csv: {df_messy.shape[0]} rows × {df_messy.shape[1]} cols (Edge-case stress test)")
print(f"   Contains: empty strings, N/A, -, null, nil, not available, spaces, mixed types")


# ══════════════════════════════════════════════════════════════════════
# Remove old sample if exists
# ══════════════════════════════════════════════════════════════════════
old_file = 'data/sample_sales.xlsx'
if os.path.exists(old_file):
    os.remove(old_file)

print("\n" + "=" * 70)
print("📁 SAMPLE FILES CREATED:")
print("=" * 70)
print()
print("  SIMPLE UPLOAD FILES:")
print("  1. sample_ecommerce_sales.xlsx  - E-Commerce (258 rows, 12 cols)")
print("  2. sample_employee_data.xlsx    - HR/Employee (154 rows, 12 cols)")
print("  3. sample_student_grades.csv    - Education (100 rows, 8 cols)")
print("  4. sample_financial_report.xlsx - Finance time-series (36 rows, 9 cols)")
print("  5. sample_budget_vs_actual.xlsx - Budget variance + Tax audit (12 rows, 8 cols)")
print("  6. sample_messy_data.csv        - Messy data stress test (80 rows, 8 cols)")
print()
print("  SMART JOIN PAIRS (upload file 1 first, then file 2 as second):")
print("  7. sample_orders.xlsx     +  sample_customers.xlsx  → Join on Customer_ID")
print("  8. sample_products.xlsx   +  sample_inventory.csv   → Join on SKU")
print()
print("=" * 70)
