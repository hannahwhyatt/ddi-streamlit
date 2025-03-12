import streamlit as st
import pandas as pd

from utils import api_call


# Data --------------------------------------------------------------------------
# Fetch the set of drug names for the search box
drug_names = api_call("drug_names")
barkla_drug_names = api_call("barkla_drug_names")
barkla_side_effects_names = api_call("barkla_side_effects_names")
faers_drug_names = api_call("faers_drug_names")

all_drug_names = set(barkla_drug_names) | set(drug_names)
available_drug_names =  set(barkla_drug_names)
unavailable_drug_names = set(drug_names) - set(barkla_drug_names)

# Layout ------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="Culprit Drugs")

# VEC LOGO
col01, col02 = st.columns([8, 1])
with col02:
    st.image("streamlit/assets/branding.png", width=250)

#  =================================================================================
#  =================================================================================
#  =================================================================================
# Section title
st.header("Identify Problematic Drugs by Side Effect")
st.write("""List the selected drug portfolio in order of highest to lowest "combined" rate of the selected side effect.""")

# Drug Selection ---------------------------------------------------------------
if barkla_drug_names and drug_names:
    selected_drugs_A = st.multiselect(
        "Select Drug Portfolio",
        options=available_drug_names,
        help=f"Search and select from {len(available_drug_names)} drugs",
        key="selected_drugs_A"
    )
else:
    st.error("Failed to fetch data.")
col11, col12 = st.columns([0.5, 0.5])
with col11:
    if barkla_side_effects_names:
        selected_side_effect = st.selectbox(
            "Select Problematic Side Effect",
            options=barkla_side_effects_names,
            help=f"Select from {len(barkla_side_effects_names)} side effects",
            placeholder='Choose an option',
            index=None
        )
    else:
        st.error("Failed to fetch data.")


# Selection Search Response -----------------------------------------------
# Initialize search state
if 'has_searched_for_culprits' not in st.session_state:
    st.session_state.has_searched_for_culprits = False

# Search for Culprits
search_for_culprits = st.button("Search", key="search_for_culprits")
if search_for_culprits:
    st.session_state.has_searched_for_culprits = True

# Fetch Culprits
if st.session_state.has_searched_for_culprits and selected_side_effect and selected_drugs_A:
    culprits = api_call("culprit_drug", params={"side_effect": selected_side_effect, "drug_list": selected_drugs_A})
    if culprits:
        # Convert to DataFrame for better display
        df = pd.DataFrame(culprits)
        
        # Format the combined_rate to 2 decimal places
        df['combined_rate'] = df['combined_rate'].round(2)
        
        # Rename columns for display
        df = df.rename(columns={
            'drug_name': 'Drug Name',
            'combined_rate': 'Rate',
            'score': 'Likelihood Score'
        })
        
        st.markdown(f"Drugs most likely to cause **{selected_side_effect}**.")
        st.dataframe(
            df,
            hide_index=True,
            column_config={
                "Drug Name": st.column_config.TextColumn("Drug Name", width="medium"),
                "Rate": st.column_config.NumberColumn("Combined Rate", format="%.2f"),
                "Score": st.column_config.NumberColumn("Score", format="%.2f")
            }
        )
    else:
        st.info("No drugs found for the selected side effect.")

    # Display unavailable drugs in a more structured way
    if any(drug in unavailable_drug_names for drug in selected_drugs_A):
        selected_unavailable_drugs = [drug for drug in selected_drugs_A if drug in unavailable_drug_names]
        st.warning(
            "No data available for the following drugs\n- " + 
            "\n- ".join(selected_unavailable_drugs)
        )
    # st.divider()
    # st.write(f"Number of drugs with data: {len(available_drug_names)}")
    # st.write(f"Number of drugs without data: {len(unavailable_drug_names)}")

#  =================================================================================
#  =================================================================================
#  =================================================================================

st.divider()
# Section title
st.header("Identify Probable Side Effects by Drug Selection")
st.write("""Display the top 10 side effects for a portfolio of drugs by summing the total "combined" rate of all possible side effects across all drugs selected.
           For each of the top 10 side effects, also display the drug with the highest contributing combined rate.""")

# Drug Selection ---------------------------------------------------------------
if barkla_drug_names and drug_names:
    selected_drugs_B = st.multiselect(
        "Select Drug Portfolio",
        options=available_drug_names,
        help=f"Search and select from {len(available_drug_names)} drugs",
        key="selected_drugs_B"
    )
else:
    st.error("Failed to fetch data.")


# Selection Search Response -----------------------------------------------
# Initialize search state
if 'has_searched_for_side_effects' not in st.session_state:
    st.session_state.has_searched_for_side_effects = False

# Search for Side Effects
search_for_side_effects = st.button("Search", key="search_for_side_effects")
if search_for_side_effects:
    st.session_state.has_searched_for_side_effects = True   

# Fetch Side Effects
if st.session_state.has_searched_for_side_effects and selected_drugs_B:
    side_effects = api_call("most_likely_side_effects", params={"drug_list": selected_drugs_B})
    if side_effects:
        side_effects_df = pd.DataFrame(side_effects)
        
        # Format the combined_rate to 2 decimal places
        side_effects_df['total_rate'] = side_effects_df['total_rate'].round(2)
        
        # Rename columns for display
        side_effects_df = side_effects_df.rename(columns={
            'side_effect': 'Side Effect',
            'total_rate': 'Total Rate',
            'most_likely_drug': 'Most Likely Drug'
        })
        side_effects_df = side_effects_df[['Side Effect', 'Most Likely Drug', 'Total Rate']]
        
        st.markdown(f"Top 10 most likely side effects and responsible drugs when taking **{
            ', '.join(selected_drugs_B[:-1])}** and **{selected_drugs_B[-1]}**.")
        st.dataframe(
            side_effects_df,
            hide_index=True,
            column_config={
                "Side Effect": st.column_config.TextColumn("Side Effect", width="medium"),
                "Rate": st.column_config.NumberColumn("Total Rate", format="%.2f"),
                "Drug": st.column_config.TextColumn("Most Likely Drug", width="medium")
            }
        )


#  =================================================================================
#  =================================================================================
#  =================================================================================

st.divider()
# Section title
st.header("Identify Probable Side Effects by Drug Selection (FAERS)")
st.write("""Return the top 5 most commonly occuring side effects for a given portfolio of drugs based on FAERS data.""")

# Initialize search state
if 'has_searched_for_FAERS_side_effects' not in st.session_state:
    st.session_state.has_searched_for_FAERS_side_effects = False

# Drug Selection ---------------------------------------------------------------
if faers_drug_names:
    selected_drugs_C = st.multiselect(
        "Select Drug Portfolio",
        options=faers_drug_names,
        help=f"Search and select from {len(faers_drug_names)} drugs",
        key="selected_drugs_C"
    )
else:
    st.error("Failed to fetch data.")

# Search for Side Effects
search_for_FAERS_side_effects = st.button("Search", key="search_for_FAERS_side_effects")
if search_for_FAERS_side_effects:
    st.session_state.has_searched_for_FAERS_side_effects = True   

if st.session_state.has_searched_for_FAERS_side_effects and selected_drugs_C:
    side_effects = api_call("most_likely_side_effects_faers", params={"drug_list": selected_drugs_C})
    if side_effects:
        # Convert to DataFrame
        df_faers = pd.DataFrame(side_effects)
        
        # Format the rate to percentage with 1 decimal place
        df_faers['rate'] = (df_faers['rate'] * 100).round(1)
        # Convert Wilson interval to percentage as well
        df_faers['wilson_interval'] = (df_faers['wilson_interval'] * 100).round(1)
        
        # Rename columns for better display
        df_faers = df_faers.rename(columns={
            'drug_name': 'Drug',
            'side_effect': 'Side Effect',
            'drug_side_effect_occurrence_count': 'Occurrences',
            'case_count_with_drug': 'Total Cases',
            'rate': 'Rate (%)',
            'wilson_interval': 'Wilson Interval'
        })
        
        # Reorder columns and round confidence score
        df_faers['Wilson Interval'] = df_faers['Wilson Interval'].round(2)
        df_faers = df_faers[['Drug', 'Side Effect', 'Occurrences', 'Total Cases', 'Rate (%)', 'Wilson Interval']]
        
        st.markdown(f"Most common side effects reported in FAERS for **{', '.join(selected_drugs_C[:-1])}** and **{selected_drugs_C[-1]}**.")
        
        # Create a separate dataframe for each drug
        for drug in selected_drugs_C:
            drug_df = df_faers[df_faers['Drug'] == drug].copy()
            if not drug_df.empty:
                st.write(f"**{drug}** (use cases: {drug_df['Total Cases'].values[0]})")
                st.dataframe(
                    drug_df.drop(columns=['Drug', 'Total Cases']),  # Remove drug column since it's redundant
                    hide_index=True,
                    column_config={
                        "Side Effect": st.column_config.TextColumn("Side Effect", width="medium"),
                        "Occurrences": st.column_config.NumberColumn("# of Cases with Side Effect", format="%d"),
                        "Rate (%)": st.column_config.NumberColumn("Rate %", format="%.1f"),
                        "Wilson Interval": st.column_config.NumberColumn("±95% CI", format="%.1f")
                    }
                )
    else:
        st.info("No side effects found for the selected drugs.")

