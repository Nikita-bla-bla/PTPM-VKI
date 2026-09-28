import os
import sys
import math
import logging
from typing import List, Tuple, Optional

#НАСТРОЙКА ЛОГИРОВАНИЯ
def setup_logger(name: str = "triangle_app") -> logging.Logger:
    """Настраивает логгер: пишет в файл logs/app.log и в консоль (stdout)."""
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Чтобы обработчики не дублировались при повторном вызове
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Запись в файл
    file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Вывод в консоль — в stdout, чтобы порядок совпадал с print/input
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


logger = setup_logger()


#КОНСТАНТЫ РЕЗУЛЬТАТОВ
# Координаты при ошибочных числовых данных (не треугольник)
COORDS_ERROR = [(-1, -1)] * 3
# Координаты при нечисловых данных
COORDS_INVALID = [(-2, -2)] * 3


#РАЗБОР ВХОДНЫХ ДАННЫХ
def parse_side(value: str) -> Optional[float]:
    """
    Преобразует строку в положительное вещественное число.
    Возвращает None, если значение невалидно.
    """
    try:
        number = float(value.strip())
    except (ValueError, AttributeError):
        return None
    if number <= 0:
        return None
    return number



#РАСЧЁТ КООРДИНАТ ВЕРШИН
def _fit_to_field(coords: List[Tuple[float, float]], size: int = 100) -> List[Tuple[int, int]]:
    """
    Смещает и, при необходимости, масштабирует координаты так,
    чтобы фигура попала в поле size x size пикселей.
    """
    margin = 10  # отступ от края
    xs = [p[0] for p in coords]
    ys = [p[1] for p in coords]
    min_x, min_y = min(xs), min(ys)

    # Сдвигаем фигуру в положительную область с отступом
    shifted = [
        (x - min_x + margin, y - min_y + margin)
        for x, y in coords
    ]

    # Если фигура не помещается — масштабируем
    max_coord = max(max(p[0] for p in shifted), max(p[1] for p in shifted))
    limit = size - margin
    if max_coord > limit:
        scale = limit / max_coord
        shifted = [(x * scale, y * scale) for x, y in shifted]

    # Округляем до int
    return [(int(round(x)), int(round(y))) for x, y in shifted]


def compute_vertices(a: float, b: float, c: float) -> List[Tuple[int, int]]:
    """
    Вычисляет координаты трёх вершин треугольника со сторонами a, b, c.
    A = (0,0), B = (c,0), C — по теореме косинусов.
    """
    ax, ay = 0.0, 0.0
    bx, by = c, 0.0

    # Угол при вершине A
    cos_a = (a * a + c * c - b * b) / (2 * a * c)
    # Защита от числовой погрешности
    cos_a = max(-1.0, min(1.0, cos_a))

    cx = a * cos_a
    cy = a * math.sin(math.acos(cos_a))

    return _fit_to_field([(ax, ay), (bx, by), (cx, cy)])



#                    ОСНОВНАЯ ЛОГИКА
def classify_triangle(s1: str, s2: str, s3: str) -> Tuple[str, List[Tuple[int, int]]]:
    """
    Основная функция. Принимает три строки со сторонами.
    Возвращает (тип треугольника, координаты вершин).
    """
    a = parse_side(s1)
    b = parse_side(s2)
    c = parse_side(s3)

    # 1. Нечисловые данные
    if a is None or b is None or c is None:
        logger.warning("Обнаружены нечисловые данные: %r, %r, %r", s1, s2, s3)
        return "", COORDS_INVALID

    # 2. Не выполняется неравенство треугольника
    if a + b <= c or a + c <= b or b + c <= a:
        logger.info("Неравенство треугольника нарушено: a=%s, b=%s, c=%s", a, b, c)
        return "не треугольник", COORDS_ERROR

    # 3. Определяем вид треугольника
    eps = 1e-9  # допуск для сравнения float
    equal_ab = math.isclose(a, b, rel_tol=eps, abs_tol=eps)
    equal_bc = math.isclose(b, c, rel_tol=eps, abs_tol=eps)
    equal_ac = math.isclose(a, c, rel_tol=eps, abs_tol=eps)

    if equal_ab and equal_bc:
        kind = "равносторонний"
    elif equal_ab or equal_bc or equal_ac:
        kind = "равнобедренный"
    else:
        kind = "разносторонний"

    coords = compute_vertices(a, b, c)
    return kind, coords



#                       ТОЧКА ВХОДА
def main() -> None:
    # Самый первый лог
    logger.info("Программа запущена")

    try:
        line1 = input("Введите длину стороны A: ")
        line2 = input("Введите длину стороны B: ")
        line3 = input("Введите длину стороны C: ")
    except EOFError:
        logger.error("Входные данные не получены (EOF)")
        sys.exit(1)

    logger.debug("Входные строки: %r, %r, %r", line1, line2, line3)

    triangle_type, coords = classify_triangle(line1, line2, line3)

    # Вывод результата
    print("Тип треугольника:", triangle_type if triangle_type else "(пусто)")
    print("Координаты вершин:", coords)

    logger.info("Результат: тип=%r, координаты=%s", triangle_type, coords)


if __name__ == "__main__":
    main()