import pandas as pd
import streamlit as st

from utils import api_call
from constants import NAME_EVENT_COLUMNS, severity_colour_map
from components.interactions_tab.alternative_search import alternative_search


def interactions_list(selected_drugs, df):
    """ Generate drug-drug interaction cards """
    # Fetch all indications for all drugs at once
    unique_drugs = set()
    for _, row in df.iterrows():
        unique_drugs.add(row['drug_a_concept_name'])
        unique_drugs.add(row['drug_b_concept_name'])
    
    # Single API call to get all indications
    all_indications = api_call("indications", params={"drug_list": list(unique_drugs)})
    drug_indications_map = {drug: indications for drug, indications in all_indications.items()}
    
    # Sort interactins by severity high to low
    df = df.sort_values(by='severity_code', ascending=False)

    for index, row in df.iterrows():
        # Use cached indications instead of making API calls
        drug_a_indications = drug_indications_map.get(row['drug_a_concept_name'], [])
        drug_b_indications = drug_indications_map.get(row['drug_b_concept_name'], [])
        
        # Create DataFrames with only the needed columns
        drug_a_df = pd.DataFrame(drug_a_indications)[NAME_EVENT_COLUMNS] if drug_a_indications else pd.DataFrame(columns=NAME_EVENT_COLUMNS)
        drug_b_df = pd.DataFrame(drug_b_indications)[NAME_EVENT_COLUMNS] if drug_b_indications else pd.DataFrame(columns=NAME_EVENT_COLUMNS)
        # container_style = """
        #     <style>
        #         [data-testid="stHorizontalBlock"] > div:first-child > div [data-testid="stVerticalBlock"] > div:first-child {
        #             background-color: #f8f9fa;
        #             padding-top: 0.25rem;
        #             padding-bottom: 0.25rem;
        #             padding-left: 0.5rem;
        #             padding-right: 0.5rem;
        #             border-radius: 0.5rem;
        #         }
        #     </style>
        # """
        # st.markdown(container_style, unsafe_allow_html=True)

        with st.container(border=False):
            col_interaction, col_alternatives = st.columns([0.5, 0.5])
            with col_interaction:
                with st.container(border=True):
                    col_interaction, col_severity_dot = st.columns([0.8, 0.2])
                    with col_interaction:
                        st.markdown(f"##### {row['drug_a_concept_name']} + {row['drug_b_concept_name']}")
                        st.markdown(f"""
                                    <div style="margin-top: 0px; margin-bottom: 8px;">
                                        <strong>Interaction effect:</strong> {row['event_concept_name']}
                                    </div>
                                    """, unsafe_allow_html=True)
                        st.markdown(f"""
                            <div style="margin-top: 0px; margin-bottom: 8px;">
                                <strong>Description:</strong> <i>{row['description']} (BNF)</i>
                            </div>
                        """, unsafe_allow_html=True)
                    with col_severity_dot:
                        severity_color = severity_colour_map.get(row['severity_code'], "grey")
                        st.markdown(
                            f'<div style="display: flex; align-items: center; justify-content: center; '
                            f'background-color: rgba(0,0,0,0.03); padding: 5px 10px; border-radius: 12px;">'
                            f'<span style="margin-right: 8px; font-weight: 500;">Severity {row["severity_code"]}</span>'
                            f'<div style="width: 12px; height: 12px; border-radius: 50%; background-color: {severity_color};"></div>'
                            f'</div>', 
                            unsafe_allow_html=True
                        )
                    severities = []
                    if row['severity_ansm']:
                        severities.append(f"{row['severity_ansm']} (ANSM)")
                    if row['severity_bnf']:
                        severities.append(f"{row['severity_bnf']} (BNF)")
                    if severities:
                        st.markdown(f"""
                            <div style="margin-top: 0px;">
                                <strong>Severity:</strong> <i>{", ".join(severities)}</i>
                            </div>
                        """, unsafe_allow_html=True)

                    button_key = f"details_{row['drug_a_concept_name']}_{row['drug_b_concept_name']}_{index}"
                    show_details = st.checkbox(
                        "Search for alternative drugs",
                        key=button_key,
                        help="Click to show/hide the alternative drug search interface"
                    )
                    # st.markdown('</div>', unsafe_allow_html=True)
                if show_details:
                    with col_alternatives:
                        with st.container(border=False, height=0):
                            st.markdown('<div style="position: absolute; left: -22px; top: 0px; font-size: 28px; color: #666; transform: scaleX(0.6);"> \
                                        ▶ \
                                    </div></div>', unsafe_allow_html=True)
                        with st.container(border=True, ):
                            st.write("#### Search for Alternative Drugs")
                            alternative_search(selected_drugs, drug_a_df, row['drug_a_concept_name'], index)
                            st.divider()
                            alternative_search(selected_drugs, drug_b_df, row['drug_b_concept_name'], index)

# ▶