"""
Sample Discharge Summaries for ICD-10 Prediction
Based on actual code frequencies from training data

DISCLAIMER: All patient cases below are SYNTHETIC and do not represent
real patients. No Protected Health Information (PHI) is contained herein.
These cases are generated for demonstration and testing purposes only.
"""

# Safety flag for compliance checks
SYNTHETIC_DATA = True

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
1. History of falling
2. Unsteadiness on feet
3. Muscle weakness"""
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
1. Hyperlipidemia, unspecified
2. Gout, left ankle and foot
3. Chronic pain syndrome"""
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
1. Hypothyroidism, unspecified
2. Chronic kidney disease, stage 2
3. Muscle weakness"""
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
1. Hypertensive CKD with stage 1-4 CKD
2. Coronary artery disease
3. Essential hypertension
4. Chronic kidney disease stage 3"""
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
1. Primary osteoarthritis, unspecified knee
2. Chronic pain syndrome
3. Difficulty in walking"""
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
1. GERD without esophagitis
2. Obstructive sleep apnea
3. Obesity"""
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
1. Acute on chronic heart failure
2. Atrial fibrillation
3. Essential hypertension
4. Coronary artery disease"""
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
1. Type 2 DM with diabetic neuropathy
2. Peripheral neuropathy
3. Chronic pain syndrome"""
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
1. Alzheimer's disease with early onset
2. Dementia with behavioral disturbance
3. Cognitive decline"""
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
1. COPD, unspecified
2. Acute respiratory failure
3. History of tobacco use"""
    },
    
    11: {
        "title": "Type 2 Diabetes with Kidney Disease",
        "text": """PATIENT: 59-year-old female
ADMISSION DATE: 03/10/2026

CHIEF COMPLAINT: Elevated blood sugar and swelling

HISTORY OF PRESENT ILLNESS:
Patient with type 2 diabetes mellitus presents with hyperglycemia and peripheral edema. Blood glucose 285, HbA1c 10.1%. Creatinine elevated at 2.4 indicating diabetic chronic kidney disease. Patient also has retinopathy requiring ophthalmology follow-up.

PAST MEDICAL HISTORY:
- Type 2 diabetes with diabetic chronic kidney disease
- Diabetic retinopathy
- Hyperlipidemia
- Essential hypertension

MEDICATIONS:
- Insulin glargine 40 units daily
- Lisinopril 40mg daily
- Metformin held due to renal function

DISCHARGE DIAGNOSIS:
1. Type 2 DM with diabetic CKD
2. Chronic kidney disease stage 3
3. Essential hypertension
4. Hyperlipidemia"""
    },
    
    12: {
        "title": "Atherosclerosis with Peripheral Vascular Disease",
        "text": """PATIENT: 71-year-old male
ADMISSION DATE: 03/15/2026

CHIEF COMPLAINT: Leg pain with walking

HISTORY OF PRESENT ILLNESS:
Patient with generalized atherosclerosis presents with claudication. Reports leg pain after walking one block. ABI 0.65 bilateral. Has history of coronary artery disease and hypertensive heart disease.

PAST MEDICAL HISTORY:
- Atherosclerosis of aorta
- Peripheral vascular disease, unspecified
- Coronary artery disease
- Hypertensive heart disease

MEDICATIONS:
- Aspirin 81mg daily
- Clopidogrel 75mg daily
- Atorvastatin 80mg daily

DISCHARGE DIAGNOSIS:
1. Atherosclerosis of aorta
2. Peripheral vascular disease
3. Coronary artery disease
4. Hypertensive heart disease"""
    },
    
    13: {
        "title": "Osteoporosis with Fracture Risk",
        "text": """PATIENT: 76-year-old female
ADMISSION DATE: 03/20/2026

CHIEF COMPLAINT: Back pain and bone loss

HISTORY OF PRESENT ILLNESS:
Patient with age-related osteoporosis without current pathological fracture presents for evaluation. DEXA scan shows T-score -3.2 at lumbar spine. Patient has history of falls and is at high risk for fracture.

PAST MEDICAL HISTORY:
- Age-related osteoporosis without current pathological fracture
- History of falling
- Vitamin D deficiency
- Muscle weakness

MEDICATIONS:
- Alendronate 70mg weekly
- Calcium carbonate 1200mg daily
- Vitamin D3 2000 units daily

DISCHARGE DIAGNOSIS:
1. Osteoporosis without fracture
2. History of falling
3. Vitamin D deficiency
4. Muscle weakness, generalized"""
    },
    
    14: {
        "title": "Depression with Anxiety",
        "text": """PATIENT: 45-year-old female
ADMISSION DATE: 03/25/2026

CHIEF COMPLAINT: Sadness and worry

HISTORY OF PRESENT ILLNESS:
Patient with major depressive disorder and generalized anxiety presents with worsening symptoms. Reports poor sleep, decreased appetite, difficulty concentrating. PHQ-9 score 18, GAD-7 score 14.

PAST MEDICAL HISTORY:
- Major depressive disorder, single episode, in partial remission
- Generalized anxiety disorder
- Insomnia
- Hypothyroidism

MEDICATIONS:
- Sertraline 100mg daily
- Hydroxyzine 25mg PRN
- Levothyroxine 75mcg daily

DISCHARGE DIAGNOSIS:
1. Major depressive disorder
2. Generalized anxiety disorder
3. Insomnia
4. Hypothyroidism"""
    },
    
    15: {
        "title": "Heart Failure with CKD and Anemia",
        "text": """PATIENT: 74-year-old male
ADMISSION DATE: 03/30/2026

CHIEF COMPLAINT: Fatigue and swelling

HISTORY OF PRESENT ILLNESS:
Patient with chronic heart failure and chronic kidney disease presents with decompensation. BNP 2200, creatinine 3.1, hemoglobin 9.2. Has anemia of chronic kidney disease. Requires IV diuretics.

PAST MEDICAL HISTORY:
- Chronic systolic heart failure
- Chronic kidney disease stage 4
- Anemia in CKD
- Atrial fibrillation
- Type 2 diabetes

MEDICATIONS:
- Furosemide 80mg BID
- Carvedilol 12.5mg BID
- Epoetin alfa weekly
- Insulin

DISCHARGE DIAGNOSIS:
1. Heart failure, unspecified
2. Chronic kidney disease stage 4
3. Anemia in CKD
4. Atrial fibrillation
5. Type 2 diabetes"""
    },
    
    16: {
        "title": "Obstructive Sleep Apnea with Obesity",
        "text": """PATIENT: 52-year-old male
ADMISSION DATE: 04/05/2026

CHIEF COMPLAINT: Excessive daytime sleepiness and snoring

HISTORY OF PRESENT ILLNESS:
Patient referred for evaluation of suspected obstructive sleep apnea. Reports loud snoring, witnessed apneas, morning headaches, and excessive daytime sleepiness. Epworth Sleepiness Scale score 16. Sleep study confirms severe obstructive sleep apnea with AHI of 45.

PAST MEDICAL HISTORY:
- Obstructive sleep apnea
- Morbid obesity
- Essential hypertension
- Gastroesophageal reflux disease

MEDICATIONS:
- CPAP therapy initiated
- Lisinopril 20mg daily
- Omeprazole 20mg daily

DISCHARGE DIAGNOSIS:
1. Obstructive sleep apnea
2. Morbid obesity
3. Essential hypertension
4. GERD"""
    },
    
    17: {
        "title": "Chronic Low Back Pain with Sciatica",
        "text": """PATIENT: 55-year-old female
ADMISSION DATE: 04/10/2026

CHIEF COMPLAINT: Chronic back pain radiating to leg

HISTORY OF PRESENT ILLNESS:
Patient with long-standing low back pain now presenting with radiculopathy. Pain radiates from lower back to left leg. MRI shows L4-L5 disc herniation with nerve impingement. Pain rated 8/10, worse with sitting.

PAST MEDICAL HISTORY:
- Low back pain, unspecified
- Lumbar radiculopathy
- Difficulty walking
- History of falls

MEDICATIONS:
- Gabapentin 300mg TID
- Meloxicam 15mg daily
- Physical therapy referral

DISCHARGE DIAGNOSIS:
1. Low back pain, unspecified
2. Lumbar radiculopathy
3. Difficulty in walking
4. History of falling"""
    },
    
    18: {
        "title": "Chronic Constipation with IBS",
        "text": """PATIENT: 48-year-old female
ADMISSION DATE: 04/15/2026

CHIEF COMPLAINT: Chronic constipation and abdominal discomfort

HISTORY OF PRESENT ILLNESS:
Patient with chronic constipation and irritable bowel syndrome presents with worsening symptoms. Reports fewer than 3 bowel movements per week, straining, and abdominal bloating. Has tried multiple over-the-counter laxatives with limited relief.

PAST MEDICAL HISTORY:
- Constipation, unspecified
- Irritable bowel syndrome
- Anxiety disorder
- Hypothyroidism

MEDICATIONS:
- Polyethylene glycol daily
- Linaclotide 145mcg daily
- Sertraline 50mg daily
- Levothyroxine 100mcg daily

DISCHARGE DIAGNOSIS:
1. Constipation, unspecified
2. Irritable bowel syndrome
3. Generalized anxiety disorder
4. Hypothyroidism"""
    },
    
    19: {
        "title": "Benign Prostatic Hyperplasia",
        "text": """PATIENT: 68-year-old male
ADMISSION DATE: 04/20/2026

CHIEF COMPLAINT: Urinary difficulties

HISTORY OF PRESENT ILLNESS:
Patient with benign prostatic hyperplasia presents with worsening lower urinary tract symptoms. Reports urinary frequency, nocturia (4 times per night), weak stream, and incomplete emptying. Post-void residual 150mL. PSA 2.5.

PAST MEDICAL HISTORY:
- Benign prostatic hyperplasia without lower urinary tract symptoms
- Urinary frequency
- Nocturia
- Essential hypertension

MEDICATIONS:
- Tamsulosin 0.4mg daily
- Finasteride 5mg daily
- Amlodipine 5mg daily

DISCHARGE DIAGNOSIS:
1. BPH without LUTS
2. Urinary frequency
3. Essential hypertension
4. Nocturia"""
    },
    
    20: {
        "title": "Cerebrovascular Disease with Hemiparesis",
        "text": """PATIENT: 72-year-old male
ADMISSION DATE: 04/25/2026

CHIEF COMPLAINT: Weakness on left side

HISTORY OF PRESENT ILLNESS:
Patient with history of stroke presents with residual left-sided weakness. CT shows old right MCA infarct. Patient in rehabilitation for hemiparesis. Has difficulty with ambulation and requires assistance with ADLs.

PAST MEDICAL HISTORY:
- Cerebrovascular disease, unspecified
- Hemiparesis following stroke
- Atrial fibrillation
- Essential hypertension
- Hyperlipidemia

MEDICATIONS:
- Warfarin (INR goal 2-3)
- Atorvastatin 40mg daily
- Lisinopril 20mg daily
- Aspirin 81mg daily

DISCHARGE DIAGNOSIS:
1. Cerebrovascular disease
2. Hemiplegia following stroke
3. Atrial fibrillation
4. Essential hypertension
5. Hyperlipidemia"""
    },
    
    21: {
        "title": "Recurrent Major Depression",
        "text": """PATIENT: 38-year-old female
ADMISSION DATE: 05/01/2026

CHIEF COMPLAINT: Worsening depression

HISTORY OF PRESENT ILLNESS:
Patient with recurrent major depressive disorder presents with worsening symptoms despite medication compliance. Reports depressed mood, anhedonia, insomnia, decreased appetite, and difficulty concentrating. PHQ-9 score 21. No suicidal ideation.

PAST MEDICAL HISTORY:
- Major depressive disorder, recurrent, moderate
- Generalized anxiety disorder
- Insomnia
- Migraine headaches

MEDICATIONS:
- Escitalopram 20mg daily (increased from 10mg)
- Bupropion 150mg daily added
- Trazodone 50mg at bedtime
- Sumatriptan PRN

DISCHARGE DIAGNOSIS:
1. Recurrent major depression, moderate
2. Generalized anxiety disorder
3. Insomnia
4. Migraine"""
    },
    
    22: {
        "title": "Secondary Osteoarthritis of Hip",
        "text": """PATIENT: 66-year-old male
ADMISSION DATE: 05/05/2026

CHIEF COMPLAINT: Hip pain

HISTORY OF PRESENT ILLNESS:
Patient with secondary osteoarthritis of left hip presents for evaluation. Reports progressive pain over 2 years, now limiting ambulation. X-ray shows severe joint space narrowing and osteophyte formation. Considering hip replacement.

PAST MEDICAL HISTORY:
- Secondary osteoarthritis of hip
- Primary osteoarthritis of knee
- Chronic pain syndrome
- History of falls

MEDICATIONS:
- Acetaminophen 1000mg TID
- Meloxicam 15mg daily
- Physical therapy ongoing

DISCHARGE DIAGNOSIS:
1. Secondary osteoarthritis, left hip
2. Primary osteoarthritis, unspecified knee
3. Chronic pain syndrome
4. Difficulty in walking"""
    },
    
    23: {
        "title": "Lumbar Spinal Stenosis",
        "text": """PATIENT: 71-year-old female
ADMISSION DATE: 05/10/2026

CHIEF COMPLAINT: Back and leg pain with walking

HISTORY OF PRESENT ILLNESS:
Patient with lumbar spinal stenosis presents with neurogenic claudication. Reports bilateral leg pain when walking more than one block, relieved by sitting. MRI confirms moderate to severe central stenosis at L3-L4 and L4-L5.

PAST MEDICAL HISTORY:
- Spinal stenosis, lumbar region
- Low back pain
- Osteoporosis
- Vitamin D deficiency

MEDICATIONS:
- Gabapentin 300mg TID
- Alendronate 70mg weekly
- Vitamin D3 2000 units daily
- Acetaminophen PRN

DISCHARGE DIAGNOSIS:
1. Spinal stenosis, lumbar region
2. Low back pain
3. Osteoporosis without fracture
4. Vitamin D deficiency"""
    },
    
    24: {
        "title": "Pulmonary Hypertension with Right Heart Failure",
        "text": """PATIENT: 64-year-old female
ADMISSION DATE: 05/15/2026

CHIEF COMPLAINT: Progressive shortness of breath

HISTORY OF PRESENT ILLNESS:
Patient with secondary pulmonary hypertension presents with worsening dyspnea and lower extremity edema. Echo shows elevated PA pressures (55 mmHg) and right ventricular dysfunction. Has chronic hypoxic respiratory failure requiring home oxygen.

PAST MEDICAL HISTORY:
- Secondary pulmonary hypertension
- Chronic hypoxic respiratory failure
- COPD
- Peripheral edema

MEDICATIONS:
- Sildenafil 20mg TID
- Furosemide 40mg daily
- Supplemental oxygen 2L NC
- Albuterol inhaler PRN

DISCHARGE DIAGNOSIS:
1. Secondary pulmonary hypertension
2. Chronic respiratory failure, hypoxic
3. COPD
4. Peripheral edema"""
    },
    
    25: {
        "title": "Urinary Tract Infection with CKD",
        "text": """PATIENT: 79-year-old female
ADMISSION DATE: 05/20/2026

CHIEF COMPLAINT: Burning urination and confusion

HISTORY OF PRESENT ILLNESS:
Elderly patient with chronic kidney disease presents with dysuria, urinary frequency, and new onset confusion. Urinalysis shows pyuria and bacteriuria. Urine culture positive for E. coli. Creatinine elevated at baseline 1.9.

PAST MEDICAL HISTORY:
- Urinary tract infection
- Chronic kidney disease stage 3
- Overactive bladder
- Dementia, unspecified
- History of falls

MEDICATIONS:
- Nitrofurantoin 100mg BID x 5 days (renal dosing)
- Oxybutynin 5mg daily
- Donepezil 10mg daily

DISCHARGE DIAGNOSIS:
1. Urinary tract infection
2. Chronic kidney disease stage 3
3. Overactive bladder
4. Dementia, unspecified
5. History of falling"""
    }
}

def get_case(case_number):
    """Get a specific case by number (1-25)"""
    return DISCHARGE_SUMMARIES.get(case_number, DISCHARGE_SUMMARIES[1])

def get_case_titles():
    """Get list of all case titles"""
    return [DISCHARGE_SUMMARIES[i]["title"] for i in range(1, 26)]
