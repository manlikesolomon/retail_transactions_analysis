import streamlit as st
from utils import run_query
import pandas as pd
import altair as alt
import os
from pathlib import Path


def fallback_to_csv(query_name):
    try:
        # Get the current working directory and set the absolute path for the fallback_data folder
        current_dir = Path(os.getcwd())
        path = current_dir /  "streamlit_app" / "fallback_data" /f"{query_name}.csv"
        
        return pd.read_csv(path)
    except FileNotFoundError:
        st.error(f"Fallback CSV for `{query_name}` not found.")
        return pd.DataFrame()

st.set_page_config(page_title="Retail Transactions Analysis", layout="wide")

st.title("📈 Retail Transactions Metrics")

tabs = st.tabs(["Customer Analysis", "City Metrics", "Payment Behavior"])


with tabs[0]:
    st.header("🧑‍💼 Customer Analysis")
    st.subheader("Top 20 Customers by Transaction Value")
    top_customers_query = '''
                select 
                    Customer_Name,
                    any(City) as City,
                    round(sum(Total_Cost),2 ) `Total Transaction Value`,
                    count() as `Total Transaction Count`,
                    max(Date) as `Last Transaction Date`
                from raw.retail_transactions
                group by Customer_Name
                order by `Total Transaction Value` desc
                limit 20
    '''
    try:
        df_top_customers = run_query(top_customers_query)
    except Exception:
        
        df_top_customers = fallback_to_csv("top_customers")
    st.dataframe(df_top_customers)

    st.subheader("📈 Promotion Responsiveness (Scatter Plot)")

    promo_query = '''
                select 
                    Customer_Name,
                    countIf(Promotion != 'None') as Promo_Transactions,
                    count() as Total_Transactions,
                    round(100 * countIf(Promotion != 'None') / count(), 2) as Promo_Response_Rate
                from raw.retail_transactions
                group by Customer_Name
                having Promo_Transactions >= 5 and Total_Transactions >= 5
                order by Promo_Response_Rate desc
    '''
    try:
        df_promo = run_query(promo_query)
    except Exception:
        
        df_promo = fallback_to_csv("promo_response")

    scatter = alt.Chart(df_promo).mark_circle().encode(
        x='Total_Transactions:Q',
        y='Promo_Transactions:Q',
        size='Promo_Response_Rate:Q',
        color=alt.Color('Promo_Response_Rate:Q', scale=alt.Scale(scheme='blues')),
        tooltip=['Customer_Name', 'Promo_Response_Rate', 'Promo_Transactions', 'Total_Transactions']
    ).properties(
        title="Promotion Engagement by Customers"
    )

    st.altair_chart(scatter, use_container_width=True)

    st.subheader("🧮 Promotion Responsiveness Buckets")

    def classify_response(rate):
        if rate >= 75:
            return 'Highly Responsive'
        elif rate >= 50:
            return 'Moderately Responsive'
        else:
            return 'Low Responsive'

    df_promo['Responsiveness Category'] = df_promo['Promo_Response_Rate'].apply(classify_response)
    df_bucket = df_promo['Responsiveness Category'].value_counts().reset_index()
    df_bucket.columns = ['Category', 'Count']

    donut = alt.Chart(df_bucket).mark_arc(innerRadius=50).encode(
        theta='Count:Q',
        color='Category:N',
        tooltip=['Category', 'Count']
    ).properties(
        title="Distribution of Customer Promo Responsiveness"
    )

    st.altair_chart(donut, use_container_width=True)

    st.subheader("🔥 Customer Loyalty Score")

    loyalty_query = '''
                SELECT 
                    Customer_Name,
                    COUNT() AS Total_Transactions,
                    max(Date) AS Last_Transaction_Date,
                    dateDiff('day', max(Date), now()) AS Days_Since_Last_Purchase,
                    round(COUNT() / (1 + dateDiff('day', max(Date), now())), 2) AS Loyalty_Score
                FROM raw.retail_transactions
                GROUP BY Customer_Name
                ORDER BY Loyalty_Score DESC
                LIMIT 20
    '''
    try:
        df_loyalty = run_query(loyalty_query)
    except Exception:
        
        df_loyalty = fallback_to_csv("loyalty_score")

    loyalty_chart = alt.Chart(df_loyalty).mark_bar().encode(
        x=alt.X('Customer_Name:N', sort='-y'),
        y='Loyalty_Score:Q',
        tooltip=['Customer_Name', 'Total_Transactions', 'Last_Transaction_Date', 'Days_Since_Last_Purchase', 'Loyalty_Score']
    ).properties(
        title='Top 20 Loyal Customers'
    )

    st.altair_chart(loyalty_chart, use_container_width=True)

with tabs[1]:
    st.header("🗺️ City-Level Metrics")
    metrics_query = '''
                select 
                    city as City,
                    sum(total_transactions) as `Transaction Count`,
                    round(sum(total_revenue), 2) as `Total Revenue`,
                    round(avg(avg_transaction_value),2) as `Average Transaction Value`
                from summary.daily_city_metrics
                group by City
        '''
    try:
        df_city = run_query(metrics_query)
    except Exception:
        
        df_city = fallback_to_csv("city_metrics")
    st.dataframe(df_city)
    chart = alt.Chart(df_city).mark_bar().encode(
        x=alt.X('City', sort='-y'),
        y='Transaction Count',
        tooltip=['City', 'Transaction Count', 'Total Revenue', 'Average Transaction Value']
    ).properties(
        title='City-Level Transaction Metrics'
    ).interactive()
    st.altair_chart(chart, use_container_width=True)

    st.subheader("📊 Year-on-Year Revenue and Transaction Trends")

    yoy_query = '''
                select 
                    City,
                    toYear(Date) AS Year,
                    COUNT() AS `Transaction Count`,
                    ROUND(SUM(Total_Cost), 2) AS `Total Revenue`
                from raw.retail_transactions
                group by City, Year
                order by Year, City
        '''
    try:
        df_yoy = run_query(yoy_query)
    except Exception:
        
        df_yoy = fallback_to_csv("yoy_city")
    
    selected_city = st.selectbox("Select a City", sorted(df_yoy["City"].unique()))
    city_df = df_yoy[df_yoy["City"] == selected_city]

    base = alt.Chart(city_df).encode(x='Year:O')

    revenue_line = base.mark_line(color='blue').encode(
    y=alt.Y('Total Revenue:Q', axis=alt.Axis(title='Total Revenue')),
    tooltip=['Year', 'Total Revenue']
    )

    transaction_line = base.mark_line(color='orange').encode(
        y=alt.Y('Transaction Count:Q', axis=alt.Axis(title='Transaction Count')),
        tooltip=['Year', 'Transaction Count']
    )

    combined_chart = alt.layer(revenue_line, transaction_line).resolve_scale(
        y='independent'
    ).properties(
        title=f"Year-on-Year Revenue & Transactions - {selected_city}"
    )

    st.altair_chart(combined_chart, use_container_width=True)

with tabs[2]:
    st.header("💳 Payment Behavior")
    metrics_query = '''
                select 
                    Payment_Method,
                    count() as `Transaction Count`,
                    round(sum(Total_Cost), 2) `Total Transaction Value`,
                    round(avg(Total_Items), 2) as `Average Cart Size`
                from raw.retail_transactions
                group by Payment_Method'''
    try:
        df_payment = run_query(metrics_query)
    except Exception:
        
        df_payment = fallback_to_csv("payment_metrics")
    st.dataframe(df_payment)

    st.subheader("📊 Year-on-Year Payment Method Trends")

    yoy_payment_query = '''
                select 
                    toYear(Date) AS Year,
                    Payment_Method,
                    count() as `Transaction Count`,
                    round(sum(Total_Cost), 2) `Total Transaction Value`
                from raw.retail_transactions
                group by Year, Payment_Method
                order by Year, Payment_Method
    '''
    try:
        df_yoy_payment = run_query(yoy_payment_query)
    except Exception:
        
        df_yoy_payment = fallback_to_csv("yoy_payment")

    payment_selected = st.selectbox("Select a Payment Method", sorted(df_yoy_payment["Payment_Method"].unique()))
    payment_df = df_yoy_payment[df_yoy_payment["Payment_Method"] == payment_selected]

    base = alt.Chart(payment_df).encode(x='Year:O')

    tx_count_line = base.mark_line(color='green').encode(
        y=alt.Y('Transaction Count:Q', axis=alt.Axis(title='Transaction Count')),
        tooltip=['Year', 'Transaction Count']
    )

    total_value_line = base.mark_line(color='purple').encode(
        y=alt.Y('Total Transaction Value:Q', axis=alt.Axis(title='Total Transaction Value')),
        tooltip=['Year', 'Total Transaction Value']
    )

    combined_chart = alt.layer(tx_count_line, total_value_line).resolve_scale(
        y='independent'
    ).properties(
        title=f"Year-on-Year Trends for {payment_selected}"
    )

    st.altair_chart(combined_chart, use_container_width=True)

    st.subheader("💸 Average Transaction Value by Payment Method")

    avg_tx_query = '''
            SELECT 
                Payment_Method,
                ROUND(SUM(Total_Cost)/COUNT(), 2) AS Avg_Transaction_Value
            FROM raw.retail_transactions
            GROUP BY Payment_Method
    '''
    try:
        df_avg_tx = run_query(avg_tx_query)
    except Exception:
        df_avg_tx = fallback_to_csv("avg_tx_by_payment")

    bar_chart = alt.Chart(df_avg_tx).mark_bar().encode(
        x=alt.X('Payment_Method:N', sort='-y'),
        y='Avg_Transaction_Value:Q',
        tooltip=['Payment_Method', 'Avg_Transaction_Value']
    ).properties(
        title='Average Transaction Value by Payment Method'
    )

    st.altair_chart(bar_chart, use_container_width=True)