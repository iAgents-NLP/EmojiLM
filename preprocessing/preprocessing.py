import argparse
import csv
import os
import random
import re
from collections import Counter

import jsonlines
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm.auto import tqdm

random.seed(11944004)

parser = argparse.ArgumentParser(description='Read contents of CSV files')
parser.add_argument('files', metavar='file', nargs='*',
                    help='CSV file(s) to read')
args = parser.parse_args()

csv_files = args.files
if len(csv_files) == 0:
    csv_files = [os.path.join("emoji_dataset", f)
                 for f in os.listdir("emoji_dataset")
                 if f.endswith(".csv")]

input_text_list = []
for filename in csv_files:
    with open(filename) as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            input_text_list.append(row[0])
print(f"Total {len(input_text_list)} lines before preprocessing")


def preprocess(text):
    text = re.sub(r"[\u2009\n]", " ", text)
    text = re.sub(r"[\u200c\u200d\ufe0f]", "", text)
    return text


def extract_continuous_emojis(text):
    with open("emoji_dataset/emojis.txt", "r") as f:
        pattern = f.readline()
    pattern = f"([^{pattern}]+)([{pattern}|\n]+)"
    matches = re.findall(pattern, text)
    return matches


def postprocess(text):
    text = re.sub(r"\ufffd", "", text)
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"^[\s,。、，]+|[\s,。、，]+$", "", text)
    return text


def contains_three_continuous_chars(sentence):
    pattern = r"(.)\1\1"  # Pattern to match three continuous characters
    match = re.search(pattern, sentence)
    return bool(match)


dataset = []
for text in tqdm(input_text_list):
    text = preprocess(text)
    extracted_content = extract_continuous_emojis(text)
    for input_text, output_text in extracted_content:
        input_text = postprocess(input_text)
        output_text = postprocess(output_text)
        if len(input_text) < 3:
            continue
        if contains_three_continuous_chars(input_text):
            continue
        if len(input_text) == 0 or len(output_text) == 0:
            continue
        dataset.append({"input": input_text, "output": output_text})

print(f"Total {len(dataset)} lines after preprocessing")

# Remove consecutive lines with the same output of more than 3
prev_output = ""
prev_count = 0
dataset_without_duplicates = []
for data in dataset:
    if data["output"] == prev_output:
        prev_count += 1
    else:
        prev_count = 0
    if prev_count < 3:
        dataset_without_duplicates.append(data)
    prev_output = data["output"]
dataset = dataset_without_duplicates

print(f"Total {len(dataset)} lines after duplicate removal")
print(
    f"Samples with longer than 128 input chars: {len([d for d in dataset if len(d['input']) > 128])}")
print(
    f"Samples with longer than 6 output chars: {len([d for d in dataset if len(d['output']) > 6])}")
with jsonlines.open("emoji_dataset/dataset.jsonl", "w") as writer:
    writer.write_all(dataset)


def split_jsonl(input_file, train_file, val_file, split_ratio=0.8):
    if split_ratio <= 0 or split_ratio >= 1:
        raise ValueError("Split ratio should be between 0 and 1")

    with jsonlines.open(input_file, 'r') as reader:
        data = list(reader)
        random.shuffle(data)

        split_index = int(len(data) * split_ratio)
        train_data = data[:split_index]
        val_data = data[split_index:]

    # Writing to train.jsonl
    with jsonlines.open(train_file, 'w') as writer_train:
        for item in train_data:
            writer_train.write(item)

    # Writing to val.jsonl
    with jsonlines.open(val_file, 'w') as writer_val:
        for item in val_data:
            writer_val.write(item)


input_jsonl = 'emoji_dataset/dataset.jsonl'
train_output = 'emoji_dataset/train.jsonl'
val_output = 'emoji_dataset/val.jsonl'

split_ratio = 0.95
split_jsonl(input_jsonl, train_output, val_output, split_ratio)


print("Plotting...")
input_lengths = [len(d['input']) for d in dataset]
output_lengths = [len(d['output']) for d in dataset]
sns.set_theme(style="whitegrid")

fig, axes = plt.subplots(1, 2, figsize=(12, 6))

# Plot input length distribution on a log scale
sns.histplot(input_lengths, bins=100, ax=axes[0])
axes[0].set_title('Input Length Distribution')
axes[0].set_xlabel('Length')
axes[0].set_ylabel('Count')
axes[0].set_yscale('log')

# Plot output length distribution on a log scale
sns.histplot(output_lengths, bins=100, ax=axes[1])
axes[1].set_title('Output Length Distribution')
axes[1].set_xlabel('Length')
axes[1].set_ylabel('Count')
axes[1].set_yscale('log')

plt.tight_layout()
plt.savefig("emoji_dataset/length_distributions.png")

# Plot emoji frequency
emoji_counter = Counter()
for text in dataset:
    emoji_counter.update(text['output'])
plt.figure(figsize=(12, 6))

values = list(emoji_counter.values())
sorted_idx = sorted(range(len(values)),
                    key=lambda k: values[k], reverse=True)
sns.barplot([values[i] for i in sorted_idx])
plt.xticks([])
plt.title('Emoji Frequency Distribution')
plt.ylabel('Count')
plt.yscale('log')
plt.tight_layout()
plt.savefig("emoji_dataset/emoji_distribution.png")
