import re
from typing import List
from .patterns import URL_PATTERNS, EXTRA_BAD_WORDS, CHAR_REPLACEMENTS


class TextValidator:
    def __init__(self, extra_bad_words: List[str] = None):
        self.extra_bad_words = set(EXTRA_BAD_WORDS)
        if extra_bad_words:
            self.extra_bad_words.update(extra_bad_words)

    @staticmethod
    def normalize_text(text: str) -> str:
        text = re.sub(r'(h\s*t\s*t\s*p\s*s?\s*:?\s*/\s*/)', 'http://', text, flags=re.IGNORECASE)
        text = re.sub(r'(w\s*w\s*w\s*\.)', 'www.', text, flags=re.IGNORECASE)
        return text

    @staticmethod
    def normalize_profanity(text: str) -> str:
        return re.sub(r'\s+', '', text.lower())

    @staticmethod
    def distance(a: str, b: str) -> int:
        n, m = len(a), len(b)
        if n > m:
            a, b = b, a
            n, m = m, n

        current_row = range(n + 1)
        for i in range(1, m + 1):
            previous_row, current_row = current_row, [i] + [0] * n
            for j in range(1, n + 1):
                add, delete, change = previous_row[j] + 1, current_row[j - 1] + 1, previous_row[j - 1]
                if a[j - 1] != b[i - 1]:
                    change += 1
                current_row[j] = min(add, delete, change)

        return current_row[n]

    @staticmethod
    def replace_special_chars(text: str) -> str:
        for key, values in CHAR_REPLACEMENTS.items():
            for letter in values:
                text = text.replace(letter, key)
        return text

    def contains_similar_word(self, text: str, word: str) -> bool:
        for part in range(len(text)):
            fragment = text[part: part + len(word)]
            if len(fragment) < len(word):
                continue
            distance = self.distance(fragment, word)
            max_allowed_distance = len(word) * 0.25
            if distance <= max_allowed_distance:
                return True
        return False

    def contains_url(self, text: str) -> bool:
        text = self.normalize_text(text)
        return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in URL_PATTERNS)

    def contains_profanity(self, text: str) -> bool:
        normalized_text = self.normalize_profanity(text)
        cleaned_text = self.replace_special_chars(normalized_text)
        for bad_word in self.extra_bad_words:
            if bad_word in cleaned_text:
                return True

            if self.contains_similar_word(cleaned_text, bad_word):
                return True

        return False

    def validate(self, text: str) -> dict:      
        return {
            'has_url': self.contains_url(text),
            'has_profanity': self.contains_profanity(text)
        }
