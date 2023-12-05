import os
import random

import jsonlines


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


# Example usage:
input_jsonl = 'emoji_dataset/dataset.jsonl'
train_output = 'emoji_dataset/train.jsonl'
val_output = 'emoji_dataset/val.jsonl'

split_ratio = 0.95
split_jsonl(input_jsonl, train_output, val_output, split_ratio)
