
# India Trade Flow Dashboard - Streamlit Version

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import io
import base64


st.set_page_config(
    page_title="India Trade Flow Dashboard",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #FF6B35;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #FF6B35;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .insight-box {
        background: #0a0a0a;
        padding: 1rem;
        border-left: 4px solid #FF6B35;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .stSelectbox > div > div {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data_from_db(db_path='india_trade.db'):
    """
    Load data from SQLite database
    
    This function is cached so data loads only once for better performance
    """
    try:
        conn = sqlite3.connect(db_path)
        
        
        query = "SELECT * FROM trade_data LIMIT 300000"  
        df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

@st.cache_data
def load_sample_data():
    """
    Create sample data if database is not available
    This ensures the dashboard works even without the actual database
    """
    np.random.seed(42)
    
    countries = ['USA', 'China', 'Germany', 'UAE', 'Japan', 'UK', 'Singapore', 'Netherlands', 'France', 'Italy']
    commodities = ['Electronics', 'Textiles', 'Pharmaceuticals', 'Machinery', 'Chemicals', 'Food Products', 'Automobiles', 'Jewelry']
    years = list(range(2018, 2024))
    trade_types = ['Import', 'Export']
    
    data = []
    for _ in range(5000):  
        data.append({
            'country': np.random.choice(countries),
            'hs_section': np.random.choice(commodities),
            'year': np.random.choice(years),
            'trade_type': np.random.choice(trade_types),
            'value_usd': np.random.uniform(100000, 50000000),
            'hs_code': f"{np.random.randint(1000, 9999):04d}",
            'commodity': f"Sample {np.random.choice(commodities)} Product"
        })
    
    return pd.DataFrame(data)

def create_overview_metrics(df):
    """Create key metrics overview"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_trade = df['value_usd'].sum()
        st.markdown(f"""
        <div class="metric-card">
            <h3>Total Trade Volume</h3>
            <h2>${total_trade:,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_countries = df['country'].nunique()
        st.markdown(f"""
        <div class="metric-card">
            <h3>Trading Partners</h3>
            <h2>{total_countries}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_commodities = df['hs_section'].nunique()
        st.markdown(f"""
        <div class="metric-card">
            <h3>Commodity Sectors</h3>
            <h2>{total_commodities}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        year_range = f"{df['year'].min()} - {df['year'].max()}"
        st.markdown(f"""
        <div class="metric-card">
            <h3>Time Period</h3>
            <h2>{year_range}</h2>
        </div>
        """, unsafe_allow_html=True)

def create_trade_balance_by_sector(df):
    """Create trade balance analysis by sector showing both deficit and surplus"""
    
    # Calculate trade balance by sector
    sector_trade = df.groupby(['hs_section', 'trade_type'])['value_usd'].sum().reset_index()
    sector_pivot = sector_trade.pivot(index='hs_section', columns='trade_type', values='value_usd').fillna(0)
    
    if 'Import' in sector_pivot.columns and 'Export' in sector_pivot.columns:
        sector_pivot['Trade_Balance'] = sector_pivot['Export'] - sector_pivot['Import']
        
        # Sort by trade balance to show both extremes
        sector_pivot = sector_pivot.sort_values('Trade_Balance', ascending=True)
        
        # Get top 5 deficit and top 5 surplus sectors
        deficit_sectors = sector_pivot.head(5)  # Most negative (deficit)
        surplus_sectors = sector_pivot.tail(5)  # Most positive (surplus)
        
        # Combine for visualization
        combined_sectors = pd.concat([deficit_sectors, surplus_sectors]).drop_duplicates()
        
        # Create the chart
        fig = go.Figure()
        
        # Color coding: red for deficit, green for surplus
        colors = ['#ff4444' if x < 0 else '#44ff44' for x in combined_sectors['Trade_Balance']]
        
        fig.add_trace(go.Bar(
            y=combined_sectors.index,
            x=combined_sectors['Trade_Balance'],
            orientation='h',
            marker_color=colors,
            name='Trade Balance',
            text=[f'${x:,.0f}' for x in combined_sectors['Trade_Balance']],
            textposition='outside'
        ))
        
        # Add a vertical line at x=0 to separate deficit from surplus
        fig.add_vline(x=0, line_dash="dash", line_color="black", line_width=2)
        
        fig.update_layout(
            title="Trade Balance by Commodity Sector (Top 5 Deficit & Top 5 Surplus)",
            xaxis_title="Trade Balance (USD)",
            yaxis_title="Commodity Sector",
            height=600,
            showlegend=False
        )
        
        # Add annotations for deficit and surplus sides
        fig.add_annotation(
            x=combined_sectors['Trade_Balance'].min() * 0.5,
            y=len(combined_sectors) * 0.9,
            text="DEFICIT<br>(Imports > Exports)",
            showarrow=False,
            font=dict(size=12, color="red"),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="red",
            borderwidth=1
        )
        
        fig.add_annotation(
            x=combined_sectors['Trade_Balance'].max() * 0.5,
            y=len(combined_sectors) * 0.9,
            text="SURPLUS<br>(Exports > Imports)",
            showarrow=False,
            font=dict(size=12, color="green"),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="green",
            borderwidth=1
        )
        
        return fig, combined_sectors
    
    return None, None

def create_detailed_balance_table(df):
    """Create a detailed table showing all sectors with trade balance"""
    
    sector_trade = df.groupby(['hs_section', 'trade_type'])['value_usd'].sum().reset_index()
    sector_pivot = sector_trade.pivot(index='hs_section', columns='trade_type', values='value_usd').fillna(0)
    
    if 'Import' in sector_pivot.columns and 'Export' in sector_pivot.columns:
        sector_pivot['Trade_Balance'] = sector_pivot['Export'] - sector_pivot['Import']
        sector_pivot['Status'] = sector_pivot['Trade_Balance'].apply(
            lambda x: 'SURPLUS' if x > 0 else 'DEFICIT' if x < 0 else 'BALANCED'
        )
        
        # Format currency columns
        for col in ['Import', 'Export', 'Trade_Balance']:
            if col in sector_pivot.columns:
                sector_pivot[f'{col}_Formatted'] = sector_pivot[col].apply(lambda x: f'${x:,.0f}')
        
        # Sort by trade balance
        sector_pivot = sector_pivot.sort_values('Trade_Balance', ascending=True)
        
        return sector_pivot
    
    return None

# Additional function to show deficit/surplus summary
def create_deficit_surplus_summary(df):
    """Create summary metrics for deficit and surplus sectors"""
    
    sector_trade = df.groupby(['hs_section', 'trade_type'])['value_usd'].sum().reset_index()
    sector_pivot = sector_trade.pivot(index='hs_section', columns='trade_type', values='value_usd').fillna(0)
    
    if 'Import' in sector_pivot.columns and 'Export' in sector_pivot.columns:
        sector_pivot['Trade_Balance'] = sector_pivot['Export'] - sector_pivot['Import']
        
        deficit_sectors = sector_pivot[sector_pivot['Trade_Balance'] < 0]
        surplus_sectors = sector_pivot[sector_pivot['Trade_Balance'] > 0]
        
        summary = {
            'deficit_count': len(deficit_sectors),
            'surplus_count': len(surplus_sectors),
            'total_deficit': deficit_sectors['Trade_Balance'].sum(),
            'total_surplus': surplus_sectors['Trade_Balance'].sum(),
            'worst_deficit_sector': deficit_sectors['Trade_Balance'].idxmin() if not deficit_sectors.empty else 'None',
            'best_surplus_sector': surplus_sectors['Trade_Balance'].idxmax() if not surplus_sectors.empty else 'None'
        }
        
        return summary
    
    return None

def create_trading_partners_chart(df):
    """Create top trading partners visualization"""
    
    
    partner_totals = df.groupby('country')['value_usd'].sum().reset_index()
    partner_totals = partner_totals.sort_values('value_usd', ascending=True).tail(15)
    
    fig = px.bar(
        partner_totals,
        x='value_usd',
        y='country',
        orientation='h',
        title="Top 15 Trading Partners by Total Volume",
        labels={'value_usd': 'Total Trade Volume (USD)', 'country': 'Country'},
        color='value_usd',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(height=600, showlegend=False)
    
    return fig

def create_commodity_analysis(df):
    """Create commodity sector analysis"""
    
    
    commodity_totals = df.groupby('hs_section')['value_usd'].sum().reset_index()
    commodity_totals = commodity_totals.sort_values('value_usd', ascending=False).head(10)
    
    
    fig = px.pie(
        commodity_totals,
        values='value_usd',
        names='hs_section',
        title="Trade Volume Distribution by Commodity Sector"
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=500)
    
    return fig

def create_trade_balance_by_sector(df):
    """Create trade balance analysis by sector"""
    
    
    sector_trade = df.groupby(['hs_section', 'trade_type'])['value_usd'].sum().reset_index()
    sector_pivot = sector_trade.pivot(index='hs_section', columns='trade_type', values='value_usd').fillna(0)
    
    if 'Import' in sector_pivot.columns and 'Export' in sector_pivot.columns:
        sector_pivot['Trade_Balance'] = sector_pivot['Export'] - sector_pivot['Import']
        sector_pivot = sector_pivot.sort_values('Trade_Balance', ascending=True).tail(10)
        
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=sector_pivot.index,
            x=sector_pivot['Trade_Balance'],
            orientation='h',
            marker_color=['green' if x > 0 else 'red' for x in sector_pivot['Trade_Balance']],
            name='Trade Balance'
        ))
        
        fig.update_layout(
            title="Trade Balance by Commodity Sector",
            xaxis_title="Trade Balance (USD)",
            yaxis_title="Commodity Sector",
            height=600
        )
        
        return fig
    
    return None

def create_yearly_trends_analysis(df, selected_countries, selected_commodities):
    """Create detailed yearly trends based on user selection"""
    
    
    filtered_df = df.copy()
    
    if selected_countries and 'All' not in selected_countries:
        filtered_df = filtered_df[filtered_df['country'].isin(selected_countries)]
    
    if selected_commodities and 'All' not in selected_commodities:
        filtered_df = filtered_df[filtered_df['hs_section'].isin(selected_commodities)]
    
    
    yearly_trends = filtered_df.groupby(['year', 'trade_type'])['value_usd'].sum().reset_index()
    
    fig = px.line(
        yearly_trends,
        x='year',
        y='value_usd',
        color='trade_type',
        title=f"Trade Trends: {', '.join(selected_countries[:3]) if selected_countries else 'All Countries'}",
        markers=True
    )
    
    fig.update_layout(height=400)
    
    return fig

def main():
    """Main Streamlit application"""
    
    
    st.markdown('<h1 class="main-header">🇮🇳 India Trade Flow Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("**Comprehensive analysis of India's import-export patterns and trade relationships**")
    
    
    with st.spinner("Loading trade data..."):
        df = load_data_from_db()
        if df is None:
            st.warning("Using sample data for demonstration. Upload your database for real analysis.")
            df = load_sample_data()
    
    
    st.sidebar.header("🔍 Dashboard Filters")
    
    
    year_range = st.sidebar.slider(
        "Select Year Range",
        min_value=int(df['year'].min()),
        max_value=int(df['year'].max()),
        value=(int(df['year'].min()), int(df['year'].max()))
    )
    
    
    trade_types = st.sidebar.multiselect(
        "Trade Type",
        options=['Import', 'Export'],
        default=['Import', 'Export']
    )
    
    
    filtered_df = df[
        (df['year'] >= year_range[0]) & 
        (df['year'] <= year_range[1]) & 
        (df['trade_type'].isin(trade_types))
    ]
    
    
    st.header("📊 Trade Overview")
    create_overview_metrics(filtered_df)
    
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(create_trade_balance_chart(filtered_df), use_container_width=True)
    
    with col2:
        st.plotly_chart(create_commodity_analysis(filtered_df), use_container_width=True)
    
    
    st.header("🌍 Trading Partners Analysis")
    st.plotly_chart(create_trading_partners_chart(filtered_df), use_container_width=True)
    
    
    st.header("⚖️ Trade Balance by Sector")
    balance_chart = create_trade_balance_by_sector(filtered_df)
    if balance_chart:
        st.plotly_chart(balance_chart, use_container_width=True)
    
    
    st.header("🔬 Detailed Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        
        countries = ['All'] + sorted(df['country'].unique().tolist())
        selected_countries = st.multiselect(
            "Select Countries for Trend Analysis",
            options=countries,
            default=['All']
        )
    
    with col2:
        
        commodities = ['All'] + sorted(df['hs_section'].unique().tolist())
        selected_commodities = st.multiselect(
            "Select Commodity Sectors",
            options=commodities,
            default=['All']
        )
    
    
    if selected_countries or selected_commodities:
        trend_chart = create_yearly_trends_analysis(filtered_df, selected_countries, selected_commodities)
        st.plotly_chart(trend_chart, use_container_width=True)
    
    
    st.header("💡 Key Insights")
    
    
    total_imports = filtered_df[filtered_df['trade_type'] == 'Import']['value_usd'].sum()
    total_exports = filtered_df[filtered_df['trade_type'] == 'Export']['value_usd'].sum()
    trade_balance = total_exports - total_imports
    
    top_partner = filtered_df.groupby('country')['value_usd'].sum().idxmax()
    top_commodity = filtered_df.groupby('hs_section')['value_usd'].sum().idxmax()
    
    insights_col1, insights_col2 = st.columns(2)
    
    with insights_col1:
        st.markdown(f"""
        <div class="insight-box">
            <h4>🎯 Trade Performance</h4>
            <p><strong>Trade Balance:</strong> ${trade_balance:,.0f}</p>
            <p><strong>Status:</strong> {'SURPLUS' if trade_balance > 0 else 'DEFICIT'}</p>
            <p><strong>Total Trade Volume:</strong> ${total_imports + total_exports:,.0f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with insights_col2:
        st.markdown(f"""
        <div class="insight-box">
            <h4>🌟 Top Performers</h4>
            <p><strong>Largest Trading Partner:</strong> {top_partner}</p>
            <p><strong>Top Commodity Sector:</strong> {top_commodity}</p>
            <p><strong>Data Coverage:</strong> {len(filtered_df):,} trade records</p>
        </div>
        """, unsafe_allow_html=True)
    
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>📊 <strong>India Trade Flow Dashboard</strong> | Built with Python, Streamlit & Plotly</p>
        <p>🔄 Data updates automatically | 📈 Interactive visualizations | 🌐 Shareable insights</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

