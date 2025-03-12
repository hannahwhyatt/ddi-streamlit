import streamlit as st
import pandas as pd
from constants import frequency_values, frequency_colour_map, vaccine_list
from collections import Counter
from components.side_effects_tab.process_side_effects import process_side_effects, process_side_effects_hlt

def display_side_effects_table(data, hlt=True, key_suffix=""):
    """ Display side effects table """
    if hlt:
        hlt = st.checkbox("Group side effects by Higher Level Term", 
                          value=False, 
                          key=f"hlt_checkbox_{key_suffix}")

    if hlt:
        df = process_side_effects_hlt(data)
    else:
        df = process_side_effects(data)

    if not hlt:
        def style_cell(val):
            # Get the current column name from the styler context
            column = style_cell.column_name
            
            # Skip styling for Total Score column
            if column == 'Total Frequency Score':
                return ''
            
            if val in frequency_colour_map:
                color = frequency_colour_map[val]
                return f'background-color: {color}59'  # 59 is hex for 35% opacity
            return ''

        # Apply styling using .map instead of .applymap
        styled_df = df.style
        for column in df.columns:
            if column != 'Total Frequency Score':
                style_cell.column_name = column
                styled_df = styled_df.map(style_cell, subset=[column])
    if hlt:
        def style_cell(val):
            # Get the current column name from the styler context
            column = style_cell.column_name
            
            # Skip styling for Total Score column
            if column == 'Total Frequency Score':
                return ''
            
            for f in frequency_colour_map.keys():
                if f in val:
                    color = frequency_colour_map[f]
                    return f'background-color: {color}59'  # 59 is hex for 35% opacity
            return ''
        
        styled_df = df.style
        for column in df.columns:
            if column != 'Total Frequency Score':
                style_cell.column_name = column
                styled_df = styled_df.map(style_cell, subset=[column])


    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=False
    )
    if hlt:
        st.write('Number of side effect groups: ', len(df))
    else:
        st.write('Number of side effects: ', len(df))

def display_key():
    key_map = {
        '4': 'Common or very common',
        '3': 'Uncommon',
        '2': 'Rare or very rare',
        '1': 'Frequency not known',
        '*': 'Interaction Effect (frequency not reported)',
        '-': 'Not reported',
    }

    legend_html = '<div style="display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px; margin-top: 10px; margin-left: 10px;">'
    for value, label in key_map.items():
        legend_html += f'''
            <div style="display: flex; align-items: center; gap: 5px;">
                <div style="width: 12px; height: 12px; border-radius: 50%; background-color: {frequency_colour_map[value]}99"></div>
                <span>{value} = {label}</span>
            </div>'''
    legend_html += '</div>'

    st.markdown(legend_html, unsafe_allow_html=True)

def display_vaccine_interactions(vaccine_side_effects_df):

    # Get the actual vaccine names with interactions
    vaccine_interactions_to_display = []
    for i, row in vaccine_side_effects_df.iterrows():
        # Extract vaccine and substance names
        names = row['drug_concept_name'].split(' + ')
        vaccine_name = next((n for n in names if n in vaccine_list), None)
        substance_name = next((n for n in names if n not in vaccine_list), None)
        if vaccine_name and substance_name:
            # vaccine_interactions_to_display[vaccine_name].append(f'+ {substance_name}: {row["event_concept_name"]}')
            vaccine_interactions_to_display.append({"Vaccine": vaccine_name, "Interaction Drug": substance_name, "Side effect due to interaction": row["event_concept_name"]})

    # st.write(vaccine_interactions_to_display)
    df = pd.DataFrame(vaccine_interactions_to_display)
    df = df.sort_values(by=['Vaccine', 'Interaction Drug'])

    if not vaccine_side_effects_df.empty:
        st.dataframe(df, hide_index=True)
    else:
        st.write("No interactions found.")