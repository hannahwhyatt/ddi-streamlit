import requests
import streamlit as st
import pandas as pd

def api_call(endpoint, type="get", params=None, show_error=True):
    # Use POST method for the interactions endpoint
    if type == "post":
        response = requests.post(f"https://ddi-fast-api.onrender.com/{endpoint}", json=params)
    else:
        response = requests.get(f"https://ddi-fast-api.onrender.com/{endpoint}", params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        if show_error:
            st.error(f"Failed to fetch {endpoint}.")
        return None
    
def join_interactions_and_side_effects(interactions_df, side_effects_df):
    # Extract interaction side effects and add required columns
    interactions_side_effects = pd.DataFrame({
        'drug_concept_name': interactions_df.apply(
            lambda x: f"{x['drug_a_concept_name']} + {x['drug_b_concept_name']}", 
            axis=1
        ),
        'event_concept_name': interactions_df['event_concept_name'],
        'frequency': 'Not reported (Interaction Effect)',  # We do not have frequency data here
        'source': 'interaction',  # This is BNF or Theasurus, not currently displayed.
        'severity_code': interactions_df['severity_code']
    })
    
    # Concatenate with side effects, ensuring same columns
    return pd.concat([interactions_side_effects, side_effects_df], ignore_index=True)

