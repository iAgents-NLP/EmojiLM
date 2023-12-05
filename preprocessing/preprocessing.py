from collections import Counter
import jsonlines
import re
import csv
import argparse
import os

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
    text_without_urls = re.sub(r"https?://\S+|www\.\S+", "", text)
    cleaned_text = re.sub(r"^[\s,。、，]+|[\s,。、，]+$", "", text_without_urls)
    return cleaned_text


def contains_three_continuous_chars(sentence):
    pattern = r"(.)\1\1"  # Pattern to match three continuous characters
    match = re.search(pattern, sentence)
    return bool(match)


dataset = []
for text in input_text_list:
    text = preprocess(text)
    extracted_content = extract_continuous_emojis(text)
    for input_text, output_text in extracted_content:
        input_text = postprocess(input_text)
        output_text = postprocess(output_text)
        if len(input_text) <= 3:
            continue
        if contains_three_continuous_chars(input_text):
            continue
        dataset.append({"input": input_text, "output": output_text})

print(f"Total {len(dataset)} lines after preprocessing")
print(
    f"Samples with longer than 128 chars: {len([d for d in dataset if len(d['input']) > 128])}")

with jsonlines.open("emoji_dataset/dataset.jsonl", "w") as writer:
    writer.write_all(dataset)


# count output emoji frequency
output_emoji_counter = Counter()
for text in dataset:
    output_emoji_counter.update(text['output'])
print(output_emoji_counter)
