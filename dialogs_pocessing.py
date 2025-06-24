import os
import json
from datetime import datetime

THRESHOLD = 60 * 60
LONG_GAP_COUNT_THRESHOLD = 5

INPUT_DIR = "../bf_dialogs"
OUTPUT_DIR = "../dialogs_processed"

os.makedirs(OUTPUT_DIR, exist_ok=True)

for filename in os.listdir(INPUT_DIR):
    if not filename.lower().endswith('.json'):
        continue

    input_path = os.path.join(INPUT_DIR, filename)
    base_name = os.path.splitext(filename)[0]

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    msgs = data.get('messages') if isinstance(data, dict) and 'messages' in data else data
    if not isinstance(msgs, list) or not msgs:
        continue

    parsed = []
    for m in msgs:
        dt = None
        if 'date' in m:
            try:
                dt = datetime.fromisoformat(m['date'])
            except ValueError:
                pass
        elif 'ts' in m:
            try:
                dt = datetime.fromtimestamp(float(m['ts']))
            except ValueError:
                pass
        if dt:
            m['dt'] = dt
            parsed.append(m)
    parsed.sort(key=lambda x: x['dt'])

    sessions = []
    current = []
    long_gap_count = 0

    for prev, cur in zip(parsed, parsed[1:]):
        if not current:
            current.append(prev)
        delta = (cur['dt'] - prev['dt']).total_seconds()
        same_sender = prev.get('recepeint') == cur.get('recepeint')

        if delta > THRESHOLD and same_sender:
            long_gap_count += 1
            if long_gap_count < LONG_GAP_COUNT_THRESHOLD:
                sessions.append(current)
                current = []
        else:
            long_gap_count = 0
        current.append(cur)
    if current:
        sessions.append(current)

    for idx, sess in enumerate(sessions, start=1):
        pairs = []
        for a, b in zip(sess, sess[1:]):
            if a.get('recepeint') == 'me' and b.get('recepeint') != 'me':
                completion = a.get('text', '').strip().replace('\n', ' ')
                prompt = b.get('text', '').strip().replace('\n', ' ')
                pairs.append({
                    "prompt": f" {prompt}###",
                    "completion": f"{completion}\n###\n"
                })
        if not pairs:
            continue
        out_filename = f"{base_name}_part{idx}.jsonl"
        with open(os.path.join(OUTPUT_DIR, out_filename), 'w', encoding='utf-8') as out_f:
            for rec in pairs:
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"Written {len(pairs)} pairs to {out_filename}")