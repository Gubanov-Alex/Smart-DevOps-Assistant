"""
Автоматическое исправление проблем безопасности в коде
"""

import os
import re
import shutil
from pathlib import Path


def backup_file(file_path: Path) -> Path:
    """Создает backup файла."""
    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path


def fix_base_model_pytorch_loading():
    """Исправляет проблему с PyTorch 2.7 weights_only."""
    base_model_path = Path("app/infrastructure/ml/models/base.py")
    
    if not base_model_path.exists():
        print(f"❌ File not found: {base_model_path}")
        return
    
    backup_file(base_model_path)
    
    content = base_model_path.read_text()
    
    # Если уже исправлено, пропускаем
    if "safe_globals" in content:
        print("✅ PyTorch loading already fixed in base.py")
        return
    
    # Ищем и заменяем torch.load
    old_pattern = r'checkpoint = torch\.load\(\s*path,\s*map_location="cpu",\s*weights_only=True[^)]*\)'
    
    new_code = '''# Безопасная загрузка только весов модели с PyTorch 2.7+ compatibility
            with torch.serialization.safe_globals([torch.torch_version.TorchVersion]):
                checkpoint = torch.load(
                    path, 
                    map_location="cpu",
                    weights_only=True  # Критически важно для безопасности!
                )'''
    
    content = re.sub(old_pattern, new_code, content, flags=re.MULTILINE)
    base_model_path.write_text(content)
    print("✅ Fixed PyTorch loading in base.py")


def fix_text_processor_cleaning():
    """Исправляет проблемы с очисткой текста."""
    text_processor_path = Path("app/infrastructure/ml/preprocessing/text_processor.py")
    
    if not text_processor_path.exists():
        print(f"❌ File not found: {text_processor_path}")
        return
    
    backup_file(text_processor_path)
    
    content = text_processor_path.read_text()
    
    # Добавляем import re если его нет
    if "import re" not in content:
        content = content.replace("import logging", "import logging\nimport re")
    
    # Проверяем, уже ли исправлено
    if "dangerous_patterns" in content:
        print("✅ Text cleaning already enhanced")
        return
    
    # Находим функцию clean_log_message и заменяем её содержимое
    start_marker = "def clean_log_message(self, message: str) -> str:"
    end_marker = "return message"
    
    if start_marker in content:
        # Находим начало и конец функции
        start_idx = content.find(start_marker)
        if start_idx != -1:
            # Ищем следующий return message
            temp_content = content[start_idx:]
            end_idx = temp_content.find("return message")
            if end_idx != -1:
                end_idx += start_idx + len("return message")
                
                # Новая реализация функции
                new_function = '''def clean_log_message(self, message: str) -> str:
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
            r'<script[^>]*>.*?</script>',
            r'<script[^>]*>',
            r'</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'<iframe[^>]*>',
            r'</iframe>',
            
            # JavaScript patterns
            r'javascript\s*:',
            r'data\s*:\s*text/html',
            r'vbscript\s*:',
            
            # Dangerous function calls
            r'eval\s*(',
            r'exec\s*(',
            r'__import__\s*(',
            r'compile\s*(',
            r'execfile\s*(',
            
            # SQL injection patterns
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+.*\s+set',
            r'select\s+.*\s+from',
            r'union\s+select',
            r'--\s*',
            r'/\\*.*?\\*/',
            
            # Path traversal
            r'..\/',
            r'..\\\\\\\\'  ,
            r'file\s*://',
            r'ftp\s*://',
            
            # Log4j and other injection
            r'\\${[^}]*}',
            r'%{[^}]*}',
            
            # Command injection
            r'`[^`]*`',
            r'\\$([^)]*)',
            r'&&',
            r'\\|\\|',
            r';\s*rm',
            r';\s*cat',
            r';\s*ls',
            r';\s*echo',
        ]
        
        # Применяем все паттерны для удаления опасного контента
        for pattern in dangerous_patterns:
            message = re.sub(pattern, ' ', message, flags=re.IGNORECASE)

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
        final_dangerous = ["script", "javascript", "eval", "exec", "import", "drop table", "select", "$", "%"]
        for danger in final_dangerous:
            if danger in message:
                message = message.replace(danger, " ")

        # Normalize whitespace again after final cleaning
        message = " ".join(message.split())

        return message'''
                
                # Заменяем старую функцию на новую
                content = content[:start_idx] + new_function + content[end_idx:]
                text_processor_path.write_text(content)
                print("✅ Fixed text cleaning in text_processor.py")


def remove_unused_imports():
    """Удаляет неиспользуемые импорты из тестов."""
    test_file = Path("tests/test_security.py")
    
    if test_file.exists():
        content = test_file.read_text()
        
        # Удаляем неиспользуемый import tempfile
        if "import tempfile" in content and "tempfile" not in content.replace("import tempfile", ""):
            content = content.replace("import tempfile\n", "")
            
        # Заменяем bare except на конкретные исключения
        content = re.sub(r'except\s*:', 'except Exception:', content)
        
        test_file.write_text(content)
        print("✅ Fixed imports and except clauses in tests")


def main():
    """Основная функция исправления."""
    print("🔧 Автоматическое исправление проблем безопасности...")
    print("=" * 55)
    
    try:
        fix_base_model_pytorch_loading()
        fix_text_processor_cleaning()
        remove_unused_imports()
        
        print("\n✅ Все исправления применены!")
        print("\n🧪 Теперь запустите тесты:")
        print("make test-security")
        print("\n🔒 И проверьте безопасность:")
        print("make security")
        
    except Exception as e:
        print(f"❌ Ошибка при исправлении: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
