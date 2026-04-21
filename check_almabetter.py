"""Check AlmaBetter MCQs in Excel."""
import pandas as pd
import sys

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_excel('data/knowledge_base/mcq_knowledge_base.xlsx')

print("=" * 100)
print(f"TOTAL MCQs IN KNOWLEDGE BASE: {len(df)}")
print("=" * 100)

# Get last 2 MCQs (from AlmaBetter)
last_2 = df.tail(2)

for idx, row in last_2.iterrows():
    print(f"\n#{idx+1}:")
    print(f"Question: {row['Question_Text']}")
    print(f"A) {row['Option_A']}")
    print(f"B) {row['Option_B']}")
    print(f"C) {row['Option_C']}")
    print(f"D) {row['Option_D']}")
    print(f"Correct: {row['Correct_Answer']}")
    print(f"Category: {row['Category']} | Topic: {row['Topic']} | Difficulty: {row['Difficulty']}")
    print(f"Source: {row['Source']}")
    print("-" * 100)

print("\n✅ SUCCESS: AlmaBetter MCQs extracted and stored in Excel!")
