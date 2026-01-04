import asyncio
from typing import List

from googletrans import Translator


class VTTTranslator:
    def __init__(self):
        self.translator = Translator()

    async def translate_batch(self, texts: List[str], dest: str = 'fr') -> List[str]:
        """Translate a batch of texts more efficiently."""
        try:
            translations = await asyncio.gather(
                *[self.translator.translate(text, dest=dest) for text in texts]
            )
            return [t.text for t in translations]
        except Exception as e:
            print(f"Error in batch translation: {e}")
            return texts

    async def process_vtt_file(self, input_file: str, output_file: str, target_lang: str = 'fr'):
        """Process the VTT file with optimized translation."""
        # Read and parse the file
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Identify lines that need translation
        to_translate = []
        translate_indices = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if (not stripped or stripped.isdigit() or '-->' in stripped or stripped == 'WEBVTT'):
                continue
            to_translate.append(stripped)
            translate_indices.append(i)

        # Batch translate all text at once
        translated_texts = await self.translate_batch(to_translate, target_lang)

        # Reconstruct the lines
        translated_lines = lines.copy()
        for idx, trans_text in zip(translate_indices, translated_texts):
            translated_lines[idx] = trans_text + '\n'

        # Verify line count
        if len(translated_lines) != len(lines):
            raise ValueError(f"Line count mismatch! Original: {len(lines)}, Translated: {len(translated_lines)}")

        # Write output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(translated_lines)

        print(f"Successfully translated file saved to {output_file}")


def TranslateFunction(input_vtt_uri, output_vtt_uri, language_short_code):
    # Create a new event loop
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        translator = VTTTranslator()
        loop.run_until_complete(translator.process_vtt_file(input_vtt_uri, output_vtt_uri, language_short_code))
        loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        loop.close()
        print("DONE TRANSLATING")
        return output_vtt_uri


TranslateFunction(r"C:\Users\kaita\Downloads\Bach Double from Partita #1_english.vtt", r"C:\Users\kaita\Downloads\Bach Double from Partita #1_pourtuguese.vtt", 'pt')

