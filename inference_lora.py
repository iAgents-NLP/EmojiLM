import torch
import os
import argparse

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftConfig, PeftModel


class EmojiLM:
    def __init__(self, model_name, lora_path, upload_to_hub=False) -> None:
        self.device = 'cuda'
        self.task_prefix = "emoji: "
        self.prepare_model(model_name, lora_path)
        text_input = "那你很厲害誒"
        print("開機測試：", text_input, self.serve(text_input))
        if upload_to_hub:
            self.model.push_to_hub("EmojiLM_Seq2SeqLM_LoRA", private=True)

    def prepare_model(self, model_name, lora_path):
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, use_fast=False)
        self.tokenizer.truncation_side = 'left'

        # peft_config = PeftConfig.from_pretrained(lora_path)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.model = PeftModel.from_pretrained(model, lora_path)
        self.model.eval()
        self.model.to(self.device)

    @torch.no_grad()
    def serve(self, inputs):
        inputs = [self.task_prefix + inputs]
        model_inputs = self.tokenizer(
            inputs, max_length=128, padding='do_not_pad', truncation=True, return_tensors="pt")
        outputs = self.model.generate(
            input_ids=model_inputs["input_ids"].to(self.device), max_new_tokens=5, do_sample=True, top_p=0.9, top_k=0, temperature=0.8)

        ret = self.tokenizer.batch_decode(
            outputs.detach().cpu().numpy(), skip_special_tokens=True)[0]
        return ret


def parse_args():
    parser = argparse.ArgumentParser(description="Run PEFT inference")
    parser.add_argument("--model", type=str, default="google/mt5-base")
    parser.add_argument("--lora", type=str, required=True)
    parser.add_argument("--upload", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    LM = EmojiLM(args.model, args.lora, args.upload)
    while True:
        try:
            inp = input("Enter input: ")
        except (KeyboardInterrupt, EOFError):
            break
        print(inp, LM.serve(inp))


if __name__ == "__main__":
    main()
