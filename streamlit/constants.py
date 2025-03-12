
# Search Constants 
LIFESTYLE_FACTORS = ['Alcoholic beverage', 'cranberry', 'grapefruit', 'peppermint'] #, 'eicosapentaenoic acid', 'magnesium']

# Data Frame Columns
DDI_COLUMNS = [
    'drug_a_concept_name', 
    'drug_b_concept_name', 
    'event_concept_name', 
    'severity_bnf',
    'severity_ansm', 
    'severity_code',
    'evidence',
    'description'
]
SIDE_EFFECT_COLUMNS = [
    'drug_concept_name', 
    'event_concept_name', 
    'frequency', 
    'source'
]
NAME_EVENT_COLUMNS = [
    'drug_concept_name', 
    'event_concept_name'
]


#  DDI Severity Colours 
severity_colour_map = {1: "yellow", 2: "#FFA500", 3: "#ff6f00", 4: "#FF0000"}  # Gold, Orange, OrangeRed, Red

#  Side Effect Table Values
frequency_values = {
    'common or very common': 4,
    'uncommon': 3,
    'rare or very rare': 2,
    'frequency not known': 1,
    # None: 0,
    'unknown': 1,
    'Not reported (Interaction Effect)': 4
}

#  Side Effect Table Colours
frequency_colour_map = {
    '4': '#28a745',  # green
    '3': '#ffa500',  # orange
    '2': '#dc3545',  # red
    '1': '#6c757d',  # grey
    '*': '#0000FF',  # blue
    '-': '#e9ecef',   # light grey
    }

#  Vaccine List
vaccine_list = [

"Yellow Fever Vaccine",
"varicella-zoster virus vaccine live (Oka-Merck) strain",
"BCG Vaccine",
"ROTAVIRUS VACCINE, LIVE",
"Vibrio cholerae live attenuated",
"dengue virus live antigen, CYD serotype 4",
"rubella virus vaccine live (Wistar RA 27-3 strain)",
"Rabies vaccine, inactivated",
"Salmonella typhi Ty21a live antigen",
"influenza B virus antigen",
"yellow fever virus strain 17D-204 live antigen",
"cytomegalovirus immune globulin"

]


patient_ids_temp = [249,250,251,252,253,255,256,257,260,262,263,
                    265,266,267,268,269,270,665,667,668,669,671,
                    672,673,674,676,677,678,679,680,682,685,688,
                    689,690,695,697,698,700,702,703,705,707,708,
                    709,710,711,712,713,715,716,717,718,719,720,
                    721,722,727,728,729,730,731,732,735,736,738,
                    741,743,745,746,747]