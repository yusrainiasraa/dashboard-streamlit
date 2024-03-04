import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

# Helper Function for preparing dataframes
def create_orders_month(df):
    orders_month_df = df.resample(rule='M', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "payment_value": "sum"
    })
    orders_month_df = orders_month_df.reset_index()
    return orders_month_df

def create_top7_category(df):
    top7_category_df = data['product_category_name_english'].value_counts().head(7).reset_index()
    return top7_category_df

def create_ratings(df):
    ratings_df = data['review_score'].value_counts().sort_index(ascending=True).reset_index()
    return ratings_df

def create_type_payment(df):
    type_payment_df = data['payment_type'].value_counts().reset_index()
    return type_payment_df

def create_canceled_order(df):
    canceled = data[data['order_status'] == 'canceled']
    canceled_order_df = canceled['product_category_name_english'].value_counts().reset_index()
    return canceled_order_df

def create_rfm_df(df):
    rfm_df = data.groupby(by="review_score", as_index=False).agg({
    "order_purchase_timestamp": "max", # last order date
    "order_id": "nunique", # order count
    "payment_value": "sum" # total revenue
    })
    rfm_df.columns = ["review_score", "max_order_timestamp", "frequency", "monetary"]

    # last made order
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    date_recent = data["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (date_recent - x).days)
    
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    return rfm_df

# Load Data
data = pd.read_csv("dashboard/main_data.csv")

datetime_columns = ["order_estimated_delivery_date", "order_delivered_customer_date", "order_purchase_timestamp"]
data.sort_values(by="order_purchase_timestamp", inplace=True)
data.reset_index(inplace=True)

for column in datetime_columns:
    data[column] = pd.to_datetime(data[column])

# Filter Data
date_min = data["order_purchase_timestamp"].min()
date_max = data["order_purchase_timestamp"].max()

# Sidebar
with st.sidebar:
    st.header('Olist E-Commerce')
    st.image("https://storage.googleapis.com/kaggle-datasets-images/55151/105464/d59245a7014a35a35cc7f7b721de4dae/dataset-cover.png?t=2018-09-21-16-21-21") # Adding Olist Logo from Kaggle
    st.subheader('Pick the Date Below')

    # Input Start date
    start_date = st.date_input(
        label='Start Date',
        min_value=date_min,
        max_value=date_max,
        value=date_min
    )

    # Input End Date
    end_date = st.date_input(
        label='End Date',
        min_value=date_min,
        max_value=date_max,
        value=date_max
    )

# Global Condition
main_df = data[(data["order_purchase_timestamp"] >= str(start_date)) & (data["order_purchase_timestamp"] <= str(end_date))]

# Preparing Dataframes
orders_month_df = create_orders_month(main_df)
top7_category_df = create_top7_category(main_df)
ratings_df = create_ratings(main_df)
type_payment_df = create_type_payment(main_df)
canceled_order_df = create_canceled_order(main_df)
rfm_df = create_rfm_df(main_df)

# Dashboard
st.header(':sparkles: Olist E-Commerce Dashboard :sparkles:')

# Summary Report
st.subheader('Summary Report')
col1, col2, col3 = st.columns(3)
with col1:
    total_orders = orders_month_df.order_id.sum()
    st.metric("Total Orders", value=total_orders)
with col2:
    average_rating = round(data['review_score'].mean(), 1)
    st.metric("Average Rating", value=average_rating)
with col3:
    total_revenue = format_currency(orders_month_df.payment_value.sum(), 'USD', locale='en_US') 
    st.metric("Total Revenue", value=total_revenue)

# Data Visualization
pastel_colors = sns.color_palette("pastel")

## Trend Orders by Month
st.subheader('Trend Orders by Month')
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(orders_month_df['order_purchase_timestamp'],
        orders_month_df['order_id']
)
ax.set_xlabel('Month')
ax.set_ylabel('Frequency')
st.pyplot(fig)

## Top 7 Category Products
st.subheader('Top 7 Category Products')
fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(x="product_category_name_english", 
            y="count",
            data=top7_category_df.sort_values(by="count", ascending=False),
            palette=['skyblue','grey','grey','grey','grey','grey','grey'],
            ax=ax
)
ax.set_xlabel('Product\'s Category')
ax.set_ylabel('Orders')
st.pyplot(fig)

## Ratings
st.subheader('Ratings')
fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(x="review_score", 
            y="count",
            data=ratings_df.sort_values(by="review_score", ascending=False),
            ax=ax
)
ax.set_xlabel('Rating Scale')
ax.set_ylabel('Rating Count')
st.pyplot(fig)

## Payment Type Percentage
st.subheader('Payment Type Percentage')
fig, ax = plt.subplots(figsize=(12, 6))
ax.pie(type_payment_df['count'],
       autopct='%1.1f%%',
       explode=[0.05, 0.025, 0.025, 0.025],
       colors=pastel_colors,
       labels=None,
       shadow=True,
       pctdistance=1.2,
       startangle=45)
ax.legend(labels=type_payment_df['payment_type'],loc='upper left')
ax.axis('equal')
st.pyplot(fig)

## Canceled Order Products
st.subheader('Canceled Order Products')
fig, ax = plt.subplots(figsize=(12, 6))
ax.pie(x=canceled_order_df['count'],
       labels=canceled_order_df['product_category_name_english'],
       wedgeprops = {'width': 0.4},
       colors=pastel_colors
)
st.pyplot(fig)

## Summary RFM Analysis on Ratings (review_score)
st.subheader("Rating Based on RFM Parameters (review_score)")
col1, col2, col3 = st.columns(3)
with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)
with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)
with col3:
    avg_monetary = format_currency(round(rfm_df.monetary.mean(),2), 'USD', locale='en_US') 
    st.metric("Average Monetary", value=avg_monetary)

## Visualization RFM Analysis on Ratings (review_score)
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 6))
### Recency
sns.barplot(y="recency", x="review_score", data=rfm_df.sort_values(by="recency", ascending=True).head(5), ax=ax[0])
ax[0].set_title("By Recency (days)", loc="center", fontsize=18)
ax[0].tick_params(axis ='x', labelsize=15)
### Frequency
sns.barplot(y="frequency", x="review_score", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), ax=ax[1])
ax[1].set_title("By Frequency", loc="center", fontsize=18)
ax[1].tick_params(axis='x', labelsize=15)
### Monetary
sns.barplot(y="monetary", x="review_score", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), ax=ax[2])
ax[2].set_title("By Monetary", loc="center", fontsize=18)
ax[2].tick_params(axis='x', labelsize=15)
st.pyplot(fig)

st.caption('Copyright (c) yusrainiasraa')