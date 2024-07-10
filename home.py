import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns
import streamlit.components.v1 as components
import llm_agent
import asyncio
import json

# # Disable default sidebar navigation
# st.set_option('client.showSidebarNavigation', False)
# # Set page config
# st.set_page_config(page_title="4D Wealth Model", page_icon=":star:", layout="wide", initial_sidebar_state="collapsed")



# Define the dimensions and their options with weights
dimensions = {
    "D1": {"label": "Taxation on Funding", "options": ["Pre-Tax", "Partially Pre-Tax", "After-Tax"], "weight": 0.20},
    "D2": {"label": "Taxation on Growth", "options": ["Taxable/Ordinary Income", "Taxable/Capital Gain", "Tax-Deferred", "Tax-Free"], "weight": 0.20},
    "D3": {"label": "Taxation on Distribution", "options": ["Taxable/Ordinary Income", "Taxable/Capital Gain", "Not taxable"], "weight": 0.20},
    "D4": {"label": "Taxation on Death", "options": ["Yes", "No"], "weight": 0.20},
    "D5": {"label": "Asset Protection", "options": ["Yes", "No", "Partially"], "weight": 0.10},
    "D6": {"label": "Charitable Deduction", "options": ["Yes", "No"], "weight": 0.10}
}

# Define scores for options in each dimension
option_scores = {
    "D1": {"Pre-Tax": 3, "Partially Pre-Tax": 2, "After-Tax": 1},
    "D2": {"Taxable/Capital Gain": 1, "Taxable/Ordinary Income": 2, "Tax-Deferred": 3, "Tax-Free": 4},
    "D3": {"Taxable/Ordinary Income": 1, "Taxable/Capital Gain": 2, "Not taxable": 3},
    "D4": {"Yes": 1, "No": 2},
    "D5": {"Yes": 3, "Partially": 2, "No": 1},
    "D6": {"Yes": 2, "No": 1}
    }

def calculate_wealth_score(form_data):
    global dimensions
    global option_scores
    # Compute total income before and after planning
    total_income_before_planning = form_data["Before Planning"].replace('', 0).astype(float).sum()
    total_income_after_planning = form_data["After Planning"].replace('', 0).astype(float).sum()

    results = {}

    # Initialize accumulators for overall scores
    overall_total_before_score = 0
    overall_total_after_score = 0

    for dimension, props in dimensions.items():
        dimension_label = props["label"]
        options = props["options"]
        weight = props["weight"]

        # Initialize results for this dimension
        results[dimension] = {
            "Dimension Label": dimension_label,
            "Options": {}
        }

        total_before_score = 0
        total_after_score = 0

        for option in options:
            before_sum = form_data[form_data[f"{dimension}: {dimension_label}"] == option]["Before Planning"].replace('', 0).astype(float).sum()
            after_sum = form_data[form_data[f"{dimension}: {dimension_label}"] == option]["After Planning"].replace('', 0).astype(float).sum()

            # Get the score for this option
            option_score = option_scores[dimension].get(option, 0)

            # Calculate the percentage for the option in the dimension
            before_percentage = before_sum / total_income_before_planning if total_income_before_planning != 0 else 0
            after_percentage = after_sum / total_income_after_planning if total_income_after_planning != 0 else 0

            # Calculate scores before and after planning
            # Note: Special case for D6 where Before Planning Score is set to zero for all options
            if dimension == "D6":
                score_before_planning = 0
            else:
                score_before_planning = (weight * 100 * option_score / len(options)) * before_percentage

            score_after_planning = (weight * 100 * option_score / len(options)) * after_percentage

            # Accumulate scores for the dimension
            total_before_score += score_before_planning
            total_after_score += score_after_planning

            # Populate the nested dictionary for each option
            results[dimension]["Options"][option] = {
                "Before Planning": float(before_sum),
                "After Planning": float(after_sum),
                "Before Planning %": float(round(before_percentage, 4)),  # Format as percentage
                "After Planning %": float(round(after_percentage, 4)),   # Format as percentage
                "Before Planning Score": float(round(score_before_planning, 2)),
                "After Planning Score": float(round(score_after_planning, 2))
            }

        # Add the total scores for the dimension
        results[dimension]["Total Before Planning Score"] = float(round(total_before_score, 2))
        results[dimension]["Total After Planning Score"] = float(round(total_after_score, 2))

        # Calculate the weighted average score for the dimension
        overall_total_before_score += total_before_score
        overall_total_after_score += total_after_score

    # Add the overall scores to the results dictionary
    results["Overall"] = {
        "Overall Before Planning Score": float(round(overall_total_before_score, 2)),
        "Overall After Planning Score": float(round(overall_total_after_score, 2))
    }

    return results




# Data for the gauge charts
performance_data = {
    "Poor": 20,
    "Average": 30,
    "Good": 50
}

def create_gauge_chart(score, title):
    # Create a gauge chart
    fig = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=score,
    title={"text": title},
    gauge={
        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "black"},
        'bar': {'color': 'blue'},
        'bgcolor': 'lightgray',
        'steps': [
            {'range': [0, performance_data['Poor']], 'color': 'red'},
            {'range': [performance_data['Poor'], performance_data['Poor'] + performance_data['Average']], 'color': 'yellow'},
            {'range': [performance_data['Poor'] + performance_data['Average'], 100], 'color': 'green'}
        ],
        'threshold': {
            'line': {'color': 'red', 'width': 4},
            'thickness': 0.75,
            'value': 50
        }
    },
))
    return fig

# Define function to get color mapping based on option scores
def get_color_map(option_scores):
    sorted_options = sorted(option_scores.items(), key=lambda x: x[1], reverse=True)  # Sort descending by score
    color_map = {}
    for option, score in sorted_options:
        if score == sorted_options[0][1]:
            color_map[option] = 'green'
        elif score == sorted_options[-1][1]:
            color_map[option] = 'red'
        else:
            color_map[option] = 'orange'
    return color_map

# Define function to create a stacked bar chart
def create_stacked_bar_chart(dimension_data, dimension_label, option_scores):
    options = dimension_data['Options']
    color_map = get_color_map(option_scores)

    # Prepare data for before and after planning
    before_contributions = {}
    after_contributions = {}

    for option, values in options.items():
        before_percentage = values['Before Planning %']
        after_percentage = values['After Planning %']

        before_contributions[option] = before_percentage
        after_contributions[option] = after_percentage

    fig = go.Figure()

    # Add bars for Before Planning
    for option, color in color_map.items():
        if option in before_contributions:
            fig.add_trace(go.Bar(
                x=['Before Planning'],
                y=[before_contributions.get(option, 0)],
                name=f'{option} Before Planning',  # Unique name for the trace
                marker_color=color,
                text=[f'{before_contributions.get(option, 0)*100:.1f}%'],
                textposition='inside',
                width=0.35,  # Adjust the bar width here
                legendgroup=option,
                showlegend=True  # Ensure legend is shown
            ))

    # Add bars for After Planning
    for option, color in color_map.items():
        if option in after_contributions:
            fig.add_trace(go.Bar(
                x=['After Planning'],
                y=[after_contributions.get(option, 0)],
                name=f'{option} After Planning',  # Unique name for the trace
                marker_color=color,
                text=[f'{after_contributions.get(option, 0)*100:.1f}%'],
                textposition='inside',
                width=0.35,  # Adjust the bar width here
                legendgroup=option,
                showlegend=True  # Ensure legend is shown
            ))

    fig.update_layout(
        barmode='stack',
        title=dimension_label,
        xaxis_title='Planning Stage',
        yaxis_title='Percentage Contribution',
        xaxis=dict(
            tickvals=['Before Planning', 'After Planning'],
            ticktext=['Before Planning', 'After Planning'],
            title='Planning Stage',
        ),
        yaxis=dict(
            title='Percentage (%)',
            range=[0, 1],
            tickformat='%'
        ),
        legend_title='Options',
        legend=dict(
            title='Options',
            x=1, 
            y=1,
            tracegroupgap=0,  # Group traces to avoid duplicate legend entries
        ),
        margin=dict(l=0, r=250, t=50, b=0),  # Adjust margins to fit the legend
    )

    return fig

# Define function to create a pie chart
def create_pie_chart(data, option_scores, title):
    color_map = get_color_map(option_scores)
    labels = list(data.keys())
    values = list(data.values())
    
    # Sort labels by score in descending order to place green at the top and red at the bottom
    sorted_labels = sorted(labels, key=lambda x: option_scores[x], reverse=True)
    sorted_values = [data[label] for label in sorted_labels]
    sorted_colors = [color_map[label] for label in sorted_labels]

    # Create the pie chart
    fig = go.Figure(data=[go.Pie(
        labels=sorted_labels,
        values=sorted_values,
        hole=0.3,
        marker=dict(colors=sorted_colors),
        textinfo='label+percent',
        pull=[0.1] * len(sorted_labels),  # Add space between slices
        sort=False  # Disable the default sorting of the pie chart slices
    )])
    
    # Update layout for the pie chart
    fig.update_layout(
        title=title,
        legend=dict(
            title='Options',
            x=1, 
            y=1,
            traceorder='normal',  # Normal order for legend to show green at the top and red at the bottom
            orientation='v'  # Ensure vertical layout for legend
        ),
        margin=dict(l=0, r=250, t=150, b=0)  # Adjust margins to fit the legend
    )
    
    return fig


def display_wealth_score_results(results, df):
    global dimensions
    global option_scores

    # Extract overall scores
    overall_before_planning_score = results.get("Overall", {}).get("Overall Before Planning Score")
    overall_after_planning_score = results.get("Overall", {}).get("Overall After Planning Score")

    # Streamlit layout
    st.title("Wealth Score Analysis")

    # Check if the scores are available before creating charts
    if overall_before_planning_score is not None and overall_after_planning_score is not None:
        # Create two columns for the gauge charts
        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f"""Total Wealth Before Planning: ${df['Before Planning'].sum():,.2f}""")
            st.subheader("Before Planning 4D Wealth Score")
            gauge_chart_before = create_gauge_chart(overall_before_planning_score, "Overall Score Before Planning")
            st.plotly_chart(gauge_chart_before)

        with col2:
            st.subheader(f"""Total Wealth After Planning: ${df['After Planning'].sum():,.2f}""")
            st.subheader("After Planning 4D Wealth Score")
            gauge_chart_after = create_gauge_chart(overall_after_planning_score, "Overall Score After Planning")
            st.plotly_chart(gauge_chart_after)

    else:
        st.write("Overall scores are not available for display.")

    
    

    st.header("Distribution of Wealth")

    tab1, tab2, tab3, tab4 = st.tabs(["Dimension Analysis", "Redistribution Analysis", "Asset Type Analysis", "Agentic Recommendations"])

    with tab1:
        # Create pie charts for each dimension
        st.header("Distribution of Wealth Percentage Across Dimensions")
        for dimension_key, dimension_data in results.items():
            if dimension_key.startswith('D'):
                before_distribution = {option: values['Before Planning'] for option, values in dimension_data['Options'].items()}
                after_distribution = {option: values['After Planning'] for option, values in dimension_data['Options'].items()}
                
                st.subheader(f"Dimension Distribution - {dimension_data['Dimension Label']}")
                col1, col2 = st.columns(2)
                with col1:
                    st.write("Before Planning")
                    pie_chart_before = create_pie_chart(before_distribution, option_scores[dimension_key], f"{dimension_data['Dimension Label']} - Before Planning")
                    st.plotly_chart(pie_chart_before)
                with col2:
                    st.write("After Planning")
                    pie_chart_after = create_pie_chart(after_distribution, option_scores[dimension_key], f"{dimension_data['Dimension Label']} - After Planning")
                    st.plotly_chart(pie_chart_after)
    with tab2:
        # Display stacked bar charts for each dimension
        st.header("Impact of Redistribution of Wealth")
        for dimension_key, dimension_data in results.items():
            if dimension_key.startswith('D'):
                dimension_label = dimension_data['Dimension Label']
                option_scores_for_dimension = option_scores[dimension_key]
                chart = create_stacked_bar_chart(dimension_data, dimension_label, option_scores_for_dimension)
                st.plotly_chart(chart)


    
    with tab3:
        st.header("Asset Type Analysis")

        # Filter dataframes
        df_qualified = df[df['Asset Type'].str.contains("Qualified") & ~df['Asset Type'].str.contains("Non-Qualified")]
        df_non_qualified = df[df['Asset Type'].str.contains("Non-Qualified")]
        df_others = df[~df['Asset Type'].str.contains("Qualified|Non-Qualified")]

        # Plot for Qualified
        fig_qualified = px.bar(df_qualified, x='Asset Type', y=['Before Planning', 'After Planning'],
                            title="Qualified Asset Types",
                            labels={'value': 'Dollar Amount', 'variable': 'Planning Stage'},
                            barmode='group')
        fig_qualified.update_layout(xaxis_title="Asset Type", yaxis_title="Dollar Amount")
        st.plotly_chart(fig_qualified)

        # Plot for Non-Qualified
        fig_non_qualified = px.bar(df_non_qualified, x='Asset Type', y=['Before Planning', 'After Planning'],
                                title="Non-Qualified Asset Types",
                                labels={'value': 'Dollar Amount', 'variable': 'Planning Stage'},
                                barmode='group')
        fig_non_qualified.update_layout(xaxis_title="Asset Type", yaxis_title="Dollar Amount")
        st.plotly_chart(fig_non_qualified)

        # Plot for Others
        fig_others = px.bar(df_others, x='Asset Type', y=['Before Planning', 'After Planning'],
                        title="Other Asset Types",
                        labels={'value': 'Dollar Amount', 'variable': 'Planning Stage'},
                        barmode='group')
        fig_others.update_layout(xaxis_title="Asset Type", yaxis_title="Dollar Amount")
        st.plotly_chart(fig_others)

    with tab4:
        st.session_state.tab4_activated = True
        st.header("Agentic Recommendations")
        user_query = create_user_query(results, df)
        asyncio.run(llm_response(user_query))


def convert_json_to_string(json_data):
    """
    Convert JSON data to a pretty-formatted string.

    Args:
    - json_data (dict or list): The JSON data to convert.

    Returns:
    - str: A pretty-formatted string of the JSON data.
    """
    return json.dumps(json_data, indent=4, sort_keys=True)


def create_user_query(results, df):
    global dimensions
    global option_scores
    # Convert to JSON
    df_json_string = convert_json_to_string(json.loads(df.to_json(orient='records')))
    results_string = convert_json_to_string(results)
    dimensions_string = convert_json_to_string(dimensions)
    option_scores_string = convert_json_to_string(option_scores)

    user_query = f"""
You are an Asset Wealth Manager with strong financial expertise. I need your help in devising three strategies to improve my wealth score. In the ###Data### provided below, all columns remain fixed except for the "After Planning" column. Your task is to devise a reallocation of money in different asset types so that the wealth score is maximized. Use the ###Dimensions_Weight### and ###Options_Score### sections to understand how the wealth score is calculated.

The current results are available in the ###Results### section. Please use the following notes to devise a proper response.

###Data###
{df_json_string}

###Dimensions_Weight###
{dimensions_string}

###Options_Score###
{option_scores_string}

###Results###
{results_string}

Notes:
- Write three strategies without providing numbers for reallocating wealth in different asset types that are better for increasing our wealth score.
- Remember that we do not require number but strategic guidance on how to reallocate wealth given Asset Types with dimensions.
- Remember, everything else in the data will remain fixed. Only the "After Planning" column can be changed.
- Specify both the asset types from which we should reduce wealth and the asset types where we should invest.
"""
    return user_query
    

async def llm_response(user_query):
        page_placeholders = {}
        page_placeholders['llm_response'] = st.empty()


        run_status_element = st.empty()

        with st.spinner(f'Querying Agent for response...'):
            page_placeholders['llm_response'] = components.html(llm_agent.awaiting_response_html, height=300)

        loop = asyncio.get_event_loop()

        result = await loop.create_task(llm_agent.call_llm_agent(user_query = user_query, chat_response_container = page_placeholders['llm_response'],  run_status_element = run_status_element))

        if not result:
            NULL_REPONSE = {
                'agent_response': 'The Agent is not live right now - team will be notified to address this issue.',
                'doc_id': None,
            }
            llm_agent.render_text_area(page_placeholders['llm_response'], 'llm_response', NULL_REPONSE['agent_response'])

        else:
            run_status_element.empty()
            llm_agent.render_text_area(page_placeholders['llm_response'], 'llm_response', result['agent_response'])


# Main function to control app flow
def show():
    # Display the header
    st.title("Welcome to the 4D Wealth Planning - Magnus Financial Group")

    # Display the introductory text
    st.markdown("""
    **Unlock a New Dimension of Wealth Management with Magnus Financial Group**

    At Magnus Financial Group, we understand that achieving long-term financial success requires a comprehensive approach. Our new product, **4D Wealth**, is designed to provide you with a clear, multidimensional view of your assets and their financial implications.

    ### What is 4D Wealth?

    **4D Wealth** stands for **4 Dimensional Wealth Planning**, where we delve into the following key aspects of your financial strategy:

    1. **Funding Your Asset:** Understanding whether your contributions are pre-tax, partially pre-tax, or after-tax.
    2. **Growth of Your Asset:** Exploring how your asset grows and whether it’s taxed as it appreciates.
    3. **Taxation on Distribution:** Analyzing how your asset is taxed when distributed, whether as ordinary income, capital gain, or not taxed.
    4. **Estate and Inheritance Taxes:** Assessing if your asset is part of your taxable estate and the implications for inheritance.

    ### Why Choose Magnus Financial Group?

    For over fifteen years, Magnus Financial Group has been dedicated to offering personalized wealth management services. Our approach integrates modern technology with a client-focused service model, ensuring transparency, real-time access, and long-term financial security. We work closely with you to develop and execute a tailored financial plan that evolves with your needs.

    ### Our Process:

    1. **Personalized Consultation:** We start by understanding your unique financial situation and goals.
    2. **Strategic Planning:** Our Investment Team crafts a customized financial plan and implementation strategy.
    3. **Execution and Review:** We execute the plan and provide ongoing support with regular reviews and adjustments.

    Our team of experts ensures that your investment decisions align with your personal goals and risk tolerance, optimizing outcomes and minimizing tax consequences through disciplined strategies.
    """)

    # Define the dimensions and their options
    dimensions = {
        "D1": {"label": "Taxation on Funding", "options": ["Pre-Tax", "Partially Pre-Tax", "After-Tax"]},
        "D2": {"label": "Taxation on Growth", "options": ["Taxable/Ordinary Income", "Taxable/Capital Gain", "Tax-Deferred", "Tax-Free"]},
        "D3": {"label": "Taxation on Distribution", "options": ["Taxable/Ordinary Income", "Taxable/Capital Gain", "Not taxable"]},
        "D4": {"label": "Taxation on Death", "options": ["Yes", "No"]},
        "D5": {"label": "Asset Protection", "options": ["Yes", "No", "Partially"]},
        "D6": {"label": "Charitable Deduction", "options": ["Yes", "No"]}
    }

    # # Define the rows of the table
    # rows = [
    #     "Marketable Securities (Non-Qualified)",
    #     "Private Equity (Non-Qualified)",
    #     "Real Estate (Non-Qualified)",
    #     "Hedge Fund (Non-Qualified)",
    #     "Credit (Non-Qualified)",
    #     "Marketable Securities (Qualified)",
    #     "Life Insurance (Qualified)",
    #     "Annuity (Qualified)",
    #     "Deferred Comp, SERP, or other (Non-Qualified)",
    #     "Roth IRA, Roth 401k, Roth Annuity",
    #     "Life Insurance",
    #     "Split-Dollar Life Insurance",
    #     "Annuity",
    #     "Private Business",
    #     "Stock Options",
    #     "Artwork / Collectibles",
    #     "Digital Assets",
    #     "Charitable"
    # ]

    # # Initialize session state for storing form data
    # if 'form_data' not in st.session_state:
    #     st.session_state['form_data'] = pd.DataFrame({
    #         "Asset Type": rows,
    #         "Before Planning": [""] * len(rows),
    #         "After Planning": [""] * len(rows),
    #         "D1: Taxation on Funding": [""] * len(rows),
    #         "% D1 (if partially pre-tax)": [""] * len(rows),
    #         "D2: Taxation on Growth": [""] * len(rows),
    #         "D3: Taxation on Distribution": [""] * len(rows),
    #         "D4: Taxation on Death": [""] * len(rows),
    #         "D5: Asset Protection": [""] * len(rows),
    #         "% D5 (if partially pre-tax)": [""] * len(rows),
    #         "D6: Charitable Deduction": [""] * len(rows),
    #     })
    # Define the rows of the table with default values
    data = {
        "Asset Type": [
            "Marketable Securities (Non-Qualified)",
            "Private Equity (Non-Qualified)",
            "Real Estate (Non-Qualified)",
            "Hedge Fund (Non-Qualified)",
            "Credit (Non-Qualified)",
            "Marketable Securities (Qualified)",
            "Life Insurance (Qualified)",
            "Annuity (Qualified)",
            "Deferred Comp, SERP, or other (Non-Qualified)",
            "Roth IRA, Roth 401k, Roth Annuity",
            "Life Insurance",
            "Split-Dollar Life Insurance",
            "Annuity",
            "Private Business",
            "Stock Options",
            "Artwork / Collectibles",
            "Digital Assets",
            "Charitable"
        ],
        "Before Planning": [
            500000.00, 50000.00, 860000.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0, 0.00, 0, 0, 0.00, 0.00, 0.00, 0.00, 0.00
        ],
        "After Planning": [
            0.00, 50000.00, 400000.00, 0.00, 0.00, 100000.00, 30000.00, 0.00, 0.00, 400000.00, 0.00, 100000.00, 100000.00, 0.00, 0.00, 0.00, 0.00, 230000.00
        ],
        "D1: Taxation on Funding": [
            "Pre-Tax", "After-Tax", "After-Tax", "After-Tax", "After-Tax", "Pre-Tax", "Pre-Tax", "Pre-Tax", "Pre-Tax", "After-Tax", "After-Tax", "After-Tax", "After-Tax", "After-Tax", "After-Tax", "After-Tax", "After-Tax", "Pre-Tax"
        ],
        "% D1 (if partially pre-tax)": [
            "0%", "0%", "0%", "0%", "0%", "0%", "0%", "0%", "0%", "50%", "0%", "0%", "0%", "0%", "0%", "0%", "0%", "0%"
        ],
        "D2: Taxation on Growth": [
            "Taxable/Capital Gain", "Taxable/Ordinary Income", "Taxable/Capital Gain", "Taxable/Ordinary Income", "Taxable/Ordinary Income", "Tax-Deferred", "Tax-Deferred", "Tax-Deferred", "Tax-Deferred", "Tax-Free", "Tax-Deferred", "Tax-Deferred", "Tax-Deferred", "Taxable/Ordinary Income", "Tax-Deferred", "Tax-Deferred", "Taxable/Ordinary Income", "Tax-Free"

            ],
        "D3: Taxation on Distribution": [
            "Taxable/Capital Gain", "Taxable/Capital Gain", "Taxable/Capital Gain", "Taxable/Capital Gain", "Taxable/Capital Gain", "Taxable/Capital Gain", "Not taxable", "Taxable/Capital Gain", "Taxable/Ordinary Income", "Not taxable", "Not taxable", "Not taxable", "Taxable/Capital Gain", "Taxable/Capital Gain", "Taxable/Capital Gain", "Taxable/Capital Gain", "Taxable/Capital Gain", "Not taxable"
        ],
        "D4: Taxation on Death": [
            "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes", "Yes"
        ],
        "D5: Asset Protection": [
            "No", "No", "No", "No", "No", "Yes", "Yes", "Yes", "No", "Partially", "Yes", "Yes", "Partially", "No", "No", "No", "No", "Yes"
        ],
        "% D5 (if partially pre-tax)": [
            "0%", "0%", "0%", "0%", "0%", "0%", "0%", "0%", "0%", "50%", "0%", "0%", "0%", "0%", "0%", "0%", "0%", "0%"
        ],
        "D6: Charitable Deduction": [
            "No", "No", "No", "No", "No", "No", "No", "No", "No", "No", "No", "No", "No", "No", "No", "No", "No", "Yes"
        ]
    }

    # Initialize session state for storing form data
    if 'form_data' not in st.session_state:
        st.session_state['form_data'] = pd.DataFrame(data)

    # Define the GridOptionsBuilder object
    gb = GridOptionsBuilder.from_dataframe(st.session_state['form_data'])
    
    # Define dropdown lists for each dimension
    for dimension, props in dimensions.items():
        gb.configure_column(f"{dimension}: {props['label']}", 
                            editable=True, 
                            cellEditor='agSelectCellEditor', 
                            cellEditorParams={'values': props['options']},
                            width=200,
                            wrapText = True,
                            autoHeight = True)  # Set the width of each dimension column

    # Make the columns for asset type and before/after planning editable but not dropdowns
    gb.configure_column("Asset Type", editable=False, width=350, wrapText = True, autoHeight = True, pinned='left')  # Read-only
    gb.configure_column("Before Planning", editable=True, width=150, pinned='left')
    gb.configure_column("After Planning", editable=True, width=150, pinned='left')
    gb.configure_column("% D1 (if partially pre-tax)", editable=True, width=180)  # Editable percentage input
    gb.configure_column("% D5 (if partially pre-tax)", editable=True, width=180)  # Editable percentage input

    # Add custom CSS for header text wrapping
    custom_css = """
    <style>
    .header-wrap {
        white-space: normal !important;
        word-break: break-word;
        height: auto !important;
        padding: 10px !important;
        text-align: center;
        font-weight: bold;
    }
    .ag-header-cell-label {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

    # Display instructions for using the form
    st.markdown("""
    ### Instructions for Using the 4D Wealth Planning Form

    This form is designed to help you evaluate different assets based on four key dimensions of wealth management. Follow these steps to complete the form:

    1. **Fill in the 'Before Planning' and 'After Planning' Columns:** Enter the values for your assets before and after planning. This information will help us analyze the impact of different strategies on your wealth.

    2. **Select Options for Each Dimension:**
    - **Taxation on Funding (D1):** Choose how your contributions are taxed—Pre-Tax, Partially Pre-Tax, or After-Tax.
    - **Taxation on Growth (D2):** Specify if the growth of your asset is Taxable/Ordinary Income, Taxable/Capital Gain, Tax-Deferred, or Tax-Free.
    - **Taxation on Distribution (D3):** Indicate if the asset is taxed as Taxable/Ordinary Income, Taxable/Capital Gain, or Not Taxable upon distribution.
    - **Taxation on Death (D4):** Select Yes or No to indicate if the asset is included in the taxable estate upon death.
    - **Asset Protection (D5):** Choose whether the asset offers Protection—Yes, No, or Partially.
    - **Charitable Deduction (D6):** Indicate if there is a Charitable Deduction available for the asset—Yes or No.

    3. **Enter Percentages for Partial Pre-Tax Contributions and Asset Protection:** If you select “Partially Pre-Tax” for D1 or “Partially” for D5, enter the applicable percentage. Otherwise, leave it as 0%.

    4. **Submit the Form:** After completing the form, click the “Submit” button to calculate the wealth score based on your inputs.

    If you have any questions or need help with any section, please reach out to your financial advisor.

    Thank you for using the 4D Wealth Planning Form!
                
    ### 4D Wealth Planning Form:
    """)
    # Build the grid options
    grid_options = gb.build()
    
    # Add a cell value changed event
    def on_cell_value_changed(event):
        st.session_state['form_data'] = pd.DataFrame(event['data'])
        st.rerun()

    # Display the editable grid
    grid_response = AgGrid(
        st.session_state['form_data'],
        gridOptions=grid_options,
        editable=True,
        key='grid1'

    )
    st.session_state['form_data'] = grid_response['data']
    # Handle form submission
    if st.button("Submit"):
        df = pd.DataFrame(st.session_state['form_data'])
        # with pd.ExcelWriter("wealth_planning_form.xlsx", engine='openpyxl') as writer:
        #     df.to_excel(writer, index=False)
        # st.success("Form submitted successfully! Data saved to `wealth_planning_form.xlsx`.")
        # Calculate the wealth score
        results = calculate_wealth_score(df)
        display_wealth_score_results(results, df)

      