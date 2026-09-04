import streamlit as st
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="E-Commerce Customer Retention Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 E-Commerce Customer Retention Dashboard")

# Load dataset
retail = pd.read_excel("Online Retail.xlsx")

# Convert InvoiceDate
retail["InvoiceDate"] = pd.to_datetime(retail["InvoiceDate"])

# Clean transaction data
retail = retail.dropna(subset=["CustomerID"]).copy()

retail = retail[
    (retail["Quantity"] > 0) &
    (retail["UnitPrice"] > 0)
].copy()

# Remove cancelled/returned orders
retail = retail[
    ~retail["InvoiceNo"].astype(str).str.startswith("C")
].copy()

# Create date column
retail["Date"] = retail["InvoiceDate"].dt.date

# Sidebar
st.sidebar.header("Date Filter")

min_date = retail["Date"].min()
max_date = retail["Date"].max()

start_date = st.sidebar.date_input(
    "Start Date",
    value=min_date,
    min_value=min_date,
    max_value=max_date
)

end_date = st.sidebar.date_input(
    "End Date",
    value=max_date,
    min_value=min_date,
    max_value=max_date
)

# Check date selection
if start_date > end_date:
    st.error("Start Date cannot be after End Date.")
    st.stop()

# Filter data according to selected dates
filtered_data = retail[
    (retail["Date"] >= start_date) &
    (retail["Date"] <= end_date)
].copy()

# Create transaction month
filtered_data["InvoiceMonth"] = (
    filtered_data["InvoiceDate"]
    .dt.to_period("M")
)

# Find each customer's first purchase month
customer_cohort = (
    filtered_data.groupby("CustomerID")["InvoiceMonth"]
    .min()
    .reset_index()
)

customer_cohort.rename(
    columns={"InvoiceMonth": "CohortMonth"},
    inplace=True
)

# Add cohort month to transactions
filtered_data = filtered_data.merge(
    customer_cohort,
    on="CustomerID",
    how="left"
)

# Calculate month number after first purchase
filtered_data["CohortIndex"] = (
    (filtered_data["InvoiceMonth"].dt.year -
     filtered_data["CohortMonth"].dt.year) * 12
    +
    (filtered_data["InvoiceMonth"].dt.month -
     filtered_data["CohortMonth"].dt.month)
    + 1
)

# Count unique customers in each cohort/month
cohort_data = (
    filtered_data
    .groupby(["CohortMonth", "CohortIndex"])["CustomerID"]
    .nunique()
    .reset_index()
)

# Create retention matrix
retention_matrix = cohort_data.pivot(
    index="CohortMonth",
    columns="CohortIndex",
    values="CustomerID"
)

# Calculate retention percentage
retention_percentage = retention_matrix.divide(
    retention_matrix.iloc[:, 0],
    axis=0
) * 100

# Round percentages
retention_percentage = retention_percentage.round(1)

# Dashboard
st.subheader("Monthly Cohort Retention Matrix")

st.write(
    "The table below shows the percentage of customers "
    "from each monthly cohort who remained active in later months."
)

# Display retention heatmap
styled_retention = (
    retention_percentage.style
    .background_gradient(
        cmap="Blues",
        axis=None
    )
    .format("{:.1f}%", na_rep="")
    .highlight_null(
        props="background-color: white; color: white;"
    )
)

st.dataframe(
    styled_retention,
    use_container_width=True
)