import asyncio
import datetime
from bot.keyboards import Keyboards
from core.dice import Dice


async def schedule_checker(bot, db, hero_controller):
    """Фоновая задача. Теперь безопасно обновляет ХП через контроллер."""
    while True:
        now = datetime.datetime.now()
        day_idx = now.weekday()
        today_str = now.strftime("%Y-%m-%d")
        current_time_minutes = now.hour * 60 + now.minute

        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Достаем все задачи на сегодня
            cursor.execute("""
                SELECT s.id, s.user_id, s.time_str, s.task_text, l.id as log_id, l.status 
                FROM schedules s
                LEFT JOIN schedule_logs l ON s.id = l.schedule_id AND l.log_date = ?
                WHERE s.day_idx = ?
            """, (today_str, day_idx))
            tasks = cursor.fetchall()

            for task in tasks:
                t_hour, t_minute = map(int, task['time_str'].split(':'))
                task_minutes = t_hour * 60 + t_minute
                diff = current_time_minutes - task_minutes

                # Если время уже пришло (diff >= 0) и задача еще не выполнена
                if diff >= 0 and task['status'] != 'done':

                    if task['log_id'] is None:
                        # 1. Задача только что наступила. Уведомляем!
                        cursor.execute("""
                            INSERT INTO schedule_logs (user_id, schedule_id, log_date, status)
                            VALUES (?, ?, ?, 'notified')
                        """, (task['user_id'], task['id'], today_str))
                        log_id = cursor.lastrowid
                        conn.commit()

                        try:
                            text = f"⏰ <b>Время пришло!</b>\n{task['time_str']} — {task['task_text']}"
                            await bot.send_message(task['user_id'], text,
                                                   reply_markup=Keyboards.schedule_done_kb(log_id), parse_mode="HTML")
                        except Exception:
                            pass

                    elif diff > 5 and task['status'] == 'notified':
                        # 2. Прошло больше 5 минут. Наносим урон!
                        cursor.execute("UPDATE schedule_logs SET status = 'damaged' WHERE id = ?", (task['log_id'],))
                        conn.commit()

                        damage = Dice.roll()["pure_roll"] % 4 + 1  # 1d4 урона

                        # === ИСПРАВЛЕННЫЙ БЛОК НАНЕСЕНИЯ УРОНА ===
                        if task['user_id'] == hero_controller.model.user_id:
                            # Если это наш текущий активный герой, меняем ХП через контроллер.
                            # Это обновит ХП и в оперативной памяти, и сразу сохранит в базу данных.
                            hero_controller._modify_hp(-damage)
                            await hero_controller.save_all()
                        else:
                            # Запасной вариант для других пользователей (на будущее)
                            cursor.execute("UPDATE characters SET hp = MAX(0, hp - ?) WHERE user_id = ?",
                                           (damage, task['user_id']))
                            conn.commit()

                        try:
                            text = f"🩸 <b>Вы прокрастинируете!</b>\nЗадача «{task['task_text']}» просрочена.\nПерсонаж получает {damage} урона."
                            await bot.send_message(task['user_id'], text,
                                                   reply_markup=Keyboards.schedule_done_kb(task['log_id']),
                                                   parse_mode="HTML")
                        except Exception:
                            pass

        await asyncio.sleep(300)  # Проверяем каждую минуту