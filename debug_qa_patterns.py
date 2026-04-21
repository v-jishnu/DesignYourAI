"""Debug Q&A pattern matching."""
import re

# Q&A Pattern Detection (from pdf_extractor.py)
Q_A_PATTERN_1 = re.compile(
    r'(?:Q|Question)[\s\.\:]+(.+?)\s*(?:A|Answer)[\s\.\:]+(.+?)(?=(?:Q|Question)[\s\.\:]|$)',
    re.DOTALL | re.IGNORECASE
)

Q_A_PATTERN_2 = re.compile(
    r'(\d+)\.\s*(.+?)\?\s*(?:Answer|Ans)[\s\.\:]+(.+?)(?=\d+\.|$)',
    re.DOTALL | re.IGNORECASE
)

Q_A_PATTERN_3 = re.compile(
    r'Question[\s\.\:]+(.+?)\s*Answer[\s\.\:]+(.+?)(?=Question[\s\.\:]|$)',
    re.DOTALL | re.IGNORECASE
)

# Sample text from the PDF
sample_text = """What is the difference between generative and discriminative models?
Answer:
Generative models, such as Variational Autoencoders (VAEs) and Generative Adversarial Networks (GANs), are
designed to generate new data samples by understanding and capturing the underlying data distribution.
Discriminative models, on the other hand, focus on distinguishing between different classes or categories within the
data.
Describe the architecture of a Generative Adversarial Network and how the generator and discriminator interact
during training.
Answer:
A Generative Adversarial Network comprises a generator and a discriminator. The generator produces synthetic
data, attempting to mimic real data, while the discriminator evaluates the authenticity of the generated samples.
During training, the generator and discriminator engage in a dynamic interplay, each striving to outperform the
other."""

print("Testing Q&A Pattern Matching")
print("=" * 80)

print("\nPattern 1 (Q:/A: format):")
matches1 = Q_A_PATTERN_1.findall(sample_text)
print(f"Matches: {len(matches1)}")
for i, match in enumerate(matches1[:2], 1):
    print(f"\n  Match {i}:")
    print(f"    Q: {match[0][:100]}...")
    print(f"    A: {match[1][:100]}...")

print("\n" + "-" * 80)
print("\nPattern 2 (Numbered with Answer:):")
matches2 = Q_A_PATTERN_2.findall(sample_text)
print(f"Matches: {len(matches2)}")

print("\n" + "-" * 80)
print("\nPattern 3 (Question:/Answer:):")
matches3 = Q_A_PATTERN_3.findall(sample_text)
print(f"Matches: {len(matches3)}")

# Now test with "What" prefix pattern
print("\n" + "=" * 80)
print("\nTesting Alternative Pattern (What...?\\nAnswer:)")
print("=" * 80)

WHAT_PATTERN = re.compile(
    r'(What.+?\?)\s*Answer:\s*(.+?)(?=(?:What|Describe|Explain|How|Why|$))',
    re.DOTALL | re.IGNORECASE
)

matches_what = WHAT_PATTERN.findall(sample_text)
print(f"Matches: {len(matches_what)}")
for i, match in enumerate(matches_what[:2], 1):
    print(f"\n  Match {i}:")
    print(f"    Q: {match[0][:100]}...")
    print(f"    A: {match[1][:100]}...")
