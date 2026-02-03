"""
Sample Discharge Summaries for ICD-10 Prediction
Based on actual code frequencies from training data
"""

# Top 10 most frequent codes from training:
# Z91.81 (Fall history) - 368
# E78.5 (Hyperlipidemia) - 283
# M10.33 (Gout) - 207
# E03.9 (Hypothyroidism) - 193
# I13.0 (Hypertensive CKD) - 187
# M17.00 (Knee OA) - 174
# K21.9 (GERD) - 173
# I25.10 (CAD) - 166
# Z55.6 (Illiteracy) - 161
# N18.2 (CKD Stage 2) - 153

DISCHARGE_SUMMARIES = {
    1: {
        "title": "Elderly Fall with History of Falls",
        "text": """PATIENT: 78-year-old female
ADMISSION DATE: 01/15/2026

CHIEF COMPLAINT: Fall at home

HISTORY OF PRESENT ILLNESS:
Patient presented to ED after fall at home. She has history of falls in the past 6 months. Patient was walking to bathroom when she lost balance and fell. No loss of consciousness. Patient complains of muscle weakness in lower extremities.

PAST MEDICAL HISTORY:
- History of falling
- Unsteadiness on feet
- Muscle weakness

PHYSICAL EXAMINATION:
Vital signs stable. Patient demonstrates unsteady gait. Berg Balance Scale score 32/56 indicating high fall risk.

DISCHARGE DIAGNOSIS:
1. History of falling (Z91.81)
2. Unsteadiness on feet (R26.81)
3. Muscle weakness (M62.81)"""
    },
    
    2: {
        "title": "Hyperlipidemia and Gout",
        "text": """PATIENT: 65-year-old male
ADMISSION DATE: 01/20/2026

CHIEF COMPLAINT: Joint pain and elevated cholesterol

HISTORY OF PRESENT ILLNESS:
Patient with longstanding hyperlipidemia now presenting with acute gout flare in left foot. Patient reports severe pain in great toe. Labs show elevated uric acid and cholesterol.

PAST MEDICAL HISTORY:
- Hyperlipidemia, unspecified
- Gout, left ankle and foot
- History of recurrent gout

MEDICATIONS:
- Atorvastatin 40mg daily
- Allopurinol 300mg daily

DISCHARGE DIAGNOSIS:
1. Hyperlipidemia, unspecified (E78.5)
2. Gout, left ankle and foot (M10.33)
3. Chronic pain syndrome (G89.29)"""
    },
    
    3: {
        "title": "Hypothyroidism with CKD",
        "text": """PATIENT: 72-year-old female  
ADMISSION DATE: 02/01/2026

CHIEF COMPLAINT: Fatigue and elevated creatinine

HISTORY OF PRESENT ILLNESS:
Patient with known hypothyroidism presents with worsening fatigue. Labs reveal TSH elevated at 8.5. Creatinine 1.8 consistent with chronic kidney disease stage 2.

PAST MEDICAL HISTORY:
- Hypothyroidism, unspecified
- Chronic kidney disease, stage 2
- Fatigue

MEDICATIONS:
- Levothyroxine 125mcg daily

DISCHARGE DIAGNOSIS:
1. Hypothyroidism, unspecified (E03.9)
2. Chronic kidney disease, stage 2 (N18.2)
3. Muscle weakness (M62.81)"""
    },
    
    4: {
        "title": "Hypertensive CKD with CAD",
        "text": """PATIENT: 68-year-old male
ADMISSION DATE: 02/05/2026

CHIEF COMPLAINT: Chest pain and shortness of breath

HISTORY OF PRESENT ILLNESS:
Patient with hypertensive chronic kidney disease and coronary artery disease presents with exertional chest pain. EKG shows old inferior MI. Creatinine 2.1. Blood pressure 165/95.

PAST MEDICAL HISTORY:
- Hypertensive chronic kidney disease with stage 1-4 CKD
- Coronary atherosclerosis of native coronary artery
- Essential hypertension
- Chronic kidney disease stage 3

MEDICATIONS:
- Lisinopril 20mg daily
- Metoprolol 50mg BID
- Atorvastatin 80mg daily

DISCHARGE DIAGNOSIS:
1. Hypertensive CKD with stage 1-4 CKD (I13.0)
2. Coronary artery disease (I25.10)
3. Essential hypertension (I10)
4. Chronic kidney disease stage 3 (N18.31)"""
    },
    
    5: {
        "title": "Knee Osteoarthritis Bilateral",
        "text": """PATIENT: 70-year-old female
ADMISSION DATE: 02/10/2026

CHIEF COMPLAINT: Bilateral knee pain

HISTORY OF PRESENT ILLNESS:
Patient with long-standing osteoarthritis of bilateral knees presents for pain management. Pain rated 7/10, worse with ambulation. X-rays show severe joint space narrowing bilaterally.

PAST MEDICAL HISTORY:
- Primary osteoarthritis, unspecified knee
- Chronic pain syndrome
- Difficulty walking

PHYSICAL EXAMINATION:
Bilateral knee crepitus noted. Limited range of motion. Tenderness to palpation bilateral medial joint lines.

DISCHARGE DIAGNOSIS:
1. Primary osteoarthritis, unspecified knee (M17.00)
2. Chronic pain syndrome (G89.29)
3. Difficulty in walking (R26.2)"""
    },
    
    6: {
        "title": "GERD with Sleep Apnea",
        "text": """PATIENT: 58-year-old male
ADMISSION DATE: 02/15/2026

CHIEF COMPLAINT: Heartburn and snoring

HISTORY OF PRESENT ILLNESS:
Patient reports chronic heartburn worse at night. Also complains of daytime sleepiness. Wife reports loud snoring. Sleep study confirms obstructive sleep apnea.

PAST MEDICAL HISTORY:
- Gastro-esophageal reflux disease without esophagitis
- Obstructive sleep apnea, unspecified
- Obesity

MEDICATIONS:
- Omeprazole 40mg daily
- CPAP at night

DISCHARGE DIAGNOSIS:
1. GERD without esophagitis (K21.9)
2. Obstructive sleep apnea (G47.00)
3. Obesity (E66.01)"""
    },
    
    7: {
        "title": "CHF with Atrial Fibrillation",
        "text": """PATIENT: 75-year-old male
ADMISSION DATE: 02/20/2026

CHIEF COMPLAINT: Shortness of breath and leg swelling

HISTORY OF PRESENT ILLNESS:
Patient with history of heart failure presents with acute decompensation. Patient reports orthopnea and paroxysmal nocturnal dyspnea. EKG shows atrial fibrillation. BNP elevated at 1500.

PAST MEDICAL HISTORY:
- Acute on chronic combined systolic and diastolic heart failure
- Atrial fibrillation
- Hypertension
- Coronary artery disease

MEDICATIONS:
- Furosemide 40mg BID
- Metoprolol 25mg BID
- Warfarin 5mg daily
- Lisinopril 10mg daily

DISCHARGE DIAGNOSIS:
1. Acute on chronic heart failure (I50.32)
2. Atrial fibrillation (I48.0)
3. Essential hypertension (I10)
4. Coronary artery disease (I25.10)"""
    },
    
    8: {
        "title": "Type 2 Diabetes with Neuropathy",
        "text": """PATIENT: 62-year-old female
ADMISSION DATE: 02/25/2026

CHIEF COMPLAINT: Foot pain and numbness

HISTORY OF PRESENT ILLNESS:
Patient with poorly controlled type 2 diabetes mellitus presents with diabetic neuropathy. HbA1c 9.2%. Patient reports burning pain in feet bilaterally. Monofilament testing shows decreased sensation.

PAST MEDICAL HISTORY:
- Type 2 diabetes mellitus with diabetic neuropathy
- Peripheral neuropathy, unspecified
- Chronic pain syndrome

MEDICATIONS:
- Metformin 1000mg BID
- Gabapentin 300mg TID

DISCHARGE DIAGNOSIS:
1. Type 2 DM with diabetic neuropathy (E11.42)
2. Peripheral neuropathy (G62.9)
3. Chronic pain syndrome (G89.29)"""
    },
    
    9: {
        "title": "Dementia with Behavioral Disturbance",
        "text": """PATIENT: 82-year-old male
ADMISSION DATE: 03/01/2026

CHIEF COMPLAINT: Confusion and agitation

HISTORY OF PRESENT ILLNESS:
Patient with Alzheimer's dementia presents with increased confusion and behavioral disturbances. Family reports patient wandering at night and becoming agitated. MMSE score 12/30.

PAST MEDICAL HISTORY:
- Alzheimer's disease with early onset
- Dementia with behavioral disturbance
- Cognitive decline

MEDICATIONS:
- Donepezil 10mg daily
- Quetiapine 25mg BID

DISCHARGE DIAGNOSIS:
1. Alzheimer's disease with early onset (G30.1)
2. Dementia with behavioral disturbance (F02.B3)
3. Cognitive decline (R41.841)"""
    },
    
    10: {
        "title": "COPD with Acute Exacerbation",
        "text": """PATIENT: 68-year-old male
ADMISSION DATE: 03/05/2026

CHIEF COMPLAINT: Shortness of breath and cough

HISTORY OF PRESENT ILLNESS:
Patient with chronic obstructive pulmonary disease presents with acute exacerbation. Increased dyspnea, productive cough with yellow sputum. Chest X-ray shows hyperinflation. Requires oxygen at 3L NC.

PAST MEDICAL HISTORY:
- Chronic obstructive pulmonary disease, unspecified
- History of tobacco use
- Respiratory failure

MEDICATIONS:
- Albuterol inhaler PRN
- Spiriva 18mcg daily
- Prednisone 40mg daily

DISCHARGE DIAGNOSIS:
1. COPD, unspecified (J44.9)
2. Acute respiratory failure (J96.01)
3. History of tobacco use (Z87.891)"""
    }
}

def get_case(case_number):
    """Get a specific case by number (1-10)"""
    return DISCHARGE_SUMMARIES.get(case_number, DISCHARGE_SUMMARIES[1])

def get_case_titles():
    """Get list of all case titles"""
    return [DISCHARGE_SUMMARIES[i]["title"] for i in range(1, 11)]
