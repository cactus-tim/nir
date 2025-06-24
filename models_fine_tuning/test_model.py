from peft import PeftModel, PeftConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from sentence_transformers import SentenceTransformer
from bert_score import score as bert_score
import torch

def test(output_dir, val_ds):
    peft_model_id = output_dir

    config = PeftConfig.from_pretrained(peft_model_id)
    base_model = AutoModelForCausalLM.from_pretrained(
        config.base_model_name_or_path,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )
    model = PeftModel.from_pretrained(base_model, peft_model_id)
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(peft_model_id, trust_remote_code=True)

    embedder = SentenceTransformer("all-MiniLM-L6-v2", device=model.device)

    preds, refs = [], []
    for example in val_ds:
        prompt = example.get("input", example.get("text", ""))
        reference = example.get("target_text", example.get("output", ""))

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            generated_ids = model.generate(**inputs, max_new_tokens=50)
        pred = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

        preds.append(pred)
        refs.append(reference)

    emb_preds = embedder.encode(preds, convert_to_tensor=True)
    emb_refs = embedder.encode(refs, convert_to_tensor=True)
    cos_sims = torch.cosine_similarity(emb_preds, emb_refs)
    mean_cosine = cos_sims.mean().item()

    P, R, F1 = bert_score(preds, refs, lang="ru")
    mean_bertscore_f1 = F1.mean().item()

    print(f"Mean cosine similarity: {mean_cosine:.4f}")
    print(f"Mean BERTScore F1: {mean_bertscore_f1:.4f}")