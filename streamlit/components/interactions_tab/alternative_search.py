import streamlit as st
import pandas as pd
from utils import api_call
from constants import severity_colour_map, NAME_EVENT_COLUMNS, LIFESTYLE_FACTORS

def alternative_search(selected_drugs, drug_indications_df, drug, index):
    """ Generate alternative drug search interface """
    # Initialize session state for this specific drug's alternatives
    state_key = f"alternatives_{drug}_{index}"
    if state_key not in st.session_state:
        st.session_state[state_key] = None

    if not drug_indications_df.empty:
        drug_indications_df.columns = NAME_EVENT_COLUMNS
        selected_indications = st.multiselect(
            f"Select all relevant indications for **{drug}**",
            options=drug_indications_df['event_concept_name'],
            key=f"indications_select_{drug}_{index}"
        )
        if st.button(f"Find alternative drugs for **{drug}**", key=f"indication_search_{drug}_{index}"):
            if selected_indications:
                drug_alternatives = api_call("alternative_search", 
                                          params={"replaced_drug": drug,
                                                  "indication_list": selected_indications})
                if drug_alternatives:
                    for item in drug_alternatives:
                        replacement_drug_interactions = api_call("alternative_interactions", 
                                                            params={
                                                                "replaced_drug": drug,
                                                                "replacement_drug": item["drug_concept_name"],
                                                                "drug_list": selected_drugs
                                                            })
                        item['interactions'] = replacement_drug_interactions
                        item['max_severity'] = max([int(i["severity_code"]) for i in replacement_drug_interactions]) if replacement_drug_interactions else 0
                    drug_alternatives = sorted(drug_alternatives, key=lambda x: x['max_severity'])
                    # Store results in session state
                    st.session_state[state_key] = {
                        'alternatives': drug_alternatives,
                        'indications': selected_indications
                    }
                else:
                    st.warning("No alternatives found for selected indications.")
            else:
                st.warning("Please select at least one indication to search.")
        
        # Display results if they exist and indications match
        if st.session_state[state_key] and set(selected_indications) == set(st.session_state[state_key]['indications']):
            # Get drug class for the alternative drug
            drug_classes = api_call("drug_classes", params={"drug_list": [item["drug_concept_name"] for item in st.session_state[state_key]['alternatives']]})
            original_drug_class = api_call("drug_classes", params={"drug_list": [drug]})
            # alternative_results(drug, index, st.session_state[state_key]['alternatives'])
            alternative_results_with_drug_classes(drug, index, st.session_state[state_key]['alternatives'], drug_classes, original_drug_class)
    else:
        if drug not in LIFESTYLE_FACTORS:
            st.info(f"Alternative search not available for {drug}: no indications found.")

def alternative_results_with_drug_classes(drug, index, dict, drug_classes, original_drug_class):
    """ Generate alternative drug search results with drug classes """
    # Group alternative drugs by drug class
    drug_classes_dict = {}
    unknown_class_drugs = []  # New list for drugs without a class
    
    # Create case-insensitive drug class lookup
    if drug_classes:
        drug_classes_lower = {item['drug_name'].lower(): item['title'] for item in drug_classes}
    else:
        drug_classes_lower = {}
    
    for item in dict:
        drug_name = item['drug_concept_name'].lower()
        drug_class = drug_classes_lower.get(drug_name)
        if drug_class:
            if drug_class not in drug_classes_dict:
                drug_classes_dict[drug_class] = []
            drug_classes_dict[drug_class].append(item)
        else:
            unknown_class_drugs.append(item)

    # Get the original drug's class title
    original_class_title = original_drug_class[0]['title'] if original_drug_class else None

    # First create a container with border
    with st.container(border=True):
        # Then create tabs inside the container
        no_interactions_tab, with_interactions_tab = st.tabs(["Alternative drugs without interactions", "Alternative drugs with interactions"])
        
        with no_interactions_tab:

            # Show original drug class first
            same_class_no_interactions = False
            if original_class_title:
                st.markdown(f"##### Other {original_class_title.lower()}")
                if original_class_title and original_class_title in drug_classes_dict:
                    same_class_no_interactions = [item for item in drug_classes_dict[original_class_title] if not item['interactions']]
                    if same_class_no_interactions:
                        display_alternatives_grid(same_class_no_interactions, drug_classes_lower)
            if not same_class_no_interactions and original_class_title:
                st.write("None found")

            if original_class_title:
                st.markdown("##### Other classes of drug")
            # Show other drug classes
            other_classes_no_interactions = False
            for drug_class, items in drug_classes_dict.items():
                if drug_class != original_class_title:
                    items_no_interactions = [item for item in items if not item['interactions']]
                    if items_no_interactions:
                        if not other_classes_no_interactions:
                            other_classes_no_interactions = True
                        st.markdown(f"**{drug_class}**")
                        display_alternatives_grid(items_no_interactions, drug_classes_lower)
            
            # Show drugs without a class
            unknown_class_no_interactions = [item for item in unknown_class_drugs if not item['interactions']]
            if unknown_class_no_interactions:
                if not other_classes_no_interactions:
                    other_classes_no_interactions = True
                if original_class_title:
                    st.markdown("**Other drugs, classification not available**")
                display_alternatives_grid(unknown_class_no_interactions, drug_classes_lower)

            if not other_classes_no_interactions and not unknown_class_no_interactions and original_class_title:
                st.write("None found")

        
        with with_interactions_tab:

            # Show original drug class first
            same_class_with_interactions = False
            if original_class_title:
                st.markdown(f"##### Other {original_class_title.lower()}")
                if original_class_title and original_class_title in drug_classes_dict:
                    same_class_with_interactions = [item for item in drug_classes_dict[original_class_title] if item['interactions']]
                    if same_class_with_interactions:
                        # Sort by max severity
                        same_class_with_interactions.sort(key=lambda x: x['max_severity'])
                        display_alternatives_with_interactions(same_class_with_interactions, drug_classes_lower)
            if not same_class_with_interactions and original_class_title:
                st.write("None found")

            if original_class_title:
                st.markdown("##### Other classes of drug")
            # Show other drug classes
            other_classes_with_interactions = False
            for drug_class, items in drug_classes_dict.items():
                if drug_class != original_class_title:
                    items_with_interactions = [item for item in items if item['interactions']]
                    if items_with_interactions:
                        if not other_classes_with_interactions:
                            other_classes_with_interactions = True
                        st.markdown(f"**{drug_class}**")
                        # Sort by max severity
                        items_with_interactions.sort(key=lambda x: x['max_severity'])
                        display_alternatives_with_interactions(items_with_interactions, drug_classes_lower)
            
            # Show drugs without a class that have interactions
            unknown_class_with_interactions = [item for item in unknown_class_drugs if item['interactions']]
            if unknown_class_with_interactions:
                if not other_classes_with_interactions:
                    other_classes_with_interactions = True
                if original_class_title:
                    st.markdown("**Other drugs, classification not available**")
                # Sort by max severity
                unknown_class_with_interactions.sort(key=lambda x: x['max_severity'])
                display_alternatives_with_interactions(unknown_class_with_interactions, drug_classes_lower)

            if not other_classes_with_interactions and not unknown_class_with_interactions and original_class_title:
                st.write("None found")


def display_alternatives_grid(items, drug_classes_lower):
    """Display alternatives in a grid layout without interactions"""
    cols = st.columns(3)
    for i, item in enumerate(items):
        with cols[i % 3]:
            indications = api_call("single_drug_indications", params={"drug_name": item["drug_concept_name"]})
            indications_df = pd.DataFrame(indications) if indications else pd.DataFrame()
            indications_str = ", ".join(indications_df['event_concept_name']) if not indications_df.empty else ""
            
            drug_class = drug_classes_lower.get(item['drug_concept_name'].lower(), '')
            st.markdown(
                f"[**{item['drug_concept_name']}**](https://bnf.nice.org.uk/drugs/{item['drug_concept_name']})", 
                help=f"Drug class: {drug_class}\nIndications: {indications_str}"
            )

def display_alternatives_with_interactions(items, drug_classes_lower):
    """Display alternatives with interactions in a condensed format"""
    for item in items:
        # Create a container with border instead of an expander
        with st.container(border=True):
            # Header section - more compact layout
            cols = st.columns([3, 2])
            with cols[0]:
                indications = api_call("single_drug_indications", params={"drug_name": item["drug_concept_name"]})
                indications_df = pd.DataFrame(indications) if indications else pd.DataFrame()
                if not indications_df.empty:
                    indications_df.columns = NAME_EVENT_COLUMNS
                    indications_str = ", ".join(indications_df['event_concept_name'])
                else:
                    indications_str = ""
                
                drug_class = drug_classes_lower.get(item['drug_concept_name'].lower(), '')
                st.markdown(
                    f"[**{item['drug_concept_name']}**](https://bnf.nice.org.uk/drugs/{item['drug_concept_name']})", 
                    help=f"Drug class: {drug_class}\nIndications: {indications_str}"
                )
                
                # Move checkbox here, right below the drug name
                show_interactions = st.checkbox(f"Show interactions", key=f"show_{item['drug_concept_name']}_{id(item)}")
            
            # Sort interactions by severity
            item['interactions'] = sorted(item['interactions'], key=lambda x: x['severity_code'], reverse=True)
            
            with cols[1]:
                severity_color = severity_colour_map.get(item['max_severity'], "grey")
                # More visually appealing severity and interaction count display
                st.markdown(
                    f'<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; '
                    f'padding: 8px; height: 100%;">'
                    f'<div style="display: flex; align-items: center; margin-bottom: 8px; '
                    f'background-color: rgba(0,0,0,0.03); padding: 5px 10px; border-radius: 12px;">'
                    f'<span style="margin-right: 8px; font-weight: 500;">Maximum severity {item["max_severity"]}</span>'
                    f'<div style="width: 12px; height: 12px; border-radius: 50%; background-color: {severity_color};"></div>'
                    f'</div>'
                    f'<div style="font-size: 0.95em; color: #555;">{len(item["interactions"])} interaction(s)</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            
            # Display interactions in a compact table
            if show_interactions:
                for i, interaction in enumerate(item['interactions']):
                    # if i > 0:  # Only add divider between interactions, not before the first one
                    #     st.divider()
                    
                    # More compact and visually appealing interaction display
                    int_cols = st.columns([4, 1])
                    with int_cols[0]:
                        st.markdown(
                            f"<div style='margin: 5px 0; padding: 5px 0;'>"
                            f"<span style='font-weight: 600; font-size: 1.05em;'>{interaction['drug_a_concept_name']} + {interaction['drug_b_concept_name']}</span><br>"
                            f"<span style='font-size: 0.95em; color: #555; margin-top: 4px; display: block;'>"
                            f"<span style='font-weight: 500;'>Effect:</span> {interaction['event_concept_name']}</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    with int_cols[1]:
                        severity_color = severity_colour_map.get(interaction["severity_code"], "grey")
                        st.markdown(
                            f'<div style="display: flex; align-items: center; justify-content: flex-end; height: 100%; padding: 5px 0;">'
                            f'<div style="display: flex; align-items: center; background-color: rgba(0,0,0,0.03); '
                            f'padding: 4px 8px; border-radius: 12px;">'
                            f'<div style="width: 10px; height: 10px; border-radius: 50%; '
                            f'background-color: {severity_color}; margin-right: 6px;"></div>'
                            f'<span style="font-size: 0.9em; font-weight: 500;">Severity {interaction["severity_code"]}</span>'
                            f'</div></div>',
                            unsafe_allow_html=True
                        )

# def alternative_results(drug, index, dict):
#     """ Generate alternative drug search results """
#     # 
#     for item in dict:
#         # Get indications for the alternative drug
#         indications = api_call("single_drug_indications", params={"drug_name": item["drug_concept_name"]})
#         indications_df = pd.DataFrame(indications)
#         indications_df.columns = NAME_EVENT_COLUMNS
#         indications_str = ", ".join(indications_df['event_concept_name'])
#         st.markdown(
#                 f"[**{item['drug_concept_name']}**](https://bnf.nice.org.uk/drugs/{item['drug_concept_name']})", 
#                 help=f"Indications: {indications_str}"
#             )

#         if item['interactions']:        
#             st.warning("⚠️ This alternative also has interactions:")
#             #  sort dictionary by max severity
#             item['interactions'] = sorted(item['interactions'], key=lambda x: x['severity_code'], reverse=True)
#             with st.container(border=True):
#                 for interaction in item['interactions']:
#                     st.write(f"{interaction["drug_a_concept_name"]} + {interaction["drug_b_concept_name"]}")
#                     st.write(f"**Interaction effect:** {interaction["event_concept_name"]}")
#                     if interaction["severity_bnf"] or interaction["severity_ansm"]:
#                         severities = []
#                         if interaction["severity_ansm"]: 
#                             severities.append(f"<i>{interaction['severity_ansm']}</i> (ANSM)")
#                         if interaction["severity_bnf"]:
#                             severities.append(f"<i>{interaction['severity_bnf']}</i> (BNF)")
#                         severity_color = severity_colour_map.get(interaction["severity_code"], "grey")
#                         st.markdown(
#                             f'<div style="display: flex; align-items: center; gap: 10px; padding-bottom: 10px;">'
#                             f'<b>Severity:</b> {", ".join(severities)}. Severity Severity {interaction["severity_code"]} '
#                             f'<div style="width: 20px; height: 20px; border-radius: 50%; '
#                             f'background-color: {severity_color};"></div></div>',
#                             unsafe_allow_html=True
#                         )
#                     if interaction != item['interactions'][-1]:
#                         st.divider()
#         else:
#             st.success("✓ No interactions found with current drugs")