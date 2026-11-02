import unittest
from src.utils.base62 import encode_base62, BASE62_ALPHABET


class TestEncodeBase62(unittest.TestCase):

    def test_encode_zero(self):
        """Тест кодирования нуля"""
        self.assertEqual(encode_base62(0), BASE62_ALPHABET[0])

    def test_encode_small_numbers(self):
        """Тест кодирования небольших чисел"""
        # 1 -> '1' , 10 -> 'A', (Так как 0-9 это цифры, 10-35 это буквы в верхнем регистре)
        self.assertEqual(encode_base62(1), "1")
        self.assertEqual(encode_base62(9), "9")
        self.assertEqual(encode_base62(10), "A")
        self.assertEqual(encode_base62(35), "Z")

    def test_encode_large_number(self):
        """Тест кодирования большого числа"""
        # Проверяем, что число > 62 дает строку длиннее 1 символа
        self.assertEqual(encode_base62(62), "10")
        self.assertEqual(encode_base62(63), "11")

        # Проверяем конкретное большое число
        large_num = 1234567890
        result = encode_base62(large_num)

        # Можно проверить, что результат состоит только из символов алфавита
        self.assertTrue(all(char in BASE62_ALPHABET for char in result))

        # Проверим длину или просто факт успешного выполнения
        self.assertIsInstance(result, str)

    def test_encode_max_length_for_small_base(self):
        """Проверка на корректность символов"""
        # Генерируем число, которое должно начинаться с последнего символа
        # 62^2 - 1 = 3843. 3843 в base62 должно быть 'zz' (если считать что z=61)
        # Проверим явно:
        # BASE62: 0-9 (0-10), A-Z(10-35) a-z(36-61)
        # 61 -> 'z'
        self.assertEqual(encode_base62(61), "z")
        # 62*36 + 61 = 2293. Это должно быть 'az'
        # 2293 // 62 = 36 (индекс буквы 'a'), 2293 % 62 = 61 (индекс буквы 'z')
        # Значит 2293 -> 'az'? Нет, порядок при divmod справа налево.
        # 2293 % 62 = 61 -> 'z'
        # 36 % 62 = 36 -> 'a'
        # Итого 'az'
        self.assertEqual(encode_base62(2293), "az")
