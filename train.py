import evaluate
import jsonlines
import numpy as np
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, DataCollatorForSeq2Seq, Seq2SeqTrainingArguments, Seq2SeqTrainer
from datasets import load_dataset


def main():
    dataset_name = "emoji_dataset"
    model_name = "google/mt5-small"

    task_prefix = "emoji: "
    max_length = 128

    dataset = load_dataset(dataset_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
    tokenizer.deprecation_warnings["Asking-to-pad-a-fast-tokenizer"] = True

    # # Update Tokenizers to include all emojis
    # emojis = open("emoji_dataset/emojis.txt", "r").read().split("|")
    # print(emojis)
    # for emoji_str in emojis:
    #     for emoji in emoji_str:
    #         if not tokenizer.get_vocab().get(emoji):
    #             tokenizer.get_vocab()[emoji] = len(tokenizer.get_vocab())
    #             print("Added", emoji, "to vocab")

    def preprocess_function(examples):
        inputs, targets = examples['input'], examples['output']

        inputs = [task_prefix + inp for inp in inputs]
        model_inputs = tokenizer(
            inputs, max_length=max_length, padding='longest', truncation=True)
        labels = tokenizer(
            text_target=targets, max_length=max_length, padding='longest', truncation=True)

        labels["input_ids"] = [
            [(l if l != tokenizer.pad_token_id else -100) for l in label] for label in labels["input_ids"]
        ]
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    dataset = dataset.map(preprocess_function, batched=True)

    # Training
    metric = evaluate.load("rouge")
    current_eval_epoch = 0

    def compute_metrics(eval_preds):
        nonlocal current_eval_epoch
        predictions = eval_preds.predictions
        labels = eval_preds.label_ids
        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)

        decoded_inputs = tokenizer.batch_decode(
            eval_preds.inputs, skip_special_tokens=True)
        decoded_preds = tokenizer.batch_decode(
            predictions, skip_special_tokens=True)
        decoded_labels = tokenizer.batch_decode(
            labels, skip_special_tokens=True)

        with jsonlines.open(f"logs/predictions_{current_eval_epoch}.jsonl", "w") as writer:
            output_jsonl = []
            for input_text, output_text, gt_text in zip(decoded_inputs, decoded_preds, decoded_labels):
                output_dict = {"input": input_text,
                               "output": output_text, "gt": gt_text}
                output_jsonl.append(output_dict)
            writer.write_all(output_jsonl)

        current_eval_epoch += 1
        metric.add_batch(predictions=decoded_preds, references=decoded_labels)
        rouge_score = metric.compute()

        return rouge_score

    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    label_pad_token_id = -100
    data_collator = DataCollatorForSeq2Seq(
        tokenizer,
        model=model,
        label_pad_token_id=label_pad_token_id,
        pad_to_multiple_of=8,
    )

    training_args = Seq2SeqTrainingArguments(
        per_device_train_batch_size=2,
        per_device_eval_batch_size=8,
        learning_rate=1e-4,

        warmup_steps=10,
        num_train_epochs=5,
        fp16=True,

        output_dir="./results",
        report_to="tensorboard",
        dataloader_num_workers=8,
        predict_with_generate=True,
        evaluation_strategy="epoch",
        load_best_model_at_end=True,
        logging_dir="./logs",
        logging_steps=5,
        save_strategy='epoch',
        overwrite_output_dir=True,
        include_inputs_for_metrics=True,
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset['train'],
        eval_dataset=dataset['validation'],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )
    trainer.train()


if __name__ == "__main__":
    main()
