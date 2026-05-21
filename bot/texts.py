import datetime


class Texts:
    """
    Класс-генератор всех текстов и интерфейсов бота.
    Отвечает исключительно за визуальное представление данных (View).
    Не содержит игровой логики или расчетов.
    """

    # === Статические тексты и кнопки ===
    CONTRACT_DRAFT_PROMPT = (
        "🛠 <b>СОЗДАНИЕ КОНТРАКТА</b>\n\n"
        "1. Настрой параметры кнопками ниже.\n"
        "2. <b>Отправь сообщением название задачи</b>, чтобы подписать контракт кровью.\n"
        "<i>Или нажми «Отменить».</i>"
    )
    CONTRACT_ADDED = "✒️ <i>Контракт скреплен печатью гильдии. За работу, наемник!</i>"
    CONTRACT_CANCELED = "💨 <i>Ты отступил от доски контрактов.</i>"

    BTN_PROFILE = "Профиль"
    BTN_CONTRACTS = "Доска Контрактов"
    BTN_RITUAL = "Выстоять"
    BTN_CORRUPTION = "Провалить привычку"
    BTN_INVENTORY = "Инвентарь и Крафт"
    BTN_SHOP = "Лавка алхимика"
    BOT_STARTED = "Осколки Воли: Бот запущен..."
    WELCOME_TEXT = "Приветствую, наемник! Твоя воля расколота, но путь только начинается. Выбирай свое действие с умом."

    @staticmethod
    def corruption_result(hp: int, max_hp: int, result) -> str:
        """Генерирует лог скверны. Принимает объект CorruptionResult."""
        if result.is_fail:
            text = "🩸 <b>Вы поддались скверне... и она проникла в вас.</b>\n\n"
            # Обращение через точку, так как result.roll — это объект RollData
            if result.roll.is_crit_fail:
                text = "💀 <b>КРИТИЧЕСКИЙ ПРОВАЛ! Скверна разрывает ваше тело!</b>\n\n"
        else:
            text = "🛡 <b>Вы поддались искушению, но организм смог побороть инфекцию.</b>\n\n"

        text += f"🔺 <b>Урон:</b> -{result.damage} HP\n\n"

        if result.new_diseases:
            text += f"🦠 <b>Получены болезни:</b> " + ", ".join(result.new_diseases) + "\n"

        text += f"\n❤️ <b>Текущее здоровье:</b> {hp}/{max_hp}"
        return text

    @staticmethod
    def format_roll(roll_data) -> str:
        """Генерирует подробный лог броска кубика."""
        parts = []
        for i, bonus in enumerate(roll_data.bonuses):
            if i == 0:
                # Если бросалось 2 кубика, выводим красиво: 4 (Из 15 и 4)
                if hasattr(roll_data, 'dice_rolls') and len(roll_data.dice_rolls) > 1:
                    parts.append(f"{bonus.value} (Из {roll_data.dice_rolls[0]} и {roll_data.dice_rolls[1]})")
                else:
                    parts.append(f"{bonus.value} ({bonus.source})")
            else:
                sign = "+" if bonus.value >= 0 else "-"
                parts.append(f"{sign} {abs(bonus.value)} ({bonus.source})")

        bd_str = " ".join(parts)

        # Теги преимущества/помехи (Отменяются, если включены оба)
        adv_text = ""
        if roll_data.advantage and not roll_data.disadvantage:
            adv_text = " <i>[Преимущество]</i>"
        if roll_data.disadvantage and not roll_data.advantage:
            adv_text = " <i>[Помеха]</i>"

        crit_text = ""
        if roll_data.is_crit_success: crit_text = "\n🎯 <b>КРИТИЧЕСКИЙ УСПЕХ (Натуральная 20)!</b>"
        if roll_data.is_crit_fail: crit_text = "\n💀 <b>КРИТИЧЕСКИЙ ПРОВАЛ (Натуральная 1)!</b>"

        return (
            f"🎲 <b>{roll_data.roll_type}</b> (Сложность {roll_data.dc}){adv_text}:\n"
            f"└ <b>Результат {roll_data.total}:</b> {bd_str}{crit_text}"
        )

    @staticmethod
    def _format_mod(mod: int) -> str:
        """Форматирует модификатор D&D для вывода: +2, 0, -1"""
        return f"+{mod}" if mod >= 0 else str(mod)

    @staticmethod
    def profile_sheet(hero) -> str:
        """Генерирует D&D лист персонажа, запрашивая расчеты у GameCalculator."""
        from core.game_calculator import GameCalculator
        from core.status_registry import StatusRegistry

        char = hero.model
        # Получаем порог опыта для текущего уровня из чистого калькулятора
        xp_to_next = GameCalculator.XP_TABLE.get(char.level + 1, "Максимум")

        sheet = (
            f"📜 <b>ЛИСТ ПЕРСОНАЖА: {char.name.upper()}</b> 📜\n"
            f"───────────────────────\n"
            f"<b>Уровень:</b> {char.level} | <b>Опыт:</b> {char.xp} / {xp_to_next}\n"
            f"<b>Хитпоинты:</b> ❤️ {char.hp}/{char.max_hp} | <b>Золото:</b> {char.gold}🌕\n\n"
        )

        sheet += "<b>📊 ХАРАКТЕРИСТИКИ:</b>\n"
        stats_display = [
            ("💪 Сила", "STR"), ("🏃 Ловкость", "DEX"), ("🛡 Выносливость", "CON"),
            ("🧠 Интеллект", "INT"), ("🦉 Мудрость", "WIS"), ("🗣 Харизма", "CHA")
        ]

        # Считаем итоговые статы через калькулятор (эффекты от статусов отключены, передаем 0)
        for name, key in stats_display:
            base_stat = char.stats.get(key, 10)
            final_val, mod = GameCalculator.calculate_stat_modifier(base_stat, 0)
            sheet += f"  {name}: <b>{final_val}</b> <i>({Texts._format_mod(mod)})</i>\n"

        sheet += "\n<b>🎭 АКТИВНЫЕ СОСТОЯНИЯ:</b>\n"

        if not hero.active_statuses:
            sheet += "  <i>Ваш разум и тело девственно чисты.</i>\n"
        else:
            # ИСПРАВЛЕНО: Добавили список debuffs
            buffs, injuries, diseases, debuffs = [], [], [], []

            # Сортируем статусы по типам для красивого вывода
            for s in hero.active_statuses:
                name_key = s.name if hasattr(s, 'name') else s["name"]
                template = StatusRegistry.get(name_key)
                if not template: continue

                if template.type == 'buff':
                    buffs.append(template.name_text)
                elif template.type == 'injury':
                    injuries.append(template.name_text)
                elif template.type == 'disease':
                    diseases.append(template.name_text)
                elif template.type == 'debuff':  # ИСПРАВЛЕНО: Обрабатываем новый тип
                    debuffs.append(template.name_text)

            if buffs:
                sheet += "  <b>✨ Благословения:</b>\n"
                for b in buffs: sheet += f"    • {b}\n"

            if injuries:
                sheet += "  <b>🩸 Травмы:</b>\n"
                for i in injuries: sheet += f"    • {i}\n"

            if diseases:
                sheet += "  <b>🦠 Болезни:</b>\n"
                for d in diseases: sheet += f"    • {d}\n"

            if debuffs:  # ИСПРАВЛЕНО: Выводим дебаффы
                sheet += "  <b>📉 Ослабления:</b>\n"
                for d in debuffs: sheet += f"    • {d}\n"

        # === ГРУППИРОВКА ПРЕДМЕТОВ В ИНВЕНТАРЕ ПО КАЧЕСТВУ ===
        sheet += "\n<b>📦 СОДЕРЖИМОЕ СУМОК:</b>\n"

        # Безопасно вытаскиваем сырой словарь предметов героя {"Имя": Кол-во}
        inv_items = {}
        if hasattr(hero.inventory, "items") and isinstance(hero.inventory.items, dict):
            inv_items = hero.inventory.items
        elif hasattr(hero.inventory, "get_items"):
            inv_items = hero.inventory.get_items() or {}

        if not inv_items:
            sheet += "  <i>В заплечном мешке гуляет ветер.</i>\n"
        else:
            # Вытягиваем весь справочник предметов из ItemsRepo через контроллер
            shop_items = hero.get_shop_items()
            # Строим карту "Имя предмета" -> "Тип (precious, potion и т.д.)"
            item_type_map = {item["name_text"]: item["type"] for item in shop_items}

            # Шаблон категорий для красивой разбивки
            categories = {
                "precious": ("💎 Драгоценности", []),
                "component": ("🔮 Компоненты", []),
                "potion": ("🧪 Алхимия", []),
                "junk": ("🗑️ Хлам", [])
            }

            # Распределяем вещи Астры по спискам
            for item_name, quantity in inv_items.items():
                item_type = item_type_map.get(item_name, "junk")  # Если предмета нет в справочнике, кидаем в хлам
                if item_type in categories:
                    categories[item_type][1].append(f"    • {item_name} x{quantity}")
                else:
                    categories["junk"][1].append(f"    • {item_name} x{quantity}")

            # Собираем итоговый текст профиля (выводятся только непустые группы)
            has_any_item = False
            for type_key, (category_title, items_list) in categories.items():
                if items_list:
                    has_any_item = True
                    sheet += f"  <b>{category_title}:</b>\n"
                    for item_str in items_list:
                        sheet += item_str + "\n"

            if not has_any_item:
                sheet += "  <i>В заплечном мешке гуляет ветер.</i>\n"

        return sheet

    DIFFICULTIES = ["Легкий", "Средний", "Сложный", "Невероятный"]
    DURATIONS = ["До 15 минут", "До 2 часов", "До дня"]

    @staticmethod
    def get_deadline_options() -> list:
        """Возвращает список из 7 дней для дедлайнов: Сегодня, Завтра, и дни недели."""
        days_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        today_idx = datetime.datetime.now().weekday()
        labels = ["Сегодня", "Завтра"]
        for i in range(2, 7):
            labels.append(days_ru[(today_idx + i) % 7])
        return labels

    @staticmethod
    def board_sheet(contracts: list) -> str:
        text = "📜 <b>ДОСКА КОНТРАКТОВ</b> 📜\n───────────────────────\n"
        if not contracts:
            return text + "<i>Доска пуста. Гильдия ждет, пока ты возьмешь новый заказ.</i>"

        for c in contracts:
            text += (
                f"⚔️ <b>{c['name']}</b>\n"
                f"  ┣ <b>Сложность:</b> {c['difficulty']}\n"
                f"  ┣ <b>Время:</b> {c['duration']}\n"
                f"  ┗ <b>Дедлайн:</b> {c['deadline']}\n\n"
            )
        return text

    @staticmethod
    def contract_completed(contract_name: str, result) -> str:
        """Лог выполнения контракта. Принимает объект ContractCompleteResult."""
        text = f"⚔️ <b>Контракт «{contract_name}» успешно закрыт!</b> ⚔️\n\n"

        text += Texts.format_roll(result.wis_roll) + "\n"
        text += f"🔺 <b>Опыт:</b> +{result.xp_gained}\n\n"

        text += f"🌕 <b>Золото:</b> +{result.gold_gained}\n\n"

        int_roll = result.int_roll

        parts = []
        for i, bonus in enumerate(int_roll.bonuses):
            if i == 0:
                parts.append(f"{bonus.value} ({bonus.source})")
            else:
                sign = "+" if bonus.value >= 0 else "-"
                parts.append(f"{sign} {abs(bonus.value)} ({bonus.source})")

        int_bd = " ".join(parts)

        adv_text = ""
        if int_roll.advantage: adv_text = " <i>[Преимущество]</i>"
        if int_roll.disadvantage: adv_text = " <i>[Помеха]</i>"

        text += (
            f"🎲 <b>Проверка Интеллекта (Качество лута)</b>{adv_text}:\n"
            f"└ <b>Результат {int_roll.total}:</b> {int_bd}\n"
            f"📊 <i>Пороги: Хлам &lt; 13 | Зелья 13+ | Компоненты 17+ | Драгоценности 21+</i>\n"
        )

        if result.items_found:
            text += f"📦 <b>Лут:</b> " + ", ".join(result.items_found)
        else:
            text += f"📦 <b>Лут:</b> <i>Вы ничего не нашли.</i>"

        return text

    @staticmethod
    def ritual_result(result) -> str:
        """Лог выполнения ритуала. Принимает объект RitualResult."""
        if result.is_success:
            text = "✨ <b>Ритуал завершен успешно! Ваша воля крепчает.</b>\n\n"
            if result.roll.is_crit_success:
                text = "🌟 <b>КРИТИЧЕСКИЙ УСПЕХ! Боги благоволят вашей стойкости!</b>\n\n"

            if result.new_buff:
                text += f"🛡 <b>Получено благословение:</b> {result.new_buff}"
        else:
            text = "💨 <b>Ритуал не удался. Вы потеряли концентрацию, и энергия рассеялась.</b>\n"
            if result.roll.is_crit_fail:
                text = "🌑 <b>КРИТИЧЕСКИЙ ПРОВАЛ! Ваши мысли погрузились в хаос.</b>"

        return text

    @staticmethod
    def shop_sheet(items: list, current_gold: int) -> str:
        """Выводит витрину магазина."""
        text = f"🧪 <b>ЛАВКА АЛХИМИКА</b> 🧪\n"
        text += f"Ваше золото: {current_gold}🌕\n"
        text += f"───────────────────────\n\n"

        for i in items:
            text += (
                f"📦 <b>{i['name_text']}</b> — {i['price']}🌕\n"
                f"  ├ <b>Тип:</b> {i['type']}\n"
                f"  ┗ <i>{i['effect_desc']}</i>\n\n"
            )
        text += "<i>Нажмите на кнопку ниже, чтобы купить предмет в инвентарь.</i>"
        return text

    BTN_QUEST = "Текущий Квест"  # Не забудь добавить эту кнопку в клавиатуру!

    @staticmethod
    def quest_menu(quest) -> str:
        """Генерирует главное меню активного квеста с историей событий."""
        if not quest or quest.status != "active":
            return "🗺 <i>У вас нет активного квеста. Загляните на Доску Контрактов.</i>"

        text = (
            f"🗺 <b>КВЕСТ: {quest.quest_name}</b>\n"
            f"───────────────────────\n"
            f"<i>{quest.description}</i>\n\n"
            f"⏳ <b>День:</b> {quest.current_day+1} из {quest.max_days}\n"
            f"🏆 <b>Награда:</b> 🌕 {quest.gold_reward} | 🔺 {quest.exp_reward} XP\n"
        )

        # === НОВЫЙ БЛОК: ИСТОРИЯ ЭВЕНТОВ ===
        text += "\n📖 <b>Журнал событий:</b>\n"

        # Берем все эвенты от старта (0) до текущего дня (включительно)
        # Обязательно проверяем длину списка, чтобы не словить ошибку IndexError
        for i in range(quest.current_day + 1):
            if i < len(quest.cycle_steps):
                step = quest.cycle_steps[i]

                # Поддерживаем как объекты (DataClasses), так и сырые словари (Dicts) из базы
                step_num = step.number if hasattr(step, 'number') else step['number']
                step_title = step.display_name if hasattr(step, 'display_name') else step['display_name']
                step_desc = step.description if hasattr(step, 'description') else step['description']

                text += f"  🔹 <b>{step_title}</b>\n"
                text += f"      <i>{step_desc}</i>\n\n"

        return text.strip()  # Убираем лишние переносы строк в самом конце

    @staticmethod
    def daily_event_message(day: int, title: str, desc: str) -> str:
        """Текст сюжетного события при наступлении нового дня."""
        return (
            f"🌅 <b>ДЕНЬ {day}: {title}</b>\n"
            f"───────────────────────\n"
            f"<i>{desc}</i>"
        )

    @staticmethod
    def task_menu(task) -> str:
        """Генерирует описание конкретной задачи перед броском и выводит варианты."""
        from core.game_calculator import GameCalculator

        text = (
            f"⚔️ <b>ЗАДАЧА: {task.display_name}</b>\n"
            f"───────────────────────\n"
            f"<i>{task.description}</i>\n\n"
            f"<b>Возможные подходы:</b>\n"
        )

        for check in task.checks:
            skill_lower = check.skill.lower().strip()
            skill_ru = GameCalculator.SKILL_MAP.get(skill_lower, (check.skill, ""))[0]

            # ИСПРАВЛЕНО: Теперь КС находится внутри жирного блока до текста
            text += f"  🔹 <b>[{skill_ru}] (КС {check.difficulty})</b> {check.display_name}\n"

        return text
    @staticmethod
    def quest_check_result(result) -> str:
        """Лог выполнения задачи в квесте. Принимает QuestCheckResult."""
        from core.status_registry import StatusRegistry  # Импорт для расшифровки дебаффов

        text = Texts.format_roll(result.roll_data) + "\n\n"

        # Нарративное сообщение
        if result.success:
            text += f"✅ <i>{result.message}</i>\n"
        else:
            text += f"❌ <i>{result.message}</i>\n"

        # Вывод последствий (TaskEffects)
        if result.damage_taken > 0:
            text += f"\n🩸 <b>Урон от последствий:</b> -{result.damage_taken} HP"

        # === ОБНОВЛЕННЫЙ БЛОК ДЕБАФФОВ ===
        if result.debuffs_received:
            text += f"\n🦠 <b>Наложены негативные эффекты:</b>\n"
            for d in result.debuffs_received:
                template = StatusRegistry.get(d)
                if template:
                    # Выводим красивое название и лорное описание
                    text += f"  • <b>{template.name_text}</b> — <i>{template.description}</i>\n"
                else:
                    # Фолбэк, если дебаффа вдруг нет в БД
                    text += f"  • <b>{d}</b>\n"

        # Если квест полностью пройден
        if result.quest_completed:
            text += (
                f"\n\n───────────────────────\n"
                f"🏆 <b>ГЛОБАЛЬНЫЙ УСПЕХ: КВЕСТ ЗАВЕРШЕН!</b> 🏆\n"
                f"🌕 <b>Золото:</b> +{result.gold_reward}\n"
                f"🔺 <b>Опыт:</b> +{result.xp_reward}"
            )

        return text