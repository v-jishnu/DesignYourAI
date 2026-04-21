"""Quick script to view latest generated MCQs."""
import pandas as pd

df = pd.read_excel('data/knowledge_base/mcq_knowledge_base.xlsx')

print("=" * 80)
print("LAST 5 GENERATED MCQs")
print("=" * 80)

for idx, row in df.tail(5).iterrows():
    print(f"\n#{idx+1}: {row['Question_Text']}")
    print(f"   A) {row['Option_A']}")
    print(f"   B) {row['Option_B']}")
    print(f"   C) {row['Option_C']}")
    print(f"   D) {row['Option_D']}")
    print(f"   Correct: {row['Correct_Answer']}")
    print(f"   Category: {row['Category']} | Topic: {row['Topic']} | Difficulty: {row['Difficulty']}")
    print(f"   Source: {row['Source']}")

print("\n" + "=" * 80)
print(f"TOTAL MCQs IN KNOWLEDGE BASE: {len(df)}")
print("=" * 80)
