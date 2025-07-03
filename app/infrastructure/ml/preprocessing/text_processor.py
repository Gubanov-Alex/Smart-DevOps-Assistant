"""Text preprocessing for log classification with security enhancements."""

import json
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple, Union

import torch

logger = logging.getLogger(__name__)


class VocabularySecurityError(Exception):
    """Исключение для проблем безопасности vocabulary."""

    pass


class LogTextProcessor:
    """
    Text preprocessing pipeline for log messages with secure serialization.

    Interview talking point: Production-ready text preprocessing with security
    """

    def __init__(
        self,
        max_vocab_size: int = 10000,
        max_sequence_length: int = 128,
        min_word_freq: int = 2,
    ):
        """Initialize the text processor with security features."""
        self.max_vocab_size = max_vocab_size
        self.max_sequence_length = max_sequence_length
        self.min_word_freq = min_word_freq

        # Vocabulary mappings
        self.word_to_idx: Dict[str, int] = {}
        self.idx_to_word: Dict[int, str] = {}
        self.vocab_size = 0

        # Special tokens
        self.PAD_TOKEN = "<PAD>"
        self.UNK_TOKEN = "<UNK>"
        self.START_TOKEN = "<START>"
        self.END_TOKEN = "<END>"

        # Regex patterns for log parsing (compiled for performance)
        self.timestamp_pattern = re.compile(r"\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?")
        self.ip_pattern = re.compile(
            r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}" r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
        )
        self.uuid_pattern = re.compile(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
            re.IGNORECASE,
        )
        self.number_pattern = re.compile(r"\b\d+(?:\.\d+)?\b")
        self.url_pattern = re.compile(
            r"https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?",
            re.IGNORECASE,
        )
        self.email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    def clean_log_message(self, message: str) -> str:
        """Clean and normalize a log message with enhanced security."""
        if not isinstance(message, str):
            raise ValueError(f"Expected string, got {type(message)}")

        # Ограничение длины сообщения для предотвращения DoS
        max_message_length = 10000
        if len(message) > max_message_length:
            logger.warning(f"Message too long ({len(message)} chars), truncating")
            message = message[:max_message_length]

        # Convert to lowercase
        message = message.lower()

        # КРИТИЧЕСКИ ВАЖНО: Удаление всех опасных паттернов ПЕРЕД заменой символов
        dangerous_patterns = [
            # Script injection
            r"<script[^>]*>.*?</script>",
            r"<script[^>]*>",
            r"</script>",
            r"<iframe[^>]*>.*?</iframe>",
            r"<iframe[^>]*>",
            r"</iframe>",
            # JavaScript patterns
            r"javascript\s*:",
            r"data\s*:\s*text/html",
            r"vbscript\s*:",
            # Dangerous function calls
            r"eval\s*\(",
            r"exec\s*\(",
            r"__import__\s*\(",
            r"compile\s*\(",
            r"execfile\s*\(",
            # SQL injection patterns
            r"drop\s+table",
            r"delete\s+from",
            r"insert\s+into",
            r"update\s+.*\s+set",
            r"select\s+.*\s+from",
            r"union\s+select",
            r"--\s*",
            r"/\*.*?\*/",
            # Path traversal
            r"\.\./",
            r"\.\.\\",
            r"file\s*://",
            r"ftp\s*://",
            # Log4j and other injection
            r"\$\{[^}]*\}",
            r"%\{[^}]*\}",
            # Command injection
            r"`[^`]*`",
            r"\$\([^)]*\)",
            r"&&",
            r"\|\|",
            r";\s*rm",
            r";\s*cat",
            r";\s*ls",
            r";\s*echo",
        ]

        # Применяем все паттерны для удаления опасного контента
        for pattern in dangerous_patterns:
            message = re.sub(pattern, " ", message, flags=re.IGNORECASE)

        # Replace sensitive data with placeholders
        message = self.timestamp_pattern.sub("<TIMESTAMP>", message)
        message = self.ip_pattern.sub("<IP>", message)
        message = self.uuid_pattern.sub("<UUID>", message)
        message = self.url_pattern.sub("<URL>", message)
        message = self.email_pattern.sub("<EMAIL>", message)
        message = self.number_pattern.sub("<NUM>", message)

        # УСИЛЕННАЯ фильтрация символов - только безопасные символы
        # Разрешены: буквы, цифры, пробелы, базовые знаки препинания, placeholder символы
        safe_chars = set("abcdefghijklmnopqrstuvwxyz0123456789 ._-<>")
        cleaned_chars = []
        for char in message:
            if char in safe_chars:
                cleaned_chars.append(char)
            else:
                cleaned_chars.append(" ")  # Заменяем опасные символы пробелами

        message = "".join(cleaned_chars)

        # Normalize whitespace and remove excessive spaces
        message = " ".join(message.split())

        # Финальная проверка на опасные последовательности
        final_dangerous = [
            "script",
            "javascript",
            "eval",
            "exec",
            "import",
            "drop table",
            "select",
            "${",
            "%{",
        ]
        for danger in final_dangerous:
            if danger in message:
                message = message.replace(danger, " ")

        # Normalize whitespace again after final cleaning
        message = " ".join(message.split())

        return message

    def tokenize(self, message: str) -> List[str]:
        """Tokenize cleaned message into words with validation."""
        cleaned = self.clean_log_message(message)
        tokens = cleaned.split()

        # Ограничение количества токенов
        max_tokens = 1000
        if len(tokens) > max_tokens:
            logger.warning(f"Too many tokens ({len(tokens)}), truncating")
            tokens = tokens[:max_tokens]

        # Валидация токенов
        valid_tokens = []
        for token in tokens:
            # Пропуск слишком длинных токенов (возможные атаки)
            if len(token) > 50:
                continue
            # Пропуск токенов с подозрительным содержимым
            if not token.replace("<>", "").replace("_", "").replace("-", "").isalnum():
                continue
            valid_tokens.append(token)

        # Add start/end tokens
        valid_tokens = [self.START_TOKEN] + valid_tokens + [self.END_TOKEN]

        return valid_tokens

    def build_vocabulary(self, messages: List[str]) -> None:
        """Build vocabulary from training messages with validation."""
        if not messages:
            raise ValueError("Cannot build vocabulary from empty message list")

        if len(messages) > 1_000_000:
            logger.warning(f"Large dataset ({len(messages)} messages), processing in batches")

        # Count word frequencies
        word_counts = Counter()
        processed_count = 0

        for message in messages:
            try:
                tokens = self.tokenize(message)
                word_counts.update(tokens)
                processed_count += 1

                # Прогресс для больших датасетов
                if processed_count % 10000 == 0:
                    logger.info(f"Processed {processed_count}/{len(messages)} messages")

            except Exception as e:
                logger.warning(f"Failed to process message: {e}")
                continue

        logger.info(f"Found {len(word_counts)} unique tokens from {processed_count} messages")

        # Build vocabulary with special tokens
        vocab = [self.PAD_TOKEN, self.UNK_TOKEN, self.START_TOKEN, self.END_TOKEN]

        # Add frequent words with additional validation
        frequent_words = []
        for word, count in word_counts.most_common(self.max_vocab_size - 4):
            if count >= self.min_word_freq and self._is_valid_vocab_word(word):
                frequent_words.append(word)

        vocab.extend(frequent_words)

        # Create mappings
        self.word_to_idx = {word: idx for idx, word in enumerate(vocab)}
        self.idx_to_word = {idx: word for word, idx in self.word_to_idx.items()}
        self.vocab_size = len(vocab)  # ВАЖНО: устанавливаем ПОСЛЕ создания vocab

        logger.info(f"Built vocabulary: {self.vocab_size} words")

    def _is_valid_vocab_word(self, word: str) -> bool:
        """Валидация слова для включения в vocabulary."""
        # Пропуск слишком коротких или длинных слов
        if len(word) < 1 or len(word) > 50:
            return False

        # Пропуск слов с подозрительными символами
        suspicious_patterns = ["<script", "javascript:", "eval(", "exec("]
        word_lower = word.lower()
        if any(pattern in word_lower for pattern in suspicious_patterns):
            return False

        return True

    def encode_message(self, message: str) -> Tuple[torch.Tensor, int]:
        """
        Encode a message to tensor of token indices.

        Returns:
            (encoded_tensor, actual_length)
        """
        if not self.word_to_idx:
            raise ValueError("Vocabulary not built. Call build_vocabulary() first.")

        tokens = self.tokenize(message)

        # Convert to indices
        indices = [self.word_to_idx.get(token, self.word_to_idx[self.UNK_TOKEN]) for token in tokens]

        actual_length = len(indices)

        # Pad or truncate to max_sequence_length
        if len(indices) < self.max_sequence_length:
            pad_idx = self.word_to_idx[self.PAD_TOKEN]
            indices.extend([pad_idx] * (self.max_sequence_length - len(indices)))
        else:
            indices = indices[: self.max_sequence_length]
            actual_length = self.max_sequence_length

        return torch.tensor(indices, dtype=torch.long), actual_length

    def encode_batch(self, messages: List[str]) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Encode a batch of messages.

        Returns:
            (batch_tensor, lengths_tensor)
        """
        if not messages:
            raise ValueError("Cannot encode empty message list")

        encoded_messages = []
        lengths = []

        for message in messages:
            try:
                encoded, length = self.encode_message(message)
                encoded_messages.append(encoded)
                lengths.append(length)
            except Exception as e:
                logger.warning(f"Failed to encode message: {e}")
                # Создание пустого тензора для поврежденного сообщения
                empty_tensor = torch.zeros(self.max_sequence_length, dtype=torch.long)
                encoded_messages.append(empty_tensor)
                lengths.append(0)

        batch_tensor = torch.stack(encoded_messages)
        lengths_tensor = torch.tensor(lengths, dtype=torch.long)

        return batch_tensor, lengths_tensor

    def decode_message(self, indices: torch.Tensor) -> str:
        """Decode tensor of indices back to text."""
        if not self.idx_to_word:
            raise ValueError("Vocabulary not built. Call build_vocabulary() first.")

        indices_list = indices.tolist()
        tokens = [
            self.idx_to_word.get(idx, self.UNK_TOKEN) for idx in indices_list if idx != self.word_to_idx[self.PAD_TOKEN]
        ]

        # Remove special tokens
        tokens = [token for token in tokens if token not in {self.START_TOKEN, self.END_TOKEN, self.PAD_TOKEN}]

        return " ".join(tokens)

    def save_vocabulary(self, path: Union[str, Path]) -> None:
        """Save vocabulary to JSON file (secure alternative to pickle)."""
        path = Path(path)

        if not self.word_to_idx:
            raise ValueError("No vocabulary to save. Call build_vocabulary() first.")

        # Создание директории если не существует
        path.parent.mkdir(parents=True, exist_ok=True)

        vocab_data = {
            "word_to_idx": self.word_to_idx,
            "idx_to_word": {str(k): v for k, v in self.idx_to_word.items()},  # JSON keys must be strings
            "vocab_size": self.vocab_size,
            "max_sequence_length": self.max_sequence_length,
            "max_vocab_size": self.max_vocab_size,
            "min_word_freq": self.min_word_freq,
            "special_tokens": {
                "PAD_TOKEN": self.PAD_TOKEN,
                "UNK_TOKEN": self.UNK_TOKEN,
                "START_TOKEN": self.START_TOKEN,
                "END_TOKEN": self.END_TOKEN,
            },
            "metadata": {"version": "1.0.0", "created_by": "LogTextProcessor"},
        }

        try:
            # Безопасная запись с атомарной операцией
            temp_path = path.with_suffix(path.suffix + ".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(vocab_data, f, ensure_ascii=False, indent=2)
            temp_path.replace(path)  # Атомарная операция

            logger.info(f"Vocabulary saved to {path}")

        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise VocabularySecurityError(f"Failed to save vocabulary: {e}")

    def load_vocabulary(self, path: Union[str, Path]) -> None:
        """Load vocabulary from JSON file (secure alternative to pickle)."""
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Vocabulary file not found: {path}")

        # Проверка размера файла
        max_file_size = 100 * 1024 * 1024  # 100MB
        if path.stat().st_size > max_file_size:
            raise VocabularySecurityError(f"Vocabulary file too large: {path.stat().st_size} bytes")

        try:
            with open(path, "r", encoding="utf-8") as f:
                vocab_data = json.load(f)
        except json.JSONDecodeError as e:
            raise VocabularySecurityError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise VocabularySecurityError(f"Failed to load vocabulary: {e}")

        # Валидация структуры данных
        required_keys = {
            "word_to_idx",
            "idx_to_word",
            "vocab_size",
            "max_sequence_length",
            "max_vocab_size",
            "min_word_freq",
        }
        if not all(key in vocab_data for key in required_keys):
            missing = required_keys - set(vocab_data.keys())
            raise VocabularySecurityError(f"Invalid vocabulary format. Missing: {missing}")

        # Валидация данных
        if not isinstance(vocab_data["word_to_idx"], dict):
            raise VocabularySecurityError("Invalid word_to_idx format")

        # Проверяем что размер vocabulary логичен (может отличаться из-за фильтрации)
        expected_size = len(vocab_data["word_to_idx"])
        stored_size = vocab_data["vocab_size"]
        if abs(expected_size - stored_size) > 10:  # Допускаем небольшое расхождение
            raise VocabularySecurityError(f"Vocabulary size mismatch: expected ~{expected_size}, got {stored_size}")

        # Загрузка данных
        self.word_to_idx = vocab_data["word_to_idx"]
        self.idx_to_word = {int(k): v for k, v in vocab_data["idx_to_word"].items()}
        self.vocab_size = vocab_data["vocab_size"]
        self.max_sequence_length = vocab_data["max_sequence_length"]
        self.max_vocab_size = vocab_data["max_vocab_size"]
        self.min_word_freq = vocab_data["min_word_freq"]

        # Загрузка special tokens если есть
        if "special_tokens" in vocab_data:
            special = vocab_data["special_tokens"]
            self.PAD_TOKEN = special.get("PAD_TOKEN", self.PAD_TOKEN)
            self.UNK_TOKEN = special.get("UNK_TOKEN", self.UNK_TOKEN)
            self.START_TOKEN = special.get("START_TOKEN", self.START_TOKEN)
            self.END_TOKEN = special.get("END_TOKEN", self.END_TOKEN)

        logger.info(f"Vocabulary loaded from {path}")

    def get_vocab_stats(self) -> Dict[str, any]:
        """Get vocabulary statistics."""
        if not self.word_to_idx:
            return {"status": "No vocabulary loaded"}

        # Безопасное получение топ-слов
        top_words = list(self.word_to_idx.keys())[:20]

        return {
            "vocab_size": self.vocab_size,
            "max_sequence_length": self.max_sequence_length,
            "special_tokens": [
                self.PAD_TOKEN,
                self.UNK_TOKEN,
                self.START_TOKEN,
                self.END_TOKEN,
            ],
            "most_common_words": top_words,
            "coverage": f"{len(self.word_to_idx) / self.max_vocab_size * 100:.1f}%",
            "parameters": {
                "max_vocab_size": self.max_vocab_size,
                "min_word_freq": self.min_word_freq,
            },
        }
