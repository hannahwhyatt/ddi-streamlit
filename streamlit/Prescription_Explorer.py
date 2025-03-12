import streamlit as st
import pandas as pd
from itertools import combinations  # Add this import at the top of the file
import easyocr
import numpy as np
import cv2

from utils import api_call, join_interactions_and_side_effects
from constants import DDI_COLUMNS, SIDE_EFFECT_COLUMNS, LIFESTYLE_FACTORS, vaccine_list, patient_ids_temp
from components.side_effects_tab.display_side_effects import display_side_effects_table, display_key, display_vaccine_interactions
from components.interactions_tab.interactions_list import interactions_list

# Data --------------------------------------------------------------------------
# Fetch the set of drug names for the search box
drug_names = api_call("drug_names")

# Layout ------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="Drug Interaction and Side Effects Tool")

st.markdown("""
<style>
    .main .block-container {
        max-width: 95%;
        padding-top: 2rem;
        padding-bottom: 4rem;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# VEC LOGO
col01, col02 = st.columns([8, 1])
with col02:
    st.image("streamlit/assets/branding.png", width=250)

# App title
st.header("Prescription Explorer")
st.write("Enter the patient ID, upload a photo of the prescription, or manually select prescription drugs from the dropdown.")

# Initialize a counter for generating unique keys if it doesn't exist
if 'input_key_counter' not in st.session_state:
    st.session_state.input_key_counter = 0

# Patient Information Section ---------------------------------------------------
col_patient, col_upload = st.columns([0.6, 0.4])

with col_patient:
    with st.container(border=True):
        st.subheader("Patient Information")
        col_id, col_button, col_reset_button = st.columns([0.4, 0.3, 0.3])
        
        with col_id:
            # Use a dynamic key based on the counter
            current_key = f"patient_id_input_{st.session_state.input_key_counter}"
            # patient_id_str = st.text_input("Enter Patient ID", key=current_key)
            patient_id_int = st.selectbox("Select Patient ID", options=patient_ids_temp, key=current_key, index=None)
            try:
                patient_id = int(patient_id_int) if patient_id_int else None
                if patient_id is not None and patient_id < 1:
                    st.error("Patient ID must be a positive number")
                    patient_id = None
            except ValueError:
                st.error("Please enter a valid number")
                patient_id = None
        
        with col_button:
            # Add an empty element with the same height as the label
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            # Disable the button if patient_id is None
            get_patient_info = st.button("Get Patient Information", 
                                       use_container_width=True,
                                       disabled=patient_id is None)
        
        with col_reset_button:
            # Add an empty element with the same height as the label
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            # Disable the button if patient_id is None
            reset_patient_info = st.button("Reset", use_container_width=True, disabled=patient_id is None)
            if reset_patient_info:
                # Clear all patient-related session state variables
                st.session_state.patient_data = None
                st.session_state.diagnoses_data = None  # Add this line to clear diagnoses data
                st.session_state.drug_multiselect = []
                st.session_state.search_box = []
                st.session_state.has_searched = False
                # Increment the counter to generate a new key for the text input
                st.session_state.input_key_counter += 1
                st.rerun()
        
        if get_patient_info or ('patient_data' in st.session_state and st.session_state.patient_data) or ('diagnoses_data' in st.session_state and st.session_state.diagnoses_data):
            if get_patient_info:
                # First try to get patient data without showing error
                patient_data = api_call("patient_portfolio_mimic", params={"patient_id": patient_id}, show_error=False)
                
                # Only proceed to get diagnoses if patient data was successfully retrieved
                if patient_data:
                    # First try to get diagnoses data without showing error
                    diagnoses_data = api_call("patient_diagnoses_mimic", params={"patient_id": patient_id}, show_error=False)
                    
                    # Fetch admission details for each diagnosis
                    admission_details = {}
                    if diagnoses_data:  # Only process if diagnoses_data is not None
                        for diagnosis in diagnoses_data:
                            for hadm_id in diagnosis['hadm_ids']:
                                if hadm_id not in admission_details:
                                    # Get admission details for this hadm_id
                                    admission_info = api_call("admission_details", params={"hadm_id": hadm_id})
                                    if admission_info:
                                        admission_details[hadm_id] = admission_info
                    
                    # Store data in session state
                    st.session_state.patient_data = patient_data
                    st.session_state.diagnoses_data = diagnoses_data if diagnoses_data else []
                    st.session_state.admission_details = admission_details
                    
                else:
                    # If patient data retrieval failed, show error and don't proceed
                    st.error("Patient ID not found. Please check the patient ID and try again.")
                    # Clear any previous data
                    st.session_state.patient_data = None
                    st.session_state.diagnoses_data = None
            else:
                patient_data = st.session_state.patient_data
                diagnoses_data = st.session_state.diagnoses_data
            
            # Only display patient information if we have valid data
            if patient_data:
                # Display patient information
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.write(f"**Patient ID:** {patient_data['patient_id']}")
                    st.write(f"**Sex:** {patient_data['patient_gender']}")
                
                with col_info2:
                    st.write(f"**Age:** {abs(patient_data['patient_age'])}")
                    st.write(f"**Date of Birth:** {patient_data['patient_dob'].split()[0]}")
                
                with st.expander("**Prescriptions**", expanded=False):
                    # Process prescriptions
                    if 'prescriptions' in patient_data and patient_data['prescriptions']:
                        # Extract unique drugs from prescriptions
                        unique_drugs = set()
                        for rx in patient_data['prescriptions']:
                            # Get both drug name and generic name when available
                            drug_name = rx.get('drug', '').strip()
                            generic_name = rx.get('drug_name_generic', '').strip()
                            
                            # Add both names if they exist
                            if drug_name:
                                unique_drugs.add(drug_name.lower())
                            if generic_name:
                                unique_drugs.add(generic_name.lower())
                        
                        # Find matching drugs in our drug_names list
                        matching_drugs = [drug for drug in unique_drugs if drug in drug_names]
                        
                        if matching_drugs:
                            st.write(f"**Found {len(matching_drugs)} medications in patient records**")
                            
                            # Update the multiselect with these drugs
                            if 'drug_multiselect' not in st.session_state:
                                st.session_state.drug_multiselect = []
                            
                            st.session_state.drug_multiselect = matching_drugs
                            
                            # Display prescription table
                            prescription_df = pd.DataFrame(patient_data['prescriptions'])
                            prescription_df['start_date'] = pd.to_datetime(prescription_df['start_date']).dt.date
                            prescription_df['end_date'] = pd.to_datetime(prescription_df['end_date']).dt.date
                            
                            # Create a copy of the dataframe with renamed columns
                            display_df = prescription_df[['drug', 'drug_name_generic', 'dose_val_rx', 'dose_unit_rx', 'route', 'start_date', 'end_date']].copy()
                            # Rename columns to be more user-friendly
                            display_df.columns = ['Drug', 'Generic Name', 'Dose', 'Unit', 'Route', 'Start Date', 'End Date']
                            # Display dataframe with hide_index=True
                            st.dataframe(display_df, use_container_width=True, hide_index=True)
                        else:
                            st.warning("No matching medications found in our database.")
                    else:
                        st.warning("No prescription data available for this patient.")

                with st.expander("**Conditions**", expanded=False):
                    if 'diagnoses_data' in st.session_state and st.session_state.diagnoses_data:
                        st.write("**Diagnoses**")
                        
                        # # Create a list to hold the expanded diagnosis data
                        # expanded_diagnoses = []
                        
                        # for diagnosis in st.session_state.diagnoses_data:
                        #     # For each hadm_id, create a row with admission details
                        #     for hadm_id in diagnosis['hadm_ids']:
                        #         if hadm_id in st.session_state.admission_details:
                        #             admission = st.session_state.admission_details[hadm_id]
                        #             expanded_diagnoses.append({
                        #                 'ICD-9 Code': diagnosis['icd9_code'],
                        #                 'Short Description': diagnosis['short_title'],
                        #                 'Full Description': diagnosis['long_title'],
                        #                 'Admission Date': admission['admission_time'].split()[0] if admission['admission_time'] else "",
                        #                 'Discharge Date': admission['discharge_time'].split()[0] if admission['discharge_time'] else "",
                        #                 'HADM ID': admission['hadm_id'] if admission['hadm_id'] else ""
                        #             })
                        #         else:
                        #             # If no admission details found, still include the diagnosis
                        #             expanded_diagnoses.append({
                        #                 'ICD-9 Code': diagnosis['icd9_code'],
                        #                 'Short Description': diagnosis['short_title'],
                        #                 'Full Description': diagnosis['long_title'],
                        #                 'Admission Date': "",
                        #                 'Discharge Date': "",
                        #                 'HADM ID': ""
                        #             })
                        
                        # # Create dataframe from expanded diagnoses
                        # if expanded_diagnoses:
                        #     display_diagnoses_df = pd.DataFrame(expanded_diagnoses)
                        #     st.dataframe(display_diagnoses_df, 
                        #             use_container_width=True,
                        #             hide_index=True)
                        if st.session_state.diagnoses_data:
                            diagnoses_df = pd.DataFrame(st.session_state.diagnoses_data)
                            display_diagnoses_df = diagnoses_df[['icd9_code', 'short_title', 'long_title']]
                            display_diagnoses_df.columns = ['ICD-9 Code', 'Short Description', 'Full Description']
                            st.dataframe(display_diagnoses_df, use_container_width=True, hide_index=True)
                        else:
                            st.warning("No diagnoses data available for this patient.")
                    else:
                        st.warning("No diagnoses data available for this patient.")

with col_upload:
    with st.container(border=True):
        st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)

        # Handle prescription upload
        prescription_image = st.file_uploader("Or, upload a photo to detect drug names automatically.", type=["jpg", "jpeg", "png"], key="prescription_uploader")

        if prescription_image is not None:
            st.session_state.image_collapsed = False
            
            # Only reset selections if a new image is uploaded
            if 'last_image_name' not in st.session_state or st.session_state.last_image_name != prescription_image.name:
                st.session_state.search_box = []
                if 'drug_multiselect' in st.session_state:
                    st.session_state.drug_multiselect = []
                st.session_state.last_image_name = prescription_image.name
            
            # Process OCR only if we haven't processed this image before
            if 'processed_image_name' not in st.session_state or st.session_state.processed_image_name != prescription_image.name:
                detected_drugs = []
                image_bytes = prescription_image.read()
                reader = easyocr.Reader(['en'])
                results = reader.readtext(image_bytes)
                
                # Convert image bytes to numpy array for display
                nparr = np.frombuffer(image_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Draw bounding boxes and store processed image
                for detection in results:
                    text = detection[1].lower()
                    if text in drug_names:
                        detected_drugs.append(text)
                        bbox = np.array(detection[0], dtype=np.int32).reshape((-1, 1, 2))
                        cv2.polylines(img, [bbox], True, (255, 0, 0), 3)
                        cv2.putText(img, text, (bbox[0][0][0], bbox[0][0][1] - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                
                # Store the processed image in session state
                st.session_state.processed_img = img
                st.session_state.processed_image_name = prescription_image.name
                
                if detected_drugs:
                    st.write(f"""Identified **{len(set(detected_drugs))}** drug names from the image.""")
                    st.write("""⚠️ Please carefully review and confirm the selection before searching.""")
                    st.session_state.search_box = list(set(st.session_state.search_box + detected_drugs))
                    st.session_state.drug_multiselect = list(set(st.session_state.drug_multiselect + detected_drugs))

            # Display the image with bounding boxes
            if hasattr(st.session_state, 'processed_img'):
                image_expander = st.expander("Uploaded prescription with detected drug names", expanded=st.session_state.image_collapsed)
                with image_expander:
                    st.image(st.session_state.processed_img, use_container_width=True)

# Drug Selection ---------------------------------------------------------------
if drug_names:
    with st.container(border=True):
        col_drugs, col_lifestyle, col_search = st.columns([0.4, 0.4, 0.2])
        
        with col_drugs:
            # Create multiselect with updated default values
            selected_drugs = st.multiselect(
                "Select Drugs",
                options=drug_names,
                help=f"Search and select from {len(drug_names)} drugs",
                key="drug_multiselect"
            )
        
        with col_lifestyle:
            selected_factors = st.multiselect(
                "Select Lifestyle Factors",
                options=LIFESTYLE_FACTORS,
                default=LIFESTYLE_FACTORS,
                help=f"Search and select from {len(LIFESTYLE_FACTORS)} lifestyle factors"
            )
        
        with col_search:
            # Add vertical space to align button with multiselects
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            # Initialize search state
            if 'has_searched' not in st.session_state:
                st.session_state.has_searched = False
            search_button = st.button("Search", key="search_button", use_container_width=True)
            # Update search state when button is clicked
            if search_button:
                st.session_state.has_searched = True
                st.session_state.image_collapsed = True
else:
    st.error("Failed to fetch data.")

# Drug Selection Search Response -----------------------------------------------

# Fetch side effect and interaction data for selected drugs
if st.session_state.has_searched and selected_drugs:
    # Get interactions
    tab_interactions, tab_side_effects = st.tabs(["Interactions", "All Side Effects"])
    interactions = api_call("interactions", params={"drug_list": [*selected_drugs, *selected_factors, *vaccine_list]})
    if interactions:
        interactions_df = pd.DataFrame(interactions)[DDI_COLUMNS]  # Only select the columns we want

        # Corrected filtering for lifestyle interactions
        lifestyle_interactions = interactions_df[
            interactions_df['drug_a_concept_name'].isin(selected_factors) | 
            interactions_df['drug_b_concept_name'].isin(selected_factors)
        ]
        # Corrected filtering for vaccine interactions
        vaccine_interactions = interactions_df[
            interactions_df['drug_a_concept_name'].isin(vaccine_list) | 
            interactions_df['drug_b_concept_name'].isin(vaccine_list)
        ]
        all_other_interactions = interactions_df.drop(lifestyle_interactions.index).drop(vaccine_interactions.index)
        
        with tab_interactions:

            st.write(f"**Found {len(interactions_df)} interactions.**")
           
            # st.markdown(f"#### Interactions due to selected drugs ({len(all_other_interactions)})")
            with st.expander(f"**Interactions due to selected drugs ({len(all_other_interactions)})**", expanded=False):
                if not all_other_interactions.empty:
                    interactions_list(selected_drugs, all_other_interactions)
                else:
                    st.info("No interactions found.")

            # st.divider()
            # st.markdown(f"#### Interactions due to lifestyle factors ({len(lifestyle_interactions)})")
            with st.expander(f"**Interactions due to lifestyle factors ({len(lifestyle_interactions)})**", expanded=False):
                if not lifestyle_interactions.empty:
                    interactions_list(selected_drugs, lifestyle_interactions)
                else:
                    st.info("No interactions found.")

            # st.divider()
            # st.markdown(f"#### Interactions due to vaccines ({len(vaccine_interactions)})")
            with st.expander(f"**Interactions due to vaccines ({len(vaccine_interactions)})**", expanded=False):
                if not vaccine_interactions.empty:
                    interactions_list(selected_drugs, vaccine_interactions)
                else:
                    st.info("No interactions found.")



    else:
        with tab_interactions:
            st.warning("No interactions found for selected drugs.")
    
    # Get side effects
    side_effects = api_call("side_effects", params={"drug_list": [*selected_drugs, *selected_factors]})
    if side_effects:
        side_effects_df = pd.DataFrame(side_effects)[SIDE_EFFECT_COLUMNS]  # Only select the columns we want
        hlt_side_effects = api_call("ancestor_side_effects", params={"pt_list": side_effects_df['event_concept_name'].tolist()})
        side_effects_df["ancestor"] = side_effects_df["event_concept_name"].map(hlt_side_effects)

        if interactions:
            # Join interactions and side effects - show the full picture
            side_effects_df = join_interactions_and_side_effects(interactions_df, side_effects_df)        
        
        lifestyle_side_effects_df = side_effects_df[
            side_effects_df['drug_concept_name'].str.split(' + ').apply(
                lambda x: any(factor.strip().lower() in y.strip().lower() for factor in selected_factors for y in x)
            )
        ]

        vaccine_side_effects_df = side_effects_df[
            side_effects_df['drug_concept_name'].str.split(' + ').apply(
                lambda x: any(factor.strip().lower() in y.strip().lower() for factor in vaccine_list for y in x)
            )
        ]
        

        drug_side_effects_df = side_effects_df.drop([*lifestyle_side_effects_df.index, *vaccine_side_effects_df.index])

        with tab_side_effects:
            display_key()
            
            # Drug side effects
            drug_effects_expander = st.expander("**Due to selected drugs**", expanded=True)
            with drug_effects_expander:
                if len(drug_side_effects_df) > 0:
                    display_side_effects_table(drug_side_effects_df, key_suffix="drugs")
                else:
                    st.info("No adverse effects due to selected drugs found.")
            
            # Lifestyle factors
            lifestyle_expander = st.expander("**Due to lifestyle factor interactions**", expanded=True)
            with lifestyle_expander:
                if len(lifestyle_side_effects_df) > 0:
                    display_side_effects_table(lifestyle_side_effects_df, hlt=False, key_suffix="lifestyle")
                else:
                    st.info("No adverse effects due to drug interactions with lifestyle factors found.")
            
            # Vaccine interactions
            vaccine_expander = st.expander("**Due to vaccine interactions**", expanded=True)
            with vaccine_expander:
                if len(vaccine_side_effects_df) > 0:
                    display_vaccine_interactions(vaccine_side_effects_df)
                else:
                    st.info("No adverse effects due to drug interactions with vaccines found.")
    else:
        with tab_side_effects:
            st.warning("No side effects found for selected drugs.")



# Not in use
            # Write out pairs with no known interactions
            # st.write("##### No interactions found for the following drugs:")
            # all_items = [*selected_drugs, *selected_factors]
            # for item in all_items:
            #     if item not in interactions_df['drug_a_concept_name'].values \
            #     and item not in interactions_df['drug_b_concept_name'].values:
            #         st.markdown(f'''
            #             <div style="display: flex; align-items: center; gap: 5px;">
            #                 <div style="width: 12px; height: 12px; border-radius: 50%; background-color: green"></div>
            #                     <span>{item}</span>
            #             </div>''', unsafe_allow_html=True)
            ## OR
            # for drug_1, drug_2 in combinations(all_items, 2):
            #     if not interactions_df[
            #         ((interactions_df['drug_a_concept_name'].isin([drug_1, drug_2])) &
            #          (interactions_df['drug_b_concept_name'].isin([drug_1, drug_2])))
            #     ].empty:
            #         continue
            #     st.write(f"{drug_1} + {drug_2}")