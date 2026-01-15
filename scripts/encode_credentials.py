"""
Скрипт для кодирования Google Service Account JSON в base64.
Упрощает настройку credentials для .env файла.
"""

import base64
import json
import sys
from pathlib import Path


def print_usage():
    """Выводит справку по использованию."""
    print("📦 Кодировщик Google Service Account JSON в Base64")
    print("\nИспользование:")
    print("  python encode_credentials.py <путь_к_json_файлу>")
    print("\nПримеры:")
    print("  python encode_credentials.py credentials/service-account.json")
    print(
        "  python encode_credentials.py ~/Downloads/my-project-credentials.json"
    )
    print("\nКак получить JSON файл:")
    print("  1. Перейдите в Google Cloud Console")
    print("  2. Создайте Service Account")
    print("  3. Скачайте JSON ключ")
    print("\nПосле кодирования добавьте вывод в .env файл:")
    print("  GOOGLE_CREDENTIALS_BASE64=ваша_base64_строка")


def validate_json(data: dict) -> bool:
    """Проверяет, что JSON является валидным сервисным аккаунтом."""
    required_fields = [
        "type",
        "project_id",
        "private_key_id",
        "private_key",
        "client_email",
        "client_id",
    ]

    # Проверяем наличие обязательных полей
    for field in required_fields:
        if field not in data:
            print(f"❌ Отсутствует обязательное поле: {field}")
            return False

    # Проверяем тип
    if data.get("type") != "service_account":
        print(
            f"❌ Неверный тип: {data.get('type')} (ожидается 'service_account')"
        )
        return False

    return True


def main():
    """Основная функция скрипта."""
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)

    json_path = Path(sys.argv[1])

    # Проверяем существование файла
    if not json_path.exists():
        print(f"❌ Файл не найден: {json_path}")
        print(f"   Проверьте путь к файлу")
        sys.exit(1)

    # Проверяем расширение
    if json_path.suffix.lower() != ".json":
        print(
            f"⚠️  Предупреждение: файл имеет расширение {json_path.suffix}, ожидается .json"
        )

    try:
        # Читаем и парсим JSON
        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        # Валидируем JSON
        if not validate_json(json_data):
            print("\n❌ Файл не является валидным Google Service Account JSON")
            sys.exit(1)

        # Преобразуем JSON в строку (минифицированную)
        json_str = json.dumps(json_data, separators=(",", ":"))

        # Кодируем в base64
        base64_str = base64.b64encode(json_str.encode("utf-8")).decode("ascii")

        # Выводим результат
        print("\n" + "=" * 70)
        print("✅ GOOGLE_CREDENTIALS_BASE64 успешно сгенерирован!")
        print("=" * 70)

        print(f"\n📋 Информация о Service Account:")
        print(f"   Project: {json_data.get('project_id', 'Не указан')}")
        print(f"   Client Email: {json_data.get('client_email', 'Не указан')}")
        print(
            f"   Key ID: {json_data.get('private_key_id', 'Не указан')[:20]}..."
        )

        print(f"\n📏 Длина Base64 строки: {len(base64_str)} символов")

        print("\n🔐 Base64 строка для .env файла:")
        print("-" * 70)
        print(base64_str)
        print("-" * 70)

        print("\n📝 Инструкция по добавлению в .env:")
        print("1. Откройте .env файл в редакторе")
        print("2. Найдите строку GOOGLE_CREDENTIALS_BASE64=")
        print("3. Замените значение на строку выше")
        print("4. Сохраните файл")

        print("\n✨ Пример строки в .env:")
        print(f'GOOGLE_CREDENTIALS_BASE64="{base64_str}"')

        # Проверка декодирования
        print("\n🧪 Проверка декодирования...")
        try:
            decoded = base64.b64decode(base64_str).decode("utf-8")
            decoded_json = json.loads(decoded)
            print("✅ Base64 успешно декодируется в валидный JSON")
        except Exception as e:
            print(f"❌ Ошибка при проверке: {e}")

        print("\n" + "=" * 70)

    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        print("   Убедитесь, что файл содержит валидный JSON")
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"❌ Ошибка кодирования файла")
        print("   Убедитесь, что файл в кодировке UTF-8")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
