import re
from typing import List, Dict
from deep_translator import GoogleTranslator

# === Config ===
input_file_path = r"C:\Users\kaita\Downloads\Bach_Double_english.vtt"
output_file_path = r"C:\Users\kaita\Downloads\Bach_Double_french.vtt"

source_lang = 'en'
target_lang = 'fr'

# Musical term preservation dictionary
term_map: Dict[str, str] = {
    'measure': 'mesure',
    'bow': 'archet',
    'position': 'position',
    'finger': 'doigt',
    'string': 'corde',
    'sharp': 'dièse',
    'flat': 'bémol',
}

TIMESTAMP_ARROW = "-->"
CONTROL_PREFIXES = ("WEBVTT", "NOTE", "STYLE", "REGION")

def is_translatable(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if s.isdigit():
        return False
    if TIMESTAMP_ARROW in s:
        return False
    upper = s.upper()
    if upper.startswith(CONTROL_PREFIXES):
        return False
    return True

PLACEHOLDER_PREFIX = "@@T_"
PLACEHOLDER_SUFFIX = "@@"

def protect_terms(text: str) -> str:
    for eng in sorted(term_map.keys(), key=len, reverse=True):
        pattern = re.compile(rf"\b{re.escape(eng)}\b", flags=re.IGNORECASE)
        text = pattern.sub(f"{PLACEHOLDER_PREFIX}{eng.upper()}{PLACEHOLDER_SUFFIX}", text)
    return text

def restore_terms(text: str) -> str:
    def repl(m: re.Match) -> str:
        key = m.group(1).lower()
        return term_map.get(key, key)
    return re.sub(rf"{re.escape(PLACEHOLDER_PREFIX)}([A-Z]+){re.escape(PLACEHOLDER_SUFFIX)}", repl, text)

def translate_line_by_line(lines_to_translate: List[str], src: str, tgt: str) -> List[str]:
    translator = GoogleTranslator(source=src, target=tgt)
    out = []
    for t in lines_to_translate:
        try:
            translated = translator.translate(t)
        except Exception:
            translated = t  # keep original if translation fails
        out.append(translated)
    return out

with open(input_file_path, "r", encoding="utf-8") as f:
    original_lines = f.readlines()

indices_to_translate: List[int] = []
payload: List[str] = []

for idx, line in enumerate(original_lines):
    if is_translatable(line):
        protected = protect_terms(line.rstrip("\n"))
        payload.append(protected)
        indices_to_translate.append(idx)

if payload:
    translated_payload = translate_line_by_line(payload, source_lang, target_lang)
    translated_payload = [restore_terms(t) for t in translated_payload]
else:
    translated_payload = []

out_lines = original_lines[:]
for i, idx in enumerate(indices_to_translate):
    original_has_nl = out_lines[idx].endswith("\n")
    new_line = translated_payload[i]
    out_lines[idx] = (new_line + ("\n" if original_has_nl else ""))

with open(output_file_path, "w", encoding="utf-8") as f:
    f.writelines(out_lines)

print(f"Done. Saved: {output_file_path}")
