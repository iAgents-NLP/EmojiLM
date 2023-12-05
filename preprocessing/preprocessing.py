import jsonlines
import re
import csv
import argparse

parser = argparse.ArgumentParser(description='Read contents of CSV files')
parser.add_argument('files', metavar='file', nargs='+',
                    help='CSV file(s) to read')
args = parser.parse_args()

range_list = [
    ["1f170", "1f251"],
    ["1f300", "1f64f"],
    ["1f680", "1f6c5"],
    ["2702", "27b0"],
]
emoji_unicode = [int("1f004", 16), int("1f0cf", 16), int("24c2", 16)]
for a, b in range_list:
    emoji_unicode.extend(list(range(int(a, 16), int(b, 16) + 1)))

in_content = []
for filename in args.files:
    with open(filename) as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            in_content.append(row[0])
print(f"Total {len(in_content)} lines")


def extract_continuous_emojis(text):
    with open("emoji_dataset/emojis.txt", "r") as f:
        pattern = f.readline()
    pattern = f"([^{pattern}]+)([{pattern}|\n]+)"
    matches = re.findall(pattern, text)
    return matches


def postprocess(text):
    url_pattern = re.compile(r"https?://\S+|www\.\S+")

    # Replace URLs in the text with an empty string
    text_without_urls = url_pattern.sub("", text)
    cleaned_text = re.sub(r"^[\s,。、，]+|[\s,。、，]+$", "", text_without_urls)

    return cleaned_text


def contains_three_continuous_chars(sentence):
    pattern = r"(.)\1\1"  # Pattern to match three continuous characters
    match = re.search(pattern, sentence)
    return bool(match)


in_out_split = []
for data in in_content:
    extracted_content = extract_continuous_emojis(data)
    for input, output in extracted_content:
        input = postprocess(input)
        output = postprocess(output)
        if len(input) <= 3:
            continue
        if contains_three_continuous_chars(input):
            continue
        in_out_split.append({"input": input, "output": output})
print(f"Total {len(in_out_split)} lines")
print(
    f"Datas with longer than 128 chars: {len([d for d in in_out_split if len(d['input']) > 128])}")
with jsonlines.open("emoji_dataset/dataset.jsonl", "w") as writer:
    writer.write_all(in_out_split)
