import asyncio
from dataclasses import dataclass
from typing import Optional, List, Any

from core.models.basic_models import ContractCompleteResult, RitualResult, PurchaseResult, ContractFailResult, \
    CorruptionResult
from db.database import Database
from db.character_repo import CharacterRepo
from db.status_repo import StatusRepo
from db.inventory_repo import InventoryRepo
from db.items_repo import ItemsRepo

from core.status_registry import StatusRegistry
from core.game_calculator import GameCalculator
from core.reward_manager import RewardManager


class CharacterController:
    """
    Глобальный координатор (Facade / Управленец состоянием).
    Единственный класс, имеющий право изменять данные модели (HP, XP, инвентарь).
    Не содержит в себе математики (делегирует GameCalculator) и SQL (делегирует Repo).
    """

    def __init__(self, user_id: int, db_path: str = "oskolki.db"):
        # Подключаем все репозитории для работы с разными таблицами БД
        self.db = Database(db_path)
        self.char_repo = CharacterRepo(self.db)
        self.status_repo = StatusRepo(self.db)
        self.inventory_repo = InventoryRepo(self.db)
        self.items_repo = ItemsRepo(self.db)

        # Выгружаем текущее состояние персонажа в оперативную память
        self.model = self.char_repo.get_or_create(user_id)
        self.active_statuses = self.status_repo.load_active_statuses(self.model.user_id)
        self.inventory = self.inventory_repo.get_inventory(self.model)

        # Асинхронный лок для предотвращения гонки данных (Double Click)
        self.lock = asyncio.Lock()

    async def save_all(self):
        """Сохраняет измененные модели обратно в БД."""
        self.char_repo.save(self.model)
        self.inventory_repo.save(self.inventory)

    # ==========================================
    # ИГРОВЫЕ ДЕЙСТВИЯ (Actions)
    # ==========================================

    async def perform_ritual(self) -> RitualResult:
        """Выполнение полезной привычки (Спасбросок Силы)."""
        async with self.lock:
            # 1. Запрашиваем результат броска у калькулятора (Pure Function)
            roll, is_success = GameCalculator.calculate_ritual(
                self.model, self.active_statuses, adv=False, disadv=False
            )

            # 2. Списываем длительность баффа Силы (если таковой был на персонаже)
            self._consume_buff_for_stat("STR")

            # 3. Применяем результаты к персонажу
            received_buff = None
            if is_success:
                duration = 48 if roll.is_crit_success else 24
                # Выдача награды делегирована RewardManager
                buffs = RewardManager.grant_random_status(self, "buff", count=1, duration=duration)
                received_buff = buffs[0] if buffs else None

            await self.save_all()
            return RitualResult(roll=roll, is_success=is_success, new_buff=received_buff)

    async def succumb_to_corruption(self) -> CorruptionResult:
        """Срыв на вредную привычку (Спасбросок Выносливости)."""
        async with self.lock:
            roll, _, diseases_count = GameCalculator.calculate_corruption(
                self.model, self.active_statuses, adv=False, disadv=False
            )

            self._consume_buff_for_stat("CON")

            # Выдаем случайные болезни (урон отключен по балансу)
            received_diseases = RewardManager.grant_random_status(self, "disease", count=diseases_count)

            await self.save_all()
            return CorruptionResult(roll=roll, is_fail=diseases_count > 0, damage=0, new_diseases=received_diseases)

    async def complete_contract(self, difficulty: str, duration: str) -> ContractCompleteResult:
        """Успешное выполнение задачи из ToDo-листа."""
        async with self.lock:
            # Расчет наград (XP, Золото и Тир лута на основе 3 бросков)
            calc = GameCalculator.calculate_contract_success(
                self.model, self.active_statuses, difficulty, duration, {}, {}
            )

            # Списываем баффы, примененные для этих 3 бросков
            self._consume_buff_for_stat("WIS")
            self._consume_buff_for_stat("CHA")
            self._consume_buff_for_stat("INT")

            # Применяем ресурсы к модели
            self._add_xp(calc.xp_gained)
            self._add_gold(calc.gold_gained)

            # Выдаем динамический лут в зависимости от тира (который определил Интеллект)
            found_items = RewardManager.grant_tiered_loot(self, calc.loot_tier, count=1)

            await self.save_all()
            return ContractCompleteResult(
                xp_gained=calc.xp_gained,
                gold_gained=calc.gold_gained,
                items_found=found_items,
                wis_roll=calc.wis_roll,
                cha_roll=calc.cha_roll,
                int_roll=calc.int_roll
            )

    async def fail_contract(self) -> ContractFailResult:
        """Провал дедлайна по задаче."""
        async with self.lock:
            roll, _, injuries_count = GameCalculator.calculate_contract_fail(
                self.model, self.active_statuses, adv=False, disadv=False
            )

            self._consume_buff_for_stat("DEX")
            received_injuries = RewardManager.grant_random_status(self, "injury", count=injuries_count)

            await self.save_all()
            return ContractFailResult(hp_lost=0, is_crit_fail=roll.is_crit_fail, new_injuries=received_injuries,
                                      dex_roll=roll)

    async def process_daily_midnight(self, active_contracts_count: int = 0):
        """Ежедневное обновление (пассивный урон отключен)."""
        async with self.lock:
            await self.save_all()

    # ==========================================
    # СИСТЕМНЫЕ МЕТОДЫ ИЗМЕНЕНИЯ СОСТОЯНИЯ (Инкапсуляция)
    # ==========================================

    def _modify_hp(self, amount: int):
        """Изменяет здоровье (может быть как исцелением, так и уроном)."""
        # Убрана блокировка (if amount < 0: amount = 0)
        self.model.hp = max(0, min(self.model.max_hp, self.model.hp + amount))

    def _add_xp(self, amount: int):
        """Начисляет опыт и проверяет повышение уровня по правилам D&D."""
        self.model.xp += amount
        old_level = self.model.level
        # Запрашиваем факт повышения уровня у калькулятора
        new_level, leveled_up = GameCalculator.check_level_up(old_level, self.model.xp)

        if leveled_up:
            for _ in range(new_level - old_level):
                # +6 HP + модификатор Телосложения за каждый новый уровень
                _, con_mod = GameCalculator.calculate_stat_modifier(self.model.stats.get("CON", 10), 0)
                self.model.max_hp += max(1, 6 + con_mod)
            self.model.level = new_level
            self.model.hp = self.model.max_hp  # Восстановление ХП при левелапе

    def _add_gold(self, amount: int):
        self.model.gold = max(0, self.model.gold + amount)

    def _give_item(self, item_name: str, quantity: int = 1):
        self.inventory.add_item(item_name, quantity)

    # ==========================================
    # МЕНЕДЖМЕНТ СТАТУСОВ
    # ==========================================

    def _apply_status(self, unique_name: str, duration_hours: int = None) -> bool:
        """
        Добавляет новый статус или стакает время у существующего.
        Вся логика стакания перенесена внутрь StatusRepo.
        """
        template = StatusRegistry.get(unique_name)
        if not template:
            return False

        # StatusRepo.add_status сам сделает UPDATE expires_at, если статус уже существует
        self.status_repo.add_status(self.model.user_id, unique_name, template.type, duration_hours)
        self.active_statuses = self.status_repo.load_active_statuses(self.model.user_id)
        return True

    def _remove_status(self, unique_name: str):
        self.status_repo.remove_status(self.model.user_id, unique_name)
        self.active_statuses = self.status_repo.load_active_statuses(self.model.user_id)

    def _consume_buff_for_stat(self, stat_key: str):
        """
        Проверяет, дал ли бафф бонус к указанной характеристике при броске.
        Если да, списывает 24 часа его длительности через БД.
        """
        for s in self.active_statuses:
            # Поддержка доступа как к словарю (s["name"]), так и к объекту (s.name)
            name_key = s.name if hasattr(s, 'name') else s["name"]
            template = StatusRegistry.get(name_key)

            if template and template.type == "buff" and hasattr(template, "effects"):
                if template.effects.get(f"ROLL_BONUS_{stat_key}"):
                    self.status_repo.reduce_duration(self.model.user_id, name_key, 24)
                    self.active_statuses = self.status_repo.load_active_statuses(self.model.user_id)
                    break  # Списываем только один бафф за бросок

    # ==========================================
    # МАГАЗИН И ПРЕДМЕТЫ
    # ==========================================

    def get_shop_items(self) -> List[Any]:
        """Возвращает все товары из БД через репозиторий."""
        return self.items_repo.get_all_shop_items()

    async def buy_item(self, item_id: str) -> PurchaseResult:
        """Покупает предмет: списывает золото, добавляет в инвентарь."""
        async with self.lock:
            item = self.items_repo.get_item_by_id(item_id)

            if not item:
                return PurchaseResult(success=False, error="Предмет не найден в лавке.")

            # Калькулятор проверяет математику покупки (хватает ли денег)
            price = item.price if hasattr(item, 'price') else item['price']
            name_text = item.name_text if hasattr(item, 'name_text') else item['name_text']

            success, gold_to_spend = GameCalculator.calculate_purchase(self.model.gold, price)

            if not success:
                return PurchaseResult(success=False, error=f"Недостаточно золота. Требуется: {price} 🌕")

            self._add_gold(-gold_to_spend)
            self._give_item(name_text, 1)

            await self.save_all()
            return PurchaseResult(success=True, item_name=name_text, spent=gold_to_spend)

    async def sell_item(self, item_id: str) -> dict:
        """Продажа предмета за 50% от его стоимости."""
        async with self.lock:
            # Получаем инфу из БД
            item_def = self.items_repo.get_item_by_id(item_id)
            if not item_def:
                return {"success": False, "message": "Предмет не опознан."}

            price = item_def.price if hasattr(item_def, 'price') else item_def['price']
            name_text = item_def.name_text if hasattr(item_def, 'name_text') else item_def['name_text']

            # Проверяем наличие именно по РУССКОМУ названию
            inv_items = self.inventory.items if isinstance(self.inventory.items, dict) else (
                        self.inventory.get_items() or {})
            if inv_items.get(name_text, 0) <= 0:
                return {"success": False, "message": "Этого предмета нет в инвентаре."}

            sell_price = max(1, price // 2)

            # Удаляем 1 предмет и даем золото
            self._give_item(name_text, -1)
            self._add_gold(sell_price)
            await self.save_all()

            return {"success": True, "message": f"Вы продали {name_text} за {sell_price} 🌕."}

    async def use_potion(self, item_id: str) -> dict:
        """Использование зелий лечения и очищения."""
        async with self.lock:
            item_def = self.items_repo.get_item_by_id(item_id)
            if not item_def:
                return {"success": False, "message": "Зелье не опознано."}

            name_text = item_def.name_text if hasattr(item_def, 'name_text') else item_def['name_text']

            inv_items = self.inventory.items if isinstance(self.inventory.items, dict) else (
                        self.inventory.get_items() or {})
            if inv_items.get(name_text, 0) <= 0:
                return {"success": False, "message": "Этого зелья нет в инвентаре."}

            msg = ""
            if item_id == "healing_potion":
                heal, _ = RewardManager.use_healing_potion(self)
                msg = f"Вы выпили зелье и восстановили {heal} HP! ❤️"
            elif item_id == "cure_disease_potion":
                cured = RewardManager.use_cure_disease_potion(self)
                if cured:
                    msg = f"Очищение сработало. Вы излечились от: {cured} ✨"
                else:
                    msg = "Вы были абсолютно здоровы. Зелье потрачено впустую 💨"
            else:
                return {"success": False, "message": "Этот предмет нельзя использовать."}

            self._give_item(name_text, -1)
            await self.save_all()
            return {"success": True, "message": msg}