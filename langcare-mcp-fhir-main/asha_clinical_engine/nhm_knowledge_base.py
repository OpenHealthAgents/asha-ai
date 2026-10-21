"""
National Health Mission (NHM) Knowledge Base for ASHA AI Copilot.
Contains clinical protocols, handbooks, and clinical decision support resources
grounded strictly in Government of India (MoHFW) standards:
- NHM ASHA Module 6 & 7 (Maternal and Child Health)
- Integrated Management of Neonatal and Childhood Illnesses (IMNCI)
- RMNCH+A High Risk Pregnancy (HRP) Guidelines
- Comprehensive Primary Health Care (CPHC) NCD / CBAC Guidelines
"""

NHM_ASHA_MATERNAL_CHILD_HANDBOOK = """# National Health Mission (MoHFW, Government of India)
## ASHA Clinical Handbook: Maternal and Newborn Care (Module 6 & 7)

### 1. Antenatal Care (ANC) Protocol
Every pregnant woman must receive at least 4 Antenatal Checkups:
- **ANC 1**: Within 12 weeks of pregnancy (Registration, MCP Card issuance, baseline vitals, Hb test).
- **ANC 2**: Between 14 and 26 weeks (Screening for pre-eclampsia, gestational diabetes, fetal growth).
- **ANC 3**: Between 28 and 34 weeks (Screening for twin pregnancy, severe anemia, fetal lie).
- **ANC 4**: Between 36 weeks and delivery (Birth preparedness, identification of institutional delivery site).

### 2. Routine Prophylaxis
- **Tetanus and adult Diphtheria (Td)**: Two doses 1 month apart, or 1 booster if previously immunized within 3 years.
- **Iron and Folic Acid (IFA)**: 1 tablet daily (100mg elemental iron + 500mcg folic acid) starting after the first trimester for at least 180 days.
- **Calcium Supplementation**: 2 tablets daily (500mg elemental calcium each) from 14 weeks onwards, taken separately from IFA.
- **Deworming**: Albendazole 400mg single dose in the second trimester.

### 3. Maternal Danger Signs (Immediate Referral to PHC/FRU via 108 Ambulance)
- High Blood Pressure (>= 140/90 mmHg) with or without headache or visual disturbance.
- Severe Anemia (Hemoglobin < 7.0 g/dL) causing breathlessness or extreme fatigue.
- Vaginal bleeding at any stage of pregnancy.
- Convulsions or fits (Eclampsia).
- High fever (>= 38.5 deg C / 101.3 deg F).
- Severe abdominal pain not relieved by rest.
- Blurring of vision or epigastric pain.
- Reduced or absent fetal movements in third trimester.
- Premature rupture of membranes (water breaks before labor).

### 4. Postnatal Care (PNC) Home Visit Schedule
- Institutional delivery: Days 3, 7, 14, 21, 28, and 42.
- Home delivery: Days 1, 3, 7, 14, 21, 28, and 42.
- Check mother: Lochia, perineal wound, breast engorgement, maternal mood, temperature.
- Check infant: Temperature, cord care, exclusive breastfeeding, jaundice, weight gain.
"""

IMNCI_PEDIATRIC_TRIAGE_PROTOCOL = """# Integrated Management of Neonatal and Childhood Illnesses (IMNCI)
## Ministry of Health & Family Welfare, Government of India

### 1. General Danger Signs in Children (Age 2 Months to 5 Years)
A child with ANY of the following danger signs must be referred IMMEDIATELY to PHC/District Hospital:
1. **Inability to drink or breastfeed**.
2. **Vomiting everything**.
3. **Convulsions or history of convulsions during this illness**.
4. **Lethargic or unconscious**.
5. **Convulsing now**.

### 2. Respiratory Assessment (Cough or Difficult Breathing)
- Count breaths in one full minute:
  - Age 2 months up to 12 months: Fast breathing is 50 breaths per minute or more.
  - Age 12 months up to 5 years: Fast breathing is 40 breaths per minute or more.
- Look for **Chest Indrawing** (lower chest wall goes IN when child breathes IN).
- Listen for **Stridor** in a calm child.
- **Classification**:
  - *Severe Pneumonia / Very Severe Disease*: Chest indrawing OR stridor in calm child OR any general danger sign. -> URGENT REFERRAL, give first dose of oral amoxicillin if referral takes > 2 hours.
  - *Pneumonia*: Fast breathing without chest indrawing. -> Treat at home with Oral Amoxicillin for 5 days, advise mother to return in 2 days.
  - *No Pneumonia (Cough or Cold)*: No fast breathing, no chest indrawing. -> Home care, soothe throat, continue feeding.

### 3. Diarrhea Assessment
- Assess dehydration:
  - *Severe Dehydration*: Lethargic/unconscious, sunken eyes, skin pinch goes back very slowly (> 2 seconds). -> URGENT REFERRAL with ORS during transit.
  - *Some Dehydration*: Restless/irritable, sunken eyes, drinks eagerly, skin pinch goes back slowly. -> Treat with ORS at Sub-centre/home.
  - *No Dehydration*: Not enough signs. -> Home fluids and ORS.
- **Zinc Supplementation**:
  - Under 6 months: 10mg daily for 14 days.
  - 6 months and older: 20mg daily for 14 days.

### 4. Young Infants (Under 2 Months) - Possible Serious Bacterial Infection (PSBI)
Signs of PSBI (Emergency Referral):
- Fast breathing (60 breaths per minute or more).
- Severe chest indrawing.
- Nasal flaring or grunting.
- Hypothermia (< 35.5 deg C) or Fever (>= 37.5 deg C).
- Many or severe skin pustules / umbilical redness extending to skin.
- Lethargy / abnormal movements / poor sucking.
"""

ANC_HIGH_RISK_PREGNANCY_PROTOCOL = """# Comprehensive RMNCH+A High-Risk Pregnancy (HRP) Guidelines
## Government of India Protocol

### High-Risk Pregnancy Criteria:
1. **Severe Anemia**:
   - Hb < 7.0 g/dL.
   - Action: Immediate referral to FRU/District Hospital for parenteral iron (IV Iron Sucrose / Ferric Carboxymaltose) or packed red blood cell transfusion.
2. **Hypertensive Disorders of Pregnancy (HDP)**:
   - Gestational Hypertension: Systolic BP >= 140 mmHg and/or Diastolic BP >= 90 mmHg on two occasions 4 hours apart after 20 weeks.
   - Pre-eclampsia: BP >= 140/90 with proteinuria OR symptoms (headache, epigastric pain, visual blurring, pedal edema).
   - Eclampsia: Seizures in a patient with pre-eclampsia.
   - Action: Urgent referral. Administer loading dose of Magnesium Sulfate (4g IV + 10g IM) prior to transfer if MO/ANM is available.
3. **Gestational Diabetes Mellitus (GDM)**:
   - Fasting blood sugar >= 92 mg/dL or 2-hour 75g OGTT >= 140 mg/dL.
   - Action: Nutritional counseling, referral to Medical Officer for insulin/metformin.
4. **Obstetric History Red Flags**:
   - Previous Caesarean section, previous stillbirth, recurrent miscarriages, parity >= 4.
   - Action: Mandatory institutional delivery at FRU/District Hospital with blood bank.
"""

CBAC_NCD_SCREENING_GUIDELINE = """# Community Based Assessment Checklist (CBAC) for Non-Communicable Diseases
## Ministry of Health & Family Welfare, Ayushman Bharat - Health and Wellness Centres (AB-HWC)

### Target Population:
All individuals aged 30 years and older in the village catchment area.

### CBAC Scoring Matrix (Score > 4 indicates HIGH RISK):
- **Age**: 30-49 years (1 pt), >= 50 years (2 pts)
- **Smoking / Tobacco use**: Daily user (2 pts), Occasional/Past (1 pt), Never (0 pts)
- **Alcohol consumption**: Yes (1 pt), No (0 pts)
- **Waist Circumference**:
  - Men: 90-102 cm (1 pt), > 102 cm (2 pts)
  - Women: 80-88 cm (1 pt), > 88 cm (2 pts)
- **Physical Activity**: Less than 150 minutes per week (1 pt)
- **Family History**: High blood pressure, diabetes, heart attack in parents/siblings (2 pts)

### Common Warning Symptoms Requiring Immediate Medical Referral:
- Non-healing ulcer in mouth > 2 weeks.
- Persistent cough > 2 weeks or blood in sputum.
- Any change in bowel/bladder habits or unexplained bleeding.
- Lump in breast or bloody nipple discharge.
- Bleeding after intercourse or post-menopausal bleeding.
"""

NATIONAL_IMMUNIZATION_SCHEDULE = {
    "birth": ["BCG", "HepB-0", "OPV-0"],
    "6_weeks": ["OPV-1", "Pentavalent-1", "Rotavirus-1", "fIPV-1", "PCV-1"],
    "10_weeks": ["Pentavalent-2", "Rotavirus-2"],
    "14_weeks": ["OPV-2", "Pentavalent-3", "Rotavirus-3", "fIPV-2", "PCV-2"],
    "9_12_months": ["MR-1", "JE-1", "PCV-Booster", "VitaminA-1"],
    "16_24_months": ["MR-2", "JE-2", "DPT-Booster-1", "OPV-Booster"],
    "5_6_years": ["DPT-Booster-2"],
    "10_years": ["Td"],
    "16_years": ["Td"],
}
