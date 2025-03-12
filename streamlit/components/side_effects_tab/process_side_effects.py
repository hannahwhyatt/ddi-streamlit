import pandas as pd
from collections import Counter
from constants import frequency_values, frequency_colour_map

def process_side_effects(df):
    """ Collate side effects data into table overview """   
    # Calculate frequency scores
    frequency_scores = df.copy()
    frequency_scores['freq_value'] = frequency_scores['frequency'].map(frequency_values)
    
    # Create pivot table with numerical values
    pivot_df = frequency_scores.pivot_table(
        values='freq_value',
        index='event_concept_name',
        columns='drug_concept_name',
        aggfunc='max'
    )
    
    # Calculate and add total frequency score column
    total_frequencies = frequency_scores.groupby('event_concept_name')['freq_value'].sum()
    pivot_df.insert(0, 'Total Frequency Score', total_frequencies)
    
    # Sort by total frequency score
    pivot_df = pivot_df.sort_values('Total Frequency Score', ascending=False)
    
    # Convert numerical values to strings with custom mapping
    for col in pivot_df.columns:
        pivot_df[col] = pivot_df[col].apply(lambda x: str(int(x)) if pd.notnull(x) and x != '-' else '-')
        if ' + ' in col:
            pivot_df[col] = pivot_df[col].apply(lambda x: '*' if pd.notnull(x) and x != '-' else '-')
    
    # Reorder columns to show interaction columns first
    columns = list(pivot_df.columns)
    interaction_cols = [col for col in columns if '+' in str(col)]
    other_cols = [col for col in columns if '+' not in str(col)]
    new_column_order = ['Total Frequency Score'] + interaction_cols + other_cols[1:]  # Skip 'Total Frequency Score' in other_cols
    pivot_df = pivot_df[new_column_order]
    
    pivot_df = pivot_df.rename_axis('Side Effect')
    return pivot_df

def process_side_effects_hlt(df):
        # Calculate frequency scores
    frequency_scores = df.copy()
    frequency_scores['freq_value'] = frequency_scores['frequency'].map(frequency_values)

    def custom_agg_function(values):
        counts = []
        set_of_values = set(values)
        if len(set_of_values) > 0:
            counter = Counter(values)
            for v in set_of_values:
                if counter[v] > 0:
                    counts.append(f'{int(v)} (x{counter[v]})')
        return ', '.join(counts)
    # Replace null or None ancestors with event_concept_name
    frequency_scores['ancestor'] = frequency_scores['ancestor'].where(frequency_scores['ancestor'].notnull(), frequency_scores['event_concept_name'])

    # Create pivot table with numerical values
    pivot_df = frequency_scores.pivot_table(
        values='freq_value',
        index='ancestor',
        columns='drug_concept_name',
        aggfunc=custom_agg_function,
    )
        # Calculate and add total frequency score column
    total_frequencies = frequency_scores.groupby('ancestor')['freq_value'].sum()
    pivot_df.insert(0, 'Total Frequency Score', total_frequencies)

    # Sort by total frequency score
    pivot_df = pivot_df.sort_values('Total Frequency Score', ascending=False)
    
    # # Convert numerical values to strings with custom mapping
    for col in pivot_df.columns:
        pivot_df[col] = pivot_df[col].apply(lambda x: x if pd.notnull(x) and x != '-' else '-')
        if ' + ' in col:
            pivot_df[col] = pivot_df[col].apply(lambda x: '*' if pd.notnull(x) and x != '-' else '-')
    
    # Reorder columns to show interaction columns first
    columns = list(pivot_df.columns)
    interaction_cols = [col for col in columns if '+' in str(col)]
    other_cols = [col for col in columns if '+' not in str(col)]
    new_column_order = ['Total Frequency Score'] + interaction_cols + other_cols[1:]  # Skip 'Total Frequency Score' in other_cols
    pivot_df = pivot_df[new_column_order]
    
    pivot_df = pivot_df.rename_axis('Side Effect')    
    return pivot_df