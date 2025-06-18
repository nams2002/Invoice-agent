import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.utils import format_currency

def render_data_viewer(structured_data, aggregated_data):
    """Render the data viewer with visualizations"""
    
    if not structured_data:
        st.info("No data to display. Process some invoices first!")
        return
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📋 Details", "📈 Analytics", "💾 Export"])
    
    with tab1:
        render_overview(aggregated_data)
    
    with tab2:
        render_details(structured_data)
    
    with tab3:
        render_analytics(structured_data, aggregated_data)
    
    with tab4:
        render_export_options(structured_data)

def render_overview(aggregated_data):
    """Render overview metrics"""
    st.markdown("### Invoice Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Invoices",
            aggregated_data.get("total_invoices", 0)
        )
    
    with col2:
        st.metric(
            "Total Amount",
            format_currency(aggregated_data.get("total_amount", 0))
        )
    
    with col3:
        st.metric(
            "Average Amount",
            format_currency(aggregated_data.get("average_amount", 0))
        )
    
    with col4:
        st.metric(
            "Total Tax",
            format_currency(aggregated_data.get("total_tax", 0))
        )
    
    # Vendor distribution
    if aggregated_data.get("vendors"):
        st.markdown("### Vendor Distribution")
        vendor_df = pd.DataFrame(
            list(aggregated_data["vendors"].items()),
            columns=["Vendor", "Count"]
        )
        
        fig = px.pie(vendor_df, values='Count', names='Vendor', title='Invoices by Vendor')
        st.plotly_chart(fig, use_container_width=True)

def render_details(structured_data):
    """Render detailed invoice data"""
    st.markdown("### Invoice Details")
    
    # Convert to DataFrame for display
    display_data = []
    for invoice in structured_data:
        if "error" not in invoice:
            display_data.append({
                "Invoice #": invoice.get("invoice_number", "N/A"),
                "Date": invoice.get("date", "N/A"),
                "Vendor": invoice.get("vendor_name", "N/A"),
                "Customer": invoice.get("customer_name", "N/A"),
                "Total": format_currency(invoice.get("total", 0)),
                "Tax": format_currency(invoice.get("tax", 0)),
                "Source": invoice.get("source_file", "N/A")
            })
    
    if display_data:
        df = pd.DataFrame(display_data)
        st.dataframe(df, use_container_width=True)
        
        # Expandable detailed view
        st.markdown("### Detailed Invoice View")
        for i, invoice in enumerate(structured_data):
            if "error" not in invoice:
                with st.expander(f"Invoice {invoice.get('invoice_number', i+1)}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Invoice Information**")
                        st.write(f"Number: {invoice.get('invoice_number', 'N/A')}")
                        st.write(f"Date: {invoice.get('date', 'N/A')}")
                        st.write(f"Due Date: {invoice.get('due_date', 'N/A')}")
                        st.write(f"Payment Terms: {invoice.get('payment_terms', 'N/A')}")
                    
                    with col2:
                        st.markdown("**Financial Summary**")
                        st.write(f"Subtotal: {format_currency(invoice.get('subtotal', 0))}")
                        st.write(f"Tax: {format_currency(invoice.get('tax', 0))}")
                        st.write(f"Total: {format_currency(invoice.get('total', 0))}")
                    
                    # Items table
                    if invoice.get("items"):
                        st.markdown("**Line Items**")
                        items_df = pd.DataFrame(invoice["items"])
                        st.dataframe(items_df, use_container_width=True)
    else:
        st.warning("No valid invoice data to display")

def render_analytics(structured_data, aggregated_data):
    """Render analytics and visualizations"""
    st.markdown("### Invoice Analytics")
    
    # Time series analysis
    dates_amounts = []
    for invoice in structured_data:
        if "error" not in invoice and invoice.get("date") and invoice.get("total"):
            dates_amounts.append({
                "Date": invoice["date"],
                "Amount": invoice["total"]
            })
    
    if dates_amounts:
        df = pd.DataFrame(dates_amounts)
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        # Line chart
        fig = px.line(df, x='Date', y='Amount', title='Invoice Amounts Over Time')
        st.plotly_chart(fig, use_container_width=True)
        
        # Monthly aggregation
        df['Month'] = df['Date'].dt.to_period('M').astype(str)
        monthly = df.groupby('Month')['Amount'].agg(['sum', 'count', 'mean'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                x=monthly.index,
                y=monthly['sum'],
                title='Monthly Invoice Totals'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                x=monthly.index,
                y=monthly['count'],
                title='Monthly Invoice Count'
            )
            st.plotly_chart(fig, use_container_width=True)

def render_export_options(structured_data):
    """Render export options"""
    st.markdown("### Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Download as JSON"):
            from src.data_extractor import DataExtractor
            extractor = DataExtractor()
            file_path = extractor.save_to_json(structured_data)
            st.success(f"JSON file saved: {file_path}")
            
            # Create download link
            with open(file_path, 'r') as f:
                st.download_button(
                    label="Click to Download JSON",
                    data=f.read(),
                    file_name=os.path.basename(file_path),
                    mime='application/json'
                )
    
    with col2:
        if st.button("📥 Download as CSV"):
            from src.data_extractor import DataExtractor
            extractor = DataExtractor()
            file_path = extractor.save_to_csv(structured_data)
            st.success(f"CSV file saved: {file_path}")
            
            # Create download link
            with open(file_path, 'r') as f:
                st.download_button(
                    label="Click to Download CSV",
                    data=f.read(),
                    file_name=os.path.basename(file_path),
                    mime='text/csv'
                )