# pages/home.py
import streamlit as st
import pandas as pd

def show():
    st.title("Wealth Planning Form")

    # Define the asset types and their groups
    asset_types = [
        "Non-Qualified / Taxable Investment",
        "Qualified, IRA or other",
        "Non-Qualified Deferred Comp, SERP, or other",
        "Roth IRA, Roth 401k, Roth Annuity",
        "Life Insurance",
        "Annuity",
        "Private Business",
        "Stock Options",
        "Artwork / Collectibles",
        "Digital Assets",
        "Charitable"
    ]

    # Define the dimensions and their options
    dimensions = {
        "D1": {"label": "Taxation on Funding", "options": ["Pre-Tax", "Partially Pre-Tax", "After-Tax"]},
        "D2": {"label": "Taxation on Growth", "options": ["Taxable/Ordinary Income", "Taxable/Capital Gain", "Tax-Deferred", "Tax-Free"]},
        "D3": {"label": "Taxation on Distribution", "options": ["Taxable/Ordinary Income", "Taxable/Capital Gain", "Not taxable"]},
        "D4": {"label": "Taxation on Death", "options": ["Yes", "No"]},
        "D5": {"label": "Asset Protection", "options": ["Yes", "No", "Partially"]},
        "D6": {"label": "Charitable Deduction", "options": ["Yes", "No"]}
    }

    # Define the rows of the table
    rows = [
        "a. Marketable Securities",
        "b. Private Equity",
        "c. Real Estate",
        "d. Hedge Fund",
        "e. Credit",
        "a. Marketable Securities",
        "b. Life Insurance inside a Qualified Plan",
        "c. Annuity inside a Qualified Plan",
        "Non-Qualified Deferred Comp, SERP, or other",
        "Roth IRA, Roth 401k, Roth Annuity",
        "a. Split-Dollar Life Insurance",
        "Annuity",
        "Private Business",
        "Stock Options",
        "Artwork / Collectibles",
        "Digital Assets",
        "Charitable"
    ]

    # Create a DataFrame for the table
    df = pd.DataFrame({
        "Asset Type": rows,
        "Before Planning": [""] * len(rows),
        "After Planning": [""] * len(rows),
        "D1": [""] * len(rows),
        "% D1 (if partially pre-tax)": [""] * len(rows),
        "D2": [""] * len(rows),
        "D3": [""] * len(rows),
        "D4": [""] * len(rows),
        "D5": [""] * len(rows),
        "% D5 (if partially pre-tax)": [""] * len(rows),
        "D6": [""] * len(rows),
    })

    # Create the form for user input
    with st.form(key='wealth_planning_form'):
        st.write("## Fill Out the Form")
        st.write("Fill out the details for each asset type.")

        # Create the table with form fields
        form_data = []
        for index, row in df.iterrows():
            st.write(f"### Asset Type: {row['Asset Type']}")
            before_planning = st.text_input(f"Before Planning ({row['Asset Type']})", key=f"before_{index}")
            after_planning = st.text_input(f"After Planning ({row['Asset Type']})", key=f"after_{index}")
            d1 = st.selectbox(f"D1: {dimensions['D1']['label']} ({row['Asset Type']})", dimensions['D1']['options'], key=f"d1_{index}")
            d1_pct = st.text_input(f"% D1 (if partially pre-tax) ({row['Asset Type']})", key=f"d1_pct_{index}")
            d2 = st.selectbox(f"D2: {dimensions['D2']['label']} ({row['Asset Type']})", dimensions['D2']['options'], key=f"d2_{index}")
            d3 = st.selectbox(f"D3: {dimensions['D3']['label']} ({row['Asset Type']})", dimensions['D3']['options'], key=f"d3_{index}")
            d4 = st.selectbox(f"D4: {dimensions['D4']['label']} ({row['Asset Type']})", dimensions['D4']['options'], key=f"d4_{index}")
            d5 = st.selectbox(f"D5: {dimensions['D5']['label']} ({row['Asset Type']})", dimensions['D5']['options'], key=f"d5_{index}")
            d5_pct = st.text_input(f"% D5 (if partially pre-tax) ({row['Asset Type']})", key=f"d5_pct_{index}")
            d6 = st.selectbox(f"D6: {dimensions['D6']['label']} ({row['Asset Type']})", dimensions['D6']['options'], key=f"d6_{index}")
            
            form_data.append({
                "Asset Type": row['Asset Type'],
                "Before Planning": before_planning,
                "After Planning": after_planning,
                "D1": d1,
                "% D1 (if partially pre-tax)": d1_pct,
                "D2": d2,
                "D3": d3,
                "D4": d4,
                "D5": d5,
                "% D5 (if partially pre-tax)": d5_pct,
                "D6": d6
            })

        # Submit button
        submit_button = st.form_submit_button(label='Submit')

        if submit_button:
            # Convert the collected form data into a DataFrame and display it
            form_df = pd.DataFrame(form_data)
            st.write("## Submitted Data")
            st.write(form_df)

            # Optionally, you can add code here to save the data to a file or a database
            # For example: form_df.to_csv('submitted_data.csv', index=False)
