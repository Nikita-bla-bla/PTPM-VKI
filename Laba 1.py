import os
import sys
import math
import logging
from logging.handlers import RotatingFileHandler
from typing import List, Tuple, Optional


# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---

def setup_logging():
    """
    Настраивает логирование: консоль (INFO+) и файл (DEBUG+ с ротацией).
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "app.log")

    logger = logging.getLogger()
    # Очищаем хендлеры, если функция вызывается повторно (хотя здесь она вызывается один раз)
    if logger.handlers:
        logger.handlers.clear()

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | [%(levelname)-7s] | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logging()

COORDS_ERROR = [(-1, -1)] * 3
COORDS_INVALID = [(-2, -2)] * 3


def parse_side(value: str) -> Optional[float]:
    try:
        number = float(value.strip())
    except (ValueError, AttributeError):
        return None

    if math.isnan(number) or math.isinf(number) or number <= 0:
        return None

    return number


def _fit_to_field(coords: List[Tuple[float, float]], size: int = 100) -> List[Tuple[int, int]]:
    margin = 10
    if not coords:
        return []

    xs = [p[0] for p in coords]
    ys = [p[1] for p in coords]
    min_x, min_y = min(xs), min(ys)

    shifted = [
        (x - min_x + margin, y - min_y + margin)
        for x, y in coords
    ]

    max_coord_val = max(max(p[0] for p in shifted), max(p[1] for p in shifted))
    limit = size - margin

    if max_coord_val > limit and max_coord_val > 0:
        scale = limit / max_coord_val
        shifted = [(x * scale, y * scale) for x, y in shifted]
        logger.debug("Применено масштабирование: scale=%.4f", scale)

    return [(int(round(x)), int(round(y))) for x, y in shifted]


def compute_vertices(a: float, b: float, c: float) -> List[Tuple[int, int]]:
    logger.debug("Вычисление координат для сторон: a=%s, b=%s, c=%s", a, b, c)

    ax, ay = 0.0, 0.0
    bx, by = c, 0.0

    denominator = 2 * b * c
    if denominator == 0:
        return [(0, 0), (0, 0), (0, 0)]

    cos_a = (b * b + c * c - a * a) / denominator
    cos_a = max(-1.0, min(1.0, cos_a))

    angle_a = math.acos(cos_a)
    cx = b * cos_a
    cy = b * math.sin(angle_a)

    logger.debug("Raw coords: A(0,0), B(%s,0), C(%s, %s)", c, cx, cy)

    return _fit_to_field([(ax, ay), (bx, by), (cx, cy)])


def classify_triangle(s1: str, s2: str, s3: str) -> Tuple[str, List[Tuple[int, int]]]:
    a = parse_side(s1)
    b = parse_side(s2)
    c = parse_side(s3)

    if a is None or b is None or c is None:
        logger.warning("Обнаружены нечисловые или недопустимые данные: '%s', '%s', '%s'", s1, s2, s3)
        return "", COORDS_INVALID

    logger.debug("Распарсенные стороны: a=%s, b=%s, c=%s", a, b, c)

    sides = sorted([a, b, c])
    if sides[0] + sides[1] <= sides[2]:
        logger.info("Неравенство треугольника нарушено: %s + %s <= %s", sides[0], sides[1], sides[2])
        return "не треугольник", COORDS_ERROR

    eps = 1e-9
    equal_ab = math.isclose(a, b, rel_tol=eps, abs_tol=eps)
    equal_bc = math.isclose(b, c, rel_tol=eps, abs_tol=eps)
    equal_ac = math.isclose(a, c, rel_tol=eps, abs_tol=eps)

    if equal_ab and equal_bc:
        kind = "равносторонний"
    elif equal_ab or equal_bc or equal_ac:
        kind = "равнобедренный"
    else:
        kind = "разносторонний"

    logger.info("Определен тип треугольника: %s", kind)

    coords = compute_vertices(a, b, c)
    return kind, coords


# ОСНОВНАЯ ЛОГИКА С ЦИКЛОМ
def main() -> None:
    logger.info("Программа запущена в циклическом режиме")
    print("=" * 30)
    print("Калькулятор треугольников")
    print("Для выхода введите 'exit' или нажмите Ctrl+C")
    print("=" * 30)

    while True:
        try:
            line1 = input("\nВведите длину стороны A (или 'exit'): ")

            # Проверка на выход
            if line1.strip().lower() in ['exit', 'quit', 'выход']:
                logger.info("Пользователь запросил выход из программы")
                print("До свидания!")
                break

            line2 = input("Введите длину стороны B: ")
            line3 = input("Введите длину стороны C: ")

        except EOFError:
            # Если ввод перенаправлен из файла и он закончился
            logger.info("Конец входного потока (EOF). Завершение работы.")
            break
        except KeyboardInterrupt:
            # Обработка Ctrl+C
            logger.info("Получен сигнал прерывания (Ctrl+C). Завершение работы.")
            print("\nПрограмма остановлена пользователем.")
            break

        logger.debug("Получены входные строки: %r, %r, %r", line1, line2, line3)

        triangle_type, coords = classify_triangle(line1, line2, line3)

        # Вывод результата пользователю
        print("-" * 30)
        if triangle_type:
            print(f"Тип треугольника: {triangle_type}")
        else:
            print("Тип треугольника: (ошибка ввода)")

        print(f"Координаты вершин: {coords}")
        print("-" * 30)

        logger.info("Цикл завершен. Результат: тип=%r", triangle_type)


if __name__ == "__main__":
    main()