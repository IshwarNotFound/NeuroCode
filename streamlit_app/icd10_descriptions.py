"""
ICD-10 Code Descriptions and Chapter Colors
Provides human-readable descriptions for common ICD-10 codes
"""

# Chapter color mapping for visual display
ICD10_CHAPTER_COLORS = {
    'A': '#FF6B6B',  # Infectious diseases - Red
    'B': '#FF6B6B',  # Infectious diseases - Red
    'C': '#9B59B6',  # Neoplasms - Purple
    'D': '#9B59B6',  # Neoplasms/Blood - Purple
    'E': '#F39C12',  # Endocrine/Metabolic - Orange
    'F': '#3498DB',  # Mental disorders - Blue
    'G': '#1ABC9C',  # Nervous system - Teal
    'H': '#E91E63',  # Eye/Ear - Pink
    'I': '#E74C3C',  # Circulatory - Dark Red
    'J': '#00BCD4',  # Respiratory - Cyan
    'K': '#8BC34A',  # Digestive - Green
    'L': '#FF9800',  # Skin - Orange
    'M': '#673AB7',  # Musculoskeletal - Deep Purple
    'N': '#009688',  # Genitourinary - Teal
    'O': '#E91E63',  # Pregnancy - Pink
    'P': '#FFEB3B',  # Perinatal - Yellow
    'Q': '#795548',  # Congenital - Brown
    'R': '#607D8B',  # Symptoms/Signs - Gray Blue
    'S': '#FF5722',  # Injury - Deep Orange
    'T': '#FF5722',  # Injury/Poisoning - Deep Orange
    'V': '#9E9E9E',  # External causes - Gray
    'W': '#9E9E9E',  # External causes - Gray
    'X': '#9E9E9E',  # External causes - Gray
    'Y': '#9E9E9E',  # External causes - Gray
    'Z': '#4CAF50',  # Factors influencing health - Green
}

# Chapter names
ICD10_CHAPTERS = {
    'A': 'Infectious Diseases',
    'B': 'Infectious Diseases',
    'C': 'Neoplasms',
    'D': 'Blood Diseases',
    'E': 'Endocrine & Metabolic',
    'F': 'Mental Disorders',
    'G': 'Nervous System',
    'H': 'Eye & Ear',
    'I': 'Circulatory System',
    'J': 'Respiratory System',
    'K': 'Digestive System',
    'L': 'Skin Diseases',
    'M': 'Musculoskeletal',
    'N': 'Genitourinary',
    'O': 'Pregnancy',
    'P': 'Perinatal',
    'Q': 'Congenital',
    'R': 'Symptoms & Signs',
    'S': 'Injury',
    'T': 'Injury & Poisoning',
    'V': 'External Causes',
    'W': 'External Causes',
    'X': 'External Causes',
    'Y': 'External Causes',
    'Z': 'Health Factors',
}

# Common ICD-10 code descriptions (expanded list)
ICD10_DESCRIPTIONS = {
    # Circulatory System (I)
    'I10': 'Essential (primary) hypertension',
    'I11.0': 'Hypertensive heart disease with heart failure',
    'I11.9': 'Hypertensive heart disease without heart failure',
    'I12.9': 'Hypertensive chronic kidney disease',
    'I13.0': 'Hypertensive heart and chronic kidney disease with heart failure',
    'I13.10': 'Hypertensive heart and CKD without heart failure',
    'I21.0': 'ST elevation MI of anterior wall',
    'I21.3': 'ST elevation MI of unspecified site',
    'I25.10': 'Atherosclerotic heart disease of native coronary artery',
    'I25.2': 'Old myocardial infarction',
    'I25.5': 'Ischemic cardiomyopathy',
    'I48.0': 'Paroxysmal atrial fibrillation',
    'I48.1': 'Persistent atrial fibrillation',
    'I48.2': 'Chronic atrial fibrillation',
    'I48.91': 'Unspecified atrial fibrillation',
    'I50.1': 'Left ventricular failure',
    'I50.20': 'Unspecified systolic heart failure',
    'I50.22': 'Chronic systolic heart failure',
    'I50.30': 'Unspecified diastolic heart failure',
    'I50.32': 'Chronic diastolic heart failure',
    'I50.9': 'Heart failure, unspecified',
    'I63.9': 'Cerebral infarction, unspecified',
    'I69.354': 'Hemiplegia following cerebral infarction',
    'I69.391': 'Dysphagia following cerebral infarction',
    
    # Endocrine & Metabolic (E)
    'E03.9': 'Hypothyroidism, unspecified',
    'E05.90': 'Hyperthyroidism, unspecified',
    'E10.9': 'Type 1 diabetes mellitus without complications',
    'E11.9': 'Type 2 diabetes mellitus without complications',
    'E11.21': 'Type 2 DM with diabetic nephropathy',
    'E11.22': 'Type 2 DM with diabetic chronic kidney disease',
    'E11.40': 'Type 2 DM with diabetic neuropathy',
    'E11.42': 'Type 2 DM with diabetic polyneuropathy',
    'E11.65': 'Type 2 DM with hyperglycemia',
    'E66.01': 'Morbid obesity due to excess calories',
    'E66.9': 'Obesity, unspecified',
    'E78.0': 'Pure hypercholesterolemia',
    'E78.1': 'Pure hyperglyceridemia',
    'E78.2': 'Mixed hyperlipidemia',
    'E78.5': 'Hyperlipidemia, unspecified',
    'E87.1': 'Hypo-osmolality and hyponatremia',
    'E87.6': 'Hypokalemia',
    
    # Musculoskeletal (M)
    'M10.9': 'Gout, unspecified',
    'M10.33': 'Gout of wrist',
    'M17.0': 'Bilateral primary osteoarthritis of knee',
    'M17.00': 'Bilateral primary osteoarthritis of knee',
    'M17.10': 'Unilateral primary osteoarthritis of knee',
    'M17.11': 'Primary osteoarthritis, right knee',
    'M17.12': 'Primary osteoarthritis, left knee',
    'M17.40': 'Unilateral secondary osteoarthritis of knee',
    'M19.90': 'Unspecified osteoarthritis, unspecified site',
    'M25.561': 'Pain in right knee',
    'M25.562': 'Pain in left knee',
    'M54.5': 'Low back pain',
    'M54.50': 'Low back pain, unspecified site',
    'M62.81': 'Muscle weakness (generalized)',
    'M79.3': 'Panniculitis, unspecified',
    'M81.0': 'Age-related osteoporosis without current pathological fracture',
    
    # Respiratory (J)
    'J06.9': 'Acute upper respiratory infection, unspecified',
    'J18.9': 'Pneumonia, unspecified organism',
    'J20.9': 'Acute bronchitis, unspecified',
    'J43.9': 'Emphysema, unspecified',
    'J44.0': 'COPD with acute lower respiratory infection',
    'J44.1': 'COPD with acute exacerbation',
    'J44.9': 'COPD, unspecified',
    'J45.20': 'Mild intermittent asthma, uncomplicated',
    'J45.30': 'Mild persistent asthma, uncomplicated',
    'J45.40': 'Moderate persistent asthma, uncomplicated',
    'J45.50': 'Severe persistent asthma, uncomplicated',
    'J96.0': 'Acute respiratory failure',
    'J96.1': 'Chronic respiratory failure',
    
    # Nervous System (G)
    'G20': "Parkinson's disease",
    'G30.9': "Alzheimer's disease, unspecified",
    'G31.1': 'Senile degeneration of brain',
    'G35': 'Multiple sclerosis',
    'G40.909': 'Epilepsy, unspecified',
    'G43.909': 'Migraine, unspecified',
    'G47.33': 'Obstructive sleep apnea',
    'G62.9': 'Polyneuropathy, unspecified',
    'G89.29': 'Other chronic pain',
    
    # Genitourinary (N)
    'N17.9': 'Acute kidney failure, unspecified',
    'N18.1': 'Chronic kidney disease, stage 1',
    'N18.2': 'Chronic kidney disease, stage 2 (mild)',
    'N18.3': 'Chronic kidney disease, stage 3 (moderate)',
    'N18.30': 'CKD stage 3 unspecified',
    'N18.31': 'CKD stage 3a',
    'N18.32': 'CKD stage 3b',
    'N18.4': 'Chronic kidney disease, stage 4 (severe)',
    'N18.5': 'Chronic kidney disease, stage 5',
    'N18.6': 'End stage renal disease',
    'N18.9': 'Chronic kidney disease, unspecified',
    'N39.0': 'Urinary tract infection, site not specified',
    'N40.0': 'Benign prostatic hyperplasia without LUTS',
    'N40.1': 'Benign prostatic hyperplasia with LUTS',
    
    # Symptoms & Signs (R)
    'R00.0': 'Tachycardia, unspecified',
    'R00.1': 'Bradycardia, unspecified',
    'R06.02': 'Shortness of breath',
    'R07.9': 'Chest pain, unspecified',
    'R13.10': 'Dysphagia, unspecified',
    'R13.12': 'Dysphagia, oropharyngeal phase',
    'R26.0': 'Ataxic gait',
    'R26.2': 'Difficulty in walking',
    'R26.81': 'Unsteadiness on feet',
    'R26.89': 'Other abnormalities of gait and mobility',
    'R41.0': 'Disorientation, unspecified',
    'R41.82': 'Altered mental status, unspecified',
    'R41.841': 'Cognitive communication deficit',
    'R50.9': 'Fever, unspecified',
    'R53.1': 'Weakness',
    'R53.81': 'Other malaise',
    'R53.83': 'Other fatigue',
    'R55': 'Syncope and collapse',
    'R56.9': 'Unspecified convulsions',
    
    # Health Factors (Z)
    'Z23': 'Encounter for immunization',
    'Z66': 'Do not resuscitate',
    'Z74.01': 'Reduced mobility',
    'Z87.891': 'Personal history of nicotine dependence',
    'Z91.81': 'History of falling',
    'Z95.1': 'Presence of aortocoronary bypass graft',
    'Z95.5': 'Presence of coronary angioplasty implant',
    'Z96.641': 'Presence of right artificial hip joint',
    'Z96.642': 'Presence of left artificial hip joint',
    'Z96.651': 'Presence of right artificial knee joint',
    'Z96.652': 'Presence of left artificial knee joint',
    
    # Infectious Diseases (A, B)
    'A41.9': 'Sepsis, unspecified organism',
    'A49.9': 'Bacterial infection, unspecified',
    'B34.9': 'Viral infection, unspecified',
    'B95.61': 'MRSA as cause of diseases',
    'B96.20': 'Unspecified E. coli as cause of disease',
    
    # Blood Diseases (D)
    'D50.9': 'Iron deficiency anemia, unspecified',
    'D64.9': 'Anemia, unspecified',
    'D69.6': 'Thrombocytopenia, unspecified',
    
    # Mental Disorders (F)
    'F03.90': 'Unspecified dementia without behavioral disturbance',
    'F10.20': 'Alcohol dependence, uncomplicated',
    'F17.210': 'Nicotine dependence, cigarettes, uncomplicated',
    'F32.9': 'Major depressive disorder, single episode, unspecified',
    'F33.0': 'Major depressive disorder, recurrent, mild',
    'F41.1': 'Generalized anxiety disorder',
    'F41.9': 'Anxiety disorder, unspecified',
    
    # Digestive (K)
    'K21.0': 'GERD with esophagitis',
    'K21.9': 'GERD without esophagitis',
    'K25.9': 'Gastric ulcer, unspecified',
    'K29.70': 'Gastritis, unspecified',
    'K50.90': "Crohn's disease, unspecified",
    'K51.90': 'Ulcerative colitis, unspecified',
    'K59.00': 'Constipation, unspecified',
    'K76.0': 'Fatty liver disease',
}


def get_code_description(code: str) -> str:
    """Get the description for an ICD-10 code."""
    code = code.upper().strip()
    return ICD10_DESCRIPTIONS.get(code, f"ICD-10 Code: {code}")


def get_code_color(code: str) -> str:
    """Get the chapter color for an ICD-10 code."""
    if not code:
        return '#808080'  # Gray for unknown
    letter = code[0].upper()
    return ICD10_CHAPTER_COLORS.get(letter, '#808080')


def get_chapter_name(code: str) -> str:
    """Get the chapter name for an ICD-10 code."""
    if not code:
        return 'Unknown'
    letter = code[0].upper()
    return ICD10_CHAPTERS.get(letter, 'Unknown')
