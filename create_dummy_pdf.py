import os
from fpdf import FPDF

if not os.path.exists("data"):
    os.makedirs("data")

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
text = """Type 2 diabetes is a chronic condition that affects the way the body processes blood sugar (glucose). 
Symptoms of Type 2 diabetes include:
- increased thirst
- frequent urination
- increased hunger
- unintended weight loss
- fatigue
- blurred vision
- slow-healing sores
- frequent infections.
Proper management involves a healthy diet, regular physical activity, maintaining a normal body weight, and sometimes medication.
"""
pdf.multi_cell(0, 10, text)
pdf.output("data/diabetes_info.pdf")
print("Dummy PDF created in data/diabetes_info.pdf")
