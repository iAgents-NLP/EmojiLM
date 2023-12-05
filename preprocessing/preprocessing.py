import jsonlines
import json
import re


range_list = [
    ["1f170", "1f251"],
    ["1f300", "1f64f"],
    ["1f680", "1f6c5"],
    ["2702", "27b0"],
]
emoji_unicode = [int("1f004", 16), int("1f0cf", 16), int("24c2", 16)]
for a, b in range_list:
    emoji_unicode.extend(list(range(int(a, 16), int(b, 16) + 1)))
# emoji_unicode = list(map(ord, emoji_unicode))
# print(emoji_unicode)
# print(list(map(chr, emoji_unicode)))
# print("🤮".encode("utf-8"))
in_content = []
out_content = []
with open("dump.json", "r") as f:
    for data in jsonlines.Reader(f):
        # print(data)
        if data["Type"] == 1:
            choose = False
            for c in data["Content"]:
                if ord(c) in emoji_unicode:
                    # print(c)
                    choose = True
                    break
            if choose:
                in_content.append(
                    data["Content"]
                    .replace("\u2009", "")
                    .replace("\u200c", "")
                    .replace("\u200d", "")
                    .replace("\n", " ")
                )
            else:
                out_content.append(data["Content"])

# print(hex(ord(content[-5][14])))
# print(int("1f601", 16))
# print(b"\xF0\x9F\x98\x81".decode("utf-8"))
# print(ord(b"\xF0\x9F\x98\x81".decode("utf-8")))
# print(content[-5][14].encode("utf-8"))

# print(type(data))
# print(in_content)
# print(out_content)


def extract_continuous_emojis(text):
    with open("patten.txt", "r") as f:
        pattern = f.readline()
    pattern = f"([^{pattern}]+)([{pattern}|\n]+)"
    matches = re.findall(pattern, text)
    return matches


print(extract_continuous_emojis("231😊😊\n😊123\n123😊"))
print(extract_continuous_emojis("231\n123\n123😊"))


def postprocess(text):
    url_pattern = re.compile(r"https?://\S+|www\.\S+")

    # Replace URLs in the text with an empty string
    text_without_urls = url_pattern.sub("", text)
    cleaned_text = re.sub(r"^[\s,。、，]+|[\s,。、，]+$", "", text_without_urls)

    return cleaned_text


in_out_split = []
for data in in_content:
    extracted_content = extract_continuous_emojis(data)
    for input, output in extracted_content:
        input = postprocess(input)
        if len(input) <= 3:
            continue
        output = postprocess(output)
        in_out_split.append({"input": input, "output": output})


with open("dataset.json", "w", encoding="utf8") as f:
    json.dump(in_out_split, f, indent=2, ensure_ascii=False)

print(len("小姑子"))
"""
1F004
1F0CF
1F170 - 1F251
1F300 - 1F64F
1F680 - 1F6C5
0030 - 0039
24C2
2702 - 27B0
"""
