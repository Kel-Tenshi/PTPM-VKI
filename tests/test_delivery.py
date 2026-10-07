import unittest
from src.delivery_service import calculate_delivery_cost


class TestDeliveryService(unittest.TestCase):

    # ====================================================
    # Группа 1: Базовые расчеты стандартной доставки (ok)
    # ====================================================

    def test_standard_delivery_small_package_within_500km(self):
        cost, date = calculate_delivery_cost(2.0, 300, "обычный", is_express=False)
        self.assertEqual(cost, 1700)
        self.assertEqual(date, "2026-09-04")

    def test_standard_delivery_medium_weight_tier_ten_kg(self):
        cost, date = calculate_delivery_cost(10.0, 400, "обычный", is_express=False)
        self.assertEqual(cost, 2640)
        self.assertEqual(date, "2026-09-04")

    def test_standard_delivery_heavy_weight_tier_twenty_five_kg(self):
        cost, date = calculate_delivery_cost(25.0, 600, "обычный", is_express=False)
        self.assertEqual(cost, 4800)
        self.assertEqual(date, "2026-09-04")

    def test_standard_delivery_fragile_package_surcharge(self):
        cost, date = calculate_delivery_cost(3.0, 200, "хрупкий", is_express=False)
        self.assertEqual(cost, 1500)
        self.assertEqual(date, "2026-09-04")

    def test_standard_delivery_hazardous_package_surcharge(self):
        cost, date = calculate_delivery_cost(3.0, 200, "опасный", is_express=False)
        self.assertEqual(cost, 2200)
        self.assertEqual(date, "2026-09-04")

    def test_delivery_duration_calculation_long_distance(self):
        cost, date = calculate_delivery_cost(2.0, 1500, "обычный", is_express=False)
        self.assertEqual(date, "2026-09-06")

    # ====================================================
    # Группа 2: Граничные допустимые значения (ok)
    # ====================================================

    def test_boundary_minimum_allowed_weight(self):
        cost, date = calculate_delivery_cost(0.1, 100, "обычный")
        self.assertNotEqual(cost, -1)
        self.assertNotEqual(date, "0000-00-00")

    def test_boundary_maximum_allowed_weight(self):
        cost, date = calculate_delivery_cost(50.0, 100, "обычный")
        self.assertNotEqual(cost, -1)
        self.assertNotEqual(date, "0000-00-00")

    def test_boundary_minimum_allowed_distance(self):
        cost, date = calculate_delivery_cost(1.0, 1, "обычный")
        self.assertNotEqual(cost, -1)
        self.assertNotEqual(date, "0000-00-00")

    def test_boundary_maximum_allowed_distance(self):
        cost, date = calculate_delivery_cost(1.0, 5000, "обычный")
        self.assertNotEqual(cost, -1)
        self.assertNotEqual(date, "0000-00-00")

    # ====================================================
    # Группа 3: Негативные тесты и ограничения (ok)
    # ====================================================

    def test_invalid_weight_below_minimum_boundary(self):
        cost, date = calculate_delivery_cost(0.05, 100, "обычный")
        self.assertEqual(cost, -1)
        self.assertEqual(date, "0000-00-00")

    def test_invalid_weight_negative_value(self):
        cost, date = calculate_delivery_cost(-5.0, 100, "обычный")
        self.assertEqual(cost, -1)
        self.assertEqual(date, "0000-00-00")

    def test_invalid_weight_exceeds_maximum_boundary(self):
        cost, date = calculate_delivery_cost(50.1, 100, "обычный")
        self.assertEqual(cost, -1)
        self.assertEqual(date, "0000-00-00")

    def test_invalid_distance_zero_value(self):
        cost, date = calculate_delivery_cost(2.0, 0, "обычный")
        self.assertEqual(cost, -1)
        self.assertEqual(date, "0000-00-00")

    def test_invalid_distance_negative_value(self):
        cost, date = calculate_delivery_cost(2.0, -100, "обычный")
        self.assertEqual(cost, -1)
        self.assertEqual(date, "0000-00-00")

    def test_invalid_distance_exceeds_maximum_boundary(self):
        cost, date = calculate_delivery_cost(2.0, 5001, "обычный")
        self.assertEqual(cost, -1)
        self.assertEqual(date, "0000-00-00")

    def test_invalid_package_type_unsupported_string(self):
        cost, date = calculate_delivery_cost(2.0, 100, "секретный")
        self.assertEqual(cost, -1)
        self.assertEqual(date, "0000-00-00")

    def test_invalid_package_type_empty_string(self):
        cost, date = calculate_delivery_cost(2.0, 100, "")
        self.assertEqual(cost, -1)
        self.assertEqual(date, "0000-00-00")

    # =========================================================================
    # Группа 4: Тесты выявления дефектов логики (УПАДУТ С FAIL НА delivery.py)
    # =========================================================================

    def test_express_delivery_must_have_surcharge_not_discount(self):
        """
        FAIL: Экспресс-доставка должна стоить дороже обычной.
        Базовая стоимость для 2кг, 200км = 1200 руб.
        Код delivery.py делает скидку 50% (* 0.5) и возвращает 600 руб вместо наценки.
        """
        cost, _ = calculate_delivery_cost(2.0, 200, "обычный", is_express=True)
        self.assertGreaterEqual(
            cost, 1200, f"Экспресс-доставка сделала посылку дешевле базовой стоимости ({cost} < 1200)!"
        )

    def test_express_delivery_duration_minimum_one_day(self):
        """
        FAIL: Доставка не может занимать 0 дней.
        Для дистанции 300 км целочисленное деление 1 // 2 дает 0 дней, посылка прибывает 2026-09-03.
        Ожидается минимум 1 рабочий день -> 2026-09-04.
        """
        _, date = calculate_delivery_cost(2.0, 300, "обычный", is_express=True)
        self.assertNotEqual(date, "2026-09-03", "Экспресс-доставка рассчитала срок в 0 дней (мгновенно)!")
        self.assertEqual(date, "2026-09-04")

    def test_boundary_weight_exactly_five_kg_tier_inclusion(self):
        """
        FAIL: Категория 'от 5 до 20 кг' должна включать ровно 5.0 кг (коэффициент 1.2).
        Стоимость: (200 + 100*5) * 1.2 = 840 руб.
        Код использует строгое неравенство weight > 5.0, поэтому 5.0 кг считается без надбавки (700 руб).
        """
        cost, _ = calculate_delivery_cost(5.0, 100, "обычный", is_express=False)
        self.assertEqual(
            cost, 840, f"Ожидалась наценка за весовую категорию 'от 5 кг', но получено {cost}"
        )

    def test_package_type_case_insensitive_handling(self):
        """
        FAIL: Служба доставки должна принимать тип груза без учета регистра (например, 'Обычный').
        Код возвращает ошибку (-1, '0000-00-00'), так как не нормализует строку.
        """
        cost, date = calculate_delivery_cost(2.0, 100, "Обычный", is_express=False)
        self.assertNotEqual(cost, -1, "Код отклонил валидный тип груза, переданный с заглавной буквы")
        self.assertNotEqual(date, "0000-00-00")


if __name__ == "__main__":
    unittest.main()