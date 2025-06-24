import os
import json
import glob

PERSONA_FILE = '../persona.json'
PROCESSED_DIR = '../dialogs_processed'
OUTPUT_DIR = '../datasets'

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(PERSONA_FILE, 'r', encoding='utf-8') as f:
    persona = json.load(f)

persona_text = (
    f"<system> Ты — это {persona.get('name', 'Пользователь')}\n"
    f"Профессия: {persona.get('occupation', '')}\n"
    f"Интересы: {', '.join(persona.get('interests', []))}.\n"
    f"Стиль: {persona.get('tone', '')}.\n"
    f"Любимые фразы: {', '.join(persona.get('favorite_phrases', []))}.\n"
    f"Избегать: {', '.join(persona.get('avoid', []))}." \
    "</system>\n"
)

records = []
for path in glob.glob(os.path.join(PROCESSED_DIR, '*.jsonl')):
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                rec = json.loads(line)
                records.append(rec)
            except json.JSONDecodeError:
                continue

# 1. LoRA-SFT
lora_file = os.path.join(OUTPUT_DIR, 'lora_dataset.jsonl')
with open(lora_file, 'w', encoding='utf-8') as f:
    for rec in records:
        prompt = persona_text + rec['prompt'].replace('###', '').strip() + '\n###\n'
        completion = ' ' + rec['completion'].replace('###', '').strip() + '###'
        f.write(json.dumps({'prompt': prompt, 'completion': completion}, ensure_ascii=False) + '\n')
print(f'LoRA-SFT dataset: {lora_file}')

# 2. QLoRA
qlora_file = os.path.join(OUTPUT_DIR, 'qlora_dataset.jsonl')
with open(qlora_file, 'w', encoding='utf-8') as f:
    for rec in records:
        prompt = persona_text + rec['prompt'].replace('###', '').strip() + '\n###\n'
        completion = ' ' + rec['completion'].replace('###', '').strip() + '###'
        f.write(json.dumps({'prompt': prompt, 'completion': completion}, ensure_ascii=False) + '\n')
print(f'QLoRA dataset: {qlora_file}')

# 4. Prefix-tuning
prefix_file = os.path.join(OUTPUT_DIR, 'prefix_tuning_dataset.jsonl')
with open(prefix_file, 'w', encoding='utf-8') as f:
    for rec in records:
        user_prompt = rec['prompt'].replace('###', '').strip()
        assistant_resp = rec['completion'].replace('###', '').strip()
        input_text = persona_text + f"<user> {user_prompt}\n"
        output_text = f"<assistant> {assistant_resp}"
        f.write(json.dumps({'input_text': input_text, 'output_text': output_text}, ensure_ascii=False) + '\n')
print(f'Prefix-tuning dataset: {prefix_file}')

# 6. Prompt-tuning
prompt_file = os.path.join(OUTPUT_DIR, 'prompt_tuning_dataset.jsonl')
with open(prompt_file, 'w', encoding='utf-8') as f:
    for rec in records:
        user_prompt = rec['prompt'].replace('###', '').strip()
        assistant_resp = rec['completion'].replace('###', '').strip()
        input_text = persona_text + f"<user> {user_prompt}\n"
        output_text = f"<assistant> {assistant_resp}"
        f.write(json.dumps({'input_text': input_text, 'output_text': output_text}, ensure_ascii=False) + '\n')
print(f'Prompt-tuning dataset: {prompt_file}')