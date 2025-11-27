"""
BoDH-S - Groq AI Engine
"""

import os
from groq import Groq
from dotenv import load_dotenv
from dataset_loader import DatasetLoader

load_dotenv()


class SimpyboAI:
    """
    Core AI engine for BoDH-S.
    Keeps class name SimpyboAI for compatibility with existing imports.
    """

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("❌ GROQ_API_KEY not found")

        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

        print("📚 Loading datasets...")
        loader = DatasetLoader()
        self.examples = loader.load_examples()
        print(
            f"✅ Loaded {len(self.examples['english'])} English + "
            f"{len(self.examples['hinglish'])} Hinglish"
        )

    def explain_word(self, word: str, language: str = "english") -> dict:
        """
        Call Groq to explain a word in the requested language mode.
        language: "english" or "hinglish"
        """
        prompt = self._create_prompt(word, language)

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are BoDH-S, a friendly AI that explains difficult "
                            "words in very simple language with clear examples."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=400,
                top_p=0.9,
            )

            explanation = response.choices[0].message.content
            parsed = self._parse_response(explanation)

            return {
                "success": True,
                "word": word,
                "language": language,
                **parsed,
            }

        except Exception as e:
            return {"success": False, "word": word, "error": str(e)}

    def _create_prompt(self, word: str, language: str) -> str:
        """
        Build few-shot prompt from datasets for the given language mode.
        """
        examples = self.examples[language][:3]

        if language == "english":
            prompt = (
                "You are BoDH-S. Explain words in VERY simple English.\n\n"
                "Here are examples from dictionary.json:\n\n"
            )

            for i, ex in enumerate(examples, 1):
                prompt += (
                    f"{i}. Word: {ex['word']}\n"
                    f"   Meaning: {ex['definition']}\n"
                    f"   Example: {ex['example']}\n\n"
                )

            prompt += (
                f"Now explain this word in the SAME style:\n"
                f"Word: {word}\n\n"
                "Format:\n"
                "Simple Meaning: [one clear sentence, max ~15 words]\n"
                "Example: [one practical real-life example]\n"
                "Full Form: [if abbreviation, else N/A]"
            )

        else:  # hinglish
            prompt = (
                "You are BoDH-S. Explain words in Hinglish (Hindi + English mix) for "
                "Indian users.\n\n"
                "Here are examples from hinglish_upload_v1.json:\n\n"
            )

            for i, ex in enumerate(examples, 1):
                prompt += (
                    f"{i}. Word: {ex.get('word', 'example')}\n"
                    f"   Meaning: {ex.get('definition', '')}\n"
                    f"   Example: {ex.get('example', ex.get('input', ''))}\n\n"
                )

            prompt += (
                f"Now explain this word in the SAME style:\n"
                f"Word: {word}\n\n"
                "Format:\n"
                "Simple Meaning: [1 short sentence in Hinglish]\n"
                "Example: [1 Indian-style example sentence]\n"
                "Full Form: [agar abbreviation hai toh full form, warna N/A]"
            )

        return prompt

    def _parse_response(self, text: str) -> dict:
        """
        Parse BoDH-S response into structured fields.
        Expected markers: Simple Meaning:, Example:, Full Form:
        """
        result = {"simple_meaning": "", "example": "", "full_form": ""}

        lines = text.split("\n")
        current_field = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            lower = line.lower()

            if "simple meaning:" in lower:
                current_field = "simple_meaning"
                content = line.split(":", 1)[-1].strip()
                if content:
                    result["simple_meaning"] = content

            elif "example:" in lower:
                current_field = "example"
                content = line.split(":", 1)[-1].strip()
                if content:
                    result["example"] = content

            elif "full form:" in lower:
                current_field = "full_form"
                content = line.split(":", 1)[-1].strip()
                if content and content.lower() != "n/a":
                    result["full_form"] = content

            elif current_field and not line.startswith(
                ("Simple Meaning", "Example", "Full Form")
            ):
                # Continuation line
                if result[current_field]:
                    result[current_field] += " " + line
                else:
                    result[current_field] = line

        # Cleanup
        for key in result:
            result[key] = result[key].strip().strip("*").strip()

        # Fallback if parsing failed
        if not result["simple_meaning"]:
            result["simple_meaning"] = text[:200].strip()

        return result


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("BoDH-S - AI ENGINE TEST")
    print("=" * 60 + "\n")

    engine = SimpyboAI()

    tests = [
        ("algorithm", "english"),
        ("movie", "hinglish"),
        ("warranty", "english"),
        ("film", "hinglish"),
    ]

    for word, lang in tests:
        print(f"\n{'=' * 50}")
        print(f"Testing: {word} ({lang})")
        print("=" * 50)

        result = engine.explain_word(word, lang)

        if result["success"]:
            print(f"✅ {result['simple_meaning']}")
            print(f"💡 {result['example']}")
            if result.get("full_form"):
                print(f"📝 {result['full_form']}")
        else:
            print(f"❌ {result['error']}")

    print("\n✅ Test complete!")
