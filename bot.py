import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ContentType
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import database
from config import settings

logging.basicConfig(level=logging.INFO)

class Form(StatesGroup):
    main = State()
    print_tech = State()
    print_materials = State()
    print_other_material = State()
    print_params = State()
    print_custom_infill = State()
    print_custom_infill_type = State()
    print_custom_walls = State()
    print_file = State()

    scan_type = State()
    scan_description = State()

    idea_type = State()
    idea_description = State()

    about = State()


ABOUT_PAGES = [
    ("Оборудование", "🏭 Используем FDM и фотополимерные принтеры, 3D-сканеры и постобработку."),
    ("Наши проекты", "🖼 Делаем функциональные детали, сувениры, прототипы и рекламные изделия."),
    ("Контакты", "📞 Контакты компании остаются без изменений."),
    ("На карте", "📍 Работаем по договоренности, доступна доставка и самовывоз."),
]


def kb(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=data) for text, data in row] for row in rows]
    )


def menu_kb():
    return kb(
        [
            [("📐 Рассчитать печать", "menu:print")],
            [("📡 3D-сканирование", "menu:scan")],
            [("❓ Нет модели / Хочу придумать", "menu:idea")],
            [("ℹ️ О нас", "menu:about")],
        ]
    )

def nav_kb(back="nav:back"):
    return kb([[("🔙 Назад", back), ("🏠 Главное меню", "nav:menu")]])


async def set_step(state: FSMContext, step: str):
    data = await state.get_data()
    history = data.get("history", [])
    if not history or history[-1] != step:
        history.append(step)
    await state.update_data(history=history)
	
	
async def show_main(target: Message | CallbackQuery, state: FSMContext):
    await state.set_state(Form.main)
    text = "Добро пожаловать в Chel3D 👋\nВыберите нужный раздел:"
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=menu_kb())
        await target.answer()
    else:
        await target.answer(text, reply_markup=menu_kb())


async def start_order(user, branch: str, state: FSMContext):
    database.cancel_old_drafts(user.id)
    order_id = database.create_order(user.id, user.username, user.full_name, branch)
    await state.clear()
    await state.update_data(order_id=order_id, branch=branch, history=[])


async def save_payload(state: FSMContext, key: str, value):
    data = await state.get_data()
    order_id = data["order_id"]
    payload = database.get_order_payload(order_id)
    payload[key] = value
    database.update_order_payload(order_id, payload)
    await state.update_data(payload=payload)


async def show_print_tech(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.print_tech)
    await set_step(state, "print_tech")
    await cb.message.edit_text(
        "Выберите технологию печати:",
        reply_markup=kb(
            [
                [("🧵 FDM (Пластик)", "print_tech:FDM")],
                [("💧 Фотополимер", "print_tech:Фотополимер")],
                [("🤷 Не знаю", "print_tech:Не знаю")],
                [("🏠 Главное меню", "nav:menu")],
            ]
        ),
    )


async def show_materials(cb: CallbackQuery, state: FSMContext, tech: str):
    await save_payload(state, "технология", tech)
    await state.set_state(Form.print_materials)
    await set_step(state, "print_materials")
    if tech == "Фотополимер":
        rows = [
            [("Стандартная", "mat:Стандартная")],
            [("ABS-Like", "mat:ABS-Like")],
            [("TPU-Like", "mat:TPU-Like")],
            [("Нейлон-Like", "mat:Нейлон-Like")],
            [("🤔 Другая смола", "mat:Другая смола")],
            [("🔙 Назад", "nav:back"), ("🏠 Главное меню", "nav:menu")],
        ]
        text = "Выберите фотополимерную смолу:"
    else:
        rows = [
            [("PET-G", "mat:PET-G"), ("PLA", "mat:PLA")],
            [("PET-G Carbon", "mat:PET-G Carbon"), ("TPU", "mat:TPU")],
            [("Нейлон", "mat:Нейлон")],
            [("🤔 Другой материал", "mat:Другой материал")],
            [("🔙 Назад", "nav:back"), ("🏠 Главное меню", "nav:menu")],
        ]
        text = "Выберите материал FDM:"
    await cb.message.edit_text(text, reply_markup=kb(rows))


async def show_material_card(cb: CallbackQuery, state: FSMContext, material: str):
    await save_payload(state, "материал", material)
    await cb.message.edit_text(
        f"Материал: {material}\nПодходит для большинства задач. Подтвердите выбор.",
        reply_markup=kb(
            [
                [("✅ Выбрать", "mat_use")],
                [("🔙 К списку", "nav:back")],
                [("🏠 Главное меню", "nav:menu")],
            ]
        ),
    )


async def show_print_params(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.print_params)
    await set_step(state, "print_params")
    data = await state.get_data()
    payload = data.get("payload", database.get_order_payload(data["order_id"]))
    post = payload.get("постобработка", {"Шлифовка": False, "Покраска": False, "Грунтовка": False, "Не нужна": False})
    def mark(name):
        return f"{'☑️' if post.get(name) else '☐'} {name}"
    await cb.message.edit_text(
        "Параметры печати (фиксированные значения выбираются кнопками):",
        reply_markup=kb([
            [("10%", "inf:10%"), ("20%", "inf:20%"), ("30%", "inf:30%")],
            [("50%", "inf:50%"), ("100%", "inf:100%")],
            [("✏️ Свое значение", "inf:custom")],
            [("Гироид", "ptype:Гироид"), ("Соты", "ptype:Соты")],
            [("Треугольник", "ptype:Треугольник"), ("Линии", "ptype:Линии")],
            [("Концентрическое", "ptype:Концентрическое")],
            [("✏️ Другое", "ptype:custom")],
            [("1.2 мм", "walls:1.2 мм"), ("1.6 мм", "walls:1.6 мм")],
            [("2.0 мм", "walls:2.0 мм"), ("2.4 мм", "walls:2.4 мм")],
            [("✏️ Свое значение", "walls:custom")],
            [(mark("Шлифовка"), "post:Шлифовка"), (mark("Покраска"), "post:Покраска")],
            [(mark("Грунтовка"), "post:Грунтовка"), (mark("Не нужна"), "post:Не нужна")],
            [("✅ Дальше", "to:file")],
            [("📎 Пропустить и прикрепить файл", "to:file")],
            [("🔙 Назад", "nav:back"), ("🏠 Главное меню", "nav:menu")],
        ]),
    )


async def show_file_step(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.print_file)
    await set_step(state, "print_file")
    await cb.message.edit_text(
        "Прикрепите файл STL/3MF/OBJ документом.",
        reply_markup=kb([[('❌ У меня нет файла', 'file:none')], [('🔙 Назад', 'nav:back'), ('🏠 Главное меню', 'nav:menu')]]),
    )


def build_summary(branch: str, payload: dict) -> str:
    lines = [f"Тип заявки: {branch}"]
    for k, v in payload.items():
        if k == "постобработка" and isinstance(v, dict):
            sel = [name for name, enabled in v.items() if enabled]
            lines.append(f"Постобработка: {', '.join(sel) if sel else 'не выбрана'}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("💰 Уточнит менеджер после проверки.")
    return "\n".join(lines)


async def show_review(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    payload = data.get("payload", database.get_order_payload(data["order_id"]))
    text = build_summary(data["branch"], payload)
    await cb.message.edit_text(
        text,
        reply_markup=kb(
            [[("✅ Отправить заявку", "send")], [("🔁 Новый расчет", "menu:print")], [("🏠 Главное меню", "nav:menu")]]
        ),
    )


async def submit_order(cb: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    order_id = data["order_id"]
    payload = database.get_order_payload(order_id)
    summary = build_summary(data["branch"], payload)
    database.finalize_order(order_id, data["branch"], summary)
    await cb.message.edit_text("Заявка отправлена ✅\n💰 Уточнит менеджер после проверки.", reply_markup=menu_kb())

    if settings.orders_chat_id:
        manager = f"@{settings.manager_username}" if settings.manager_username else "менеджер"
        text = f"📥 Новая заявка #{order_id}\nКлиент: {cb.from_user.full_name} (@{cb.from_user.username})\n{summary}\nОтветственный: {manager}"
        await bot.send_message(settings.orders_chat_id, text)
        for f in database.list_order_files(order_id):
            await bot.send_document(settings.orders_chat_id, f["telegram_file_id"], caption=f"Файл: {f['original_name']}")

    await state.clear()


async def callback_handler(cb: CallbackQuery, state: FSMContext, bot: Bot):
    data = cb.data or ""


    if data == "nav:menu":
        await state.clear()
        return await show_main(cb, state)

    if data.startswith("menu:"):
        action = data.split(":", 1)[1]
        if action == "print":
            await start_order(cb.from_user, "Рассчитать печать", state)
            return await show_print_tech(cb, state)
        if action == "scan":
            await start_order(cb.from_user, "3D-сканирование", state)
            await state.set_state(Form.scan_type)
            await set_step(state, "scan_type")
            await cb.message.edit_text("Что нужно отсканировать?", reply_markup=kb([
                [("🧑 Человек", "scan:Человек"), ("📦 Предмет", "scan:Предмет")],
                [("🏭 Промышленный объект", "scan:Промышленный объект")],
                [("🤔 Другое", "scan:Другое")],
                [("🏠 Главное меню", "nav:menu")],
            ]))
            return
        if action == "idea":
            await start_order(cb.from_user, "Нет модели / Хочу придумать", state)
            await state.set_state(Form.idea_type)
            await set_step(state, "idea_type")
            await cb.message.edit_text("Выберите категорию:", reply_markup=kb([
                [("✏️ По фото/эскизу", "idea:По фото/эскизу")],
                [("🏆 Сувенир/Кубок/Медаль", "idea:Сувенир/Кубок/Медаль")],
                [("📏 Мастер-модель", "idea:Мастер-модель")],
                [("🎨 Вывески", "idea:Вывески")],
                [("🤔 Другое", "idea:Другое")],
                [("🏠 Главное меню", "nav:menu")],
            ]))
            return
        if action == "about":
            await state.set_state(Form.about)
            await state.update_data(about_idx=0)
            title, text = ABOUT_PAGES[0]
            return await cb.message.edit_text(f"ℹ️ {title}\n\n{text}", reply_markup=kb([[('➡️ Далее', 'about:next')], [('🏠 Главное меню', 'nav:menu')]]))

    if data == "nav:back":
        s = await state.get_state()
        if s == Form.print_materials.state:
            return await show_print_tech(cb, state)
        if s == Form.print_file.state:
            return await show_print_params(cb, state)
        if s == Form.print_params.state:
            d = await state.get_data()
            tech = d.get("payload", {}).get("технология", "FDM")
            return await show_materials(cb, state, tech)
        return await show_main(cb, state)

    if data.startswith("print_tech:"):
        return await show_materials(cb, state, data.split(":", 1)[1])

    if data.startswith("mat:"):
        mat = data.split(":", 1)[1]
        if mat in {"Другой материал", "Другая смола"}:
            await state.set_state(Form.print_other_material)
            return await cb.message.edit_text("Введите нужный материал/смолу свободным текстом:", reply_markup=nav_kb())
        return await show_material_card(cb, state, mat)

    if data == "mat_use":
        return await show_print_params(cb, state)

    if data.startswith("inf:"):
        v = data.split(":", 1)[1]
        if v == "custom":
            await state.set_state(Form.print_custom_infill)
            return await cb.message.edit_text("Введите свое значение заполнения (%):", reply_markup=nav_kb())
        await save_payload(state, "заполнение", v)
        return await show_print_params(cb, state)

    if data.startswith("ptype:"):
        v = data.split(":", 1)[1]
        if v == "custom":
            await state.set_state(Form.print_custom_infill_type)
            return await cb.message.edit_text("Введите свой тип заполнения:", reply_markup=nav_kb())
        await save_payload(state, "тип заполнения", v)
        return await show_print_params(cb, state)

    if data.startswith("walls:"):
        v = data.split(":", 1)[1]
        if v == "custom":
            await state.set_state(Form.print_custom_walls)
            return await cb.message.edit_text("Введите свою толщину стенок:", reply_markup=nav_kb())
        await save_payload(state, "толщина стенок", v)
        return await show_print_params(cb, state)

    if data.startswith("post:"):
        key = data.split(":", 1)[1]
        d = await state.get_data()
        payload = d.get("payload", database.get_order_payload(d["order_id"]))
        post = payload.get("постобработка", {"Шлифовка": False, "Покраска": False, "Грунтовка": False, "Не нужна": False})
        post[key] = not post.get(key, False)
        if key == "Не нужна" and post[key]:
            post["Шлифовка"] = post["Покраска"] = post["Грунтовка"] = False
        if key in {"Шлифовка", "Покраска", "Грунтовка"} and post[key]:
            post["Не нужна"] = False
        await save_payload(state, "постобработка", post)
        return await show_print_params(cb, state)

    if data == "to:file":
        return await show_file_step(cb, state)

    if data == "file:none":
        await save_payload(state, "файл", "нет")
        return await show_review(cb, state)

    if data.startswith("scan:"):
        await save_payload(state, "тип сканирования", data.split(":", 1)[1])
        await state.set_state(Form.scan_description)
        return await cb.message.edit_text("Опишите задачу свободным текстом:", reply_markup=nav_kb())

    if data.startswith("idea:"):
        await save_payload(state, "категория", data.split(":", 1)[1])
        await state.set_state(Form.idea_description)
        return await cb.message.edit_text("Опишите идею свободным текстом:", reply_markup=nav_kb())

    if data.startswith("about:"):
        d = await state.get_data()
        idx = d.get("about_idx", 0)
        idx = min(len(ABOUT_PAGES) - 1, idx + 1) if data.endswith("next") else max(0, idx - 1)
        await state.update_data(about_idx=idx)
        title, text = ABOUT_PAGES[idx]
        btns = []
        row = []
        if idx > 0:
            row.append(("⬅️ Назад", "about:prev"))
        if idx < len(ABOUT_PAGES) - 1:
            row.append(("➡️ Далее", "about:next"))
        if row:
            btns.append(row)
        btns.append([("🏠 Главное меню", "nav:menu")])
        return await cb.message.edit_text(f"ℹ️ {title}\n\n{text}", reply_markup=kb(btns))

    if data == "send":
        return await submit_order(cb, state, bot)

    await cb.answer()


async def text_handler(message: Message, state: FSMContext):
    st = await state.get_state()
    if st == Form.print_other_material.state:
        await save_payload(state, "материал", message.text)
        await message.answer("Материал сохранен. Нажмите 🔙 Назад, чтобы вернуться к карточке.", reply_markup=nav_kb())
        return
    if st == Form.print_custom_infill.state:
        await save_payload(state, "заполнение", message.text)
        await state.set_state(Form.print_params)
        return await message.answer("Значение сохранено. Откройте параметры кнопками выше.")
    if st == Form.print_custom_infill_type.state:
        await save_payload(state, "тип заполнения", message.text)
        await state.set_state(Form.print_params)
        return await message.answer("Тип заполнения сохранен.")
    if st == Form.print_custom_walls.state:
        await save_payload(state, "толщина стенок", message.text)
        await state.set_state(Form.print_params)
        return await message.answer("Толщина стенок сохранена.")
    if st == Form.scan_description.state:
        await save_payload(state, "описание", message.text)
        await message.answer(build_summary("3D-сканирование", database.get_order_payload((await state.get_data())["order_id"])), reply_markup=kb([[('✅ Отправить заявку', 'send')], [('🏠 Главное меню', 'nav:menu')]]))
        return
    if st == Form.idea_description.state:
        await save_payload(state, "описание", message.text)
        await message.answer(build_summary("Нет модели / Хочу придумать", database.get_order_payload((await state.get_data())["order_id"])), reply_markup=kb([[('✅ Отправить заявку', 'send')], [('🏠 Главное меню', 'nav:menu')]]))
        return


async def file_handler(message: Message, state: FSMContext):
        st = await state.get_state()
    if st != Form.print_file.state:
        return
    if not message.document:
        await message.answer("Отправьте файл документом STL/3MF/OBJ.")
        return

    name = message.document.file_name or ""
    if not any(name.lower().endswith(ext) for ext in (".stl", ".3mf", ".obj")):
        await message.answer("Разрешены только STL/3MF/OBJ.")
        return
    order_id = (await state.get_data())["order_id"]
    database.add_order_file(order_id, message.document.file_id, name, message.document.mime_type, message.document.file_size)
    await save_payload(state, "файл", name)
    await message.answer("Файл сохранен. Нажмите отправку.", reply_markup=kb([[('✅ Отправить заявку', 'send')], [('🔙 Назад', 'nav:back'), ('🏠 Главное меню', 'nav:menu')]]))


async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await show_main(message, state)


def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, CommandStart())
    dp.callback_query.register(callback_handler)
    dp.message.register(file_handler, F.content_type == ContentType.DOCUMENT)
    dp.message.register(text_handler)


async def main():
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is empty")
    database.init_db_if_needed()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
