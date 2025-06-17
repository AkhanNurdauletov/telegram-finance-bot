from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from datetime import datetime

from finance_db import add_entry, get_all_entries, delete_entry, get_user_entries_with_id, update_entry
from utils import export_to_excel

router = Router()

class FinanceForm(StatesGroup):
    waiting_for_type = State()
    waiting_for_description = State()
    waiting_for_amount = State()
    waiting_for_deletion = State()

class EditEntryForm(StatesGroup):
    choosing_entry = State()
    entering_new_amount = State()
    entering_new_description = State()


keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить доход"), KeyboardButton(text="➖ Добавить расход")],
        [KeyboardButton(text="📖 История"), KeyboardButton(text="📊 Экспорт в Excel")],
        [KeyboardButton(text="🗑 Удалить запись")],
        [KeyboardButton(text="✏️ Редактировать запись")],

    ],
    resize_keyboard=True
)

@router.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("👋 Привет! Я бот для учёта доходов и расходов.\n\nВыберите действие:", reply_markup=keyboard)

@router.message(F.text.in_(["➕ Добавить доход", "➖ Добавить расход"]))
async def add_start(message: types.Message, state: FSMContext):
    entry_type = "income" if "доход" in message.text else "expense"
    await state.update_data(entry_type=entry_type)
    await message.answer("Введите описание:")
    await state.set_state(FinanceForm.waiting_for_description)

@router.message(FinanceForm.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите сумму:")
    await state.set_state(FinanceForm.waiting_for_amount)

@router.message(FinanceForm.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    entry_type = data["entry_type"]
    description = data["description"]
    user_id = message.from_user.id

    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Ошибка! Введите сумму числом.")
        return

    date = datetime.now().strftime("%Y-%m-%d")
    add_entry(user_id, entry_type, amount, description, date)
    await message.answer(f"✅ Запись добавлена: {description} — {amount} ({'Доход' if entry_type == 'income' else 'Расход'})")
    await state.clear()

@router.message(F.text == "📖 История")
async def history_handler(message: types.Message):
    user_id = message.from_user.id
    entries = get_all_entries(user_id)

    if not entries:
        await message.answer("Нет данных.")
        return

    response = "\n".join([f"{e[2]} — {e[0]} тг ({e[1]})" for e in entries])
    await message.answer(f"<b>История операций:</b>\n\n{response}")

@router.message(F.text == "📊 Экспорт в Excel")
async def export_handler(message: types.Message):
    file_path = export_to_excel(message.from_user.id)
    await message.answer_document(types.FSInputFile(file_path))

@router.message(F.text == "🗑 Удалить запись")
async def delete_entry_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    entries = get_all_entries(user_id)

    if not entries:
        await message.answer("У вас нет записей для удаления.")
        return

    # Показываем последние 5 записей с id
    text = "<b>Последние записи:</b>\n"
    for entry in entries[:5]:
        entry_id = entry[3] if len(entry) > 3 else "?"  # На случай, если id нет в выборке
        text += f"{entry_id}. {entry[2]} — {entry[0]} тг ({entry[1]})\n"

    await message.answer(f"{text}\nВведите ID записи, которую хотите удалить:")
    await state.set_state(FinanceForm.waiting_for_deletion)


@router.message(FinanceForm.waiting_for_deletion)
async def delete_entry_confirm(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        entry_id = int(message.text)
        delete_entry(user_id, entry_id)
        await message.answer(f"✅ Запись с ID {entry_id} удалена.")
    except ValueError:
        await message.answer("Пожалуйста, введите корректный числовой ID.")
    except Exception as e:
        await message.answer(f"Ошибка при удалении: {e}")

    await state.clear()


@router.message(F.text == "✏️ Редактировать запись")
async def edit_start(message: types.Message, state: FSMContext):
    entries = get_user_entries_with_id(message.from_user.id)
    if not entries:
        await message.answer("Нет записей для редактирования.")
        return

    text = "Выберите ID записи для редактирования:\n\n"
    text += "\n".join([f"ID {e[0]} — {e[1]}₸ | {e[2]} | {e[3]}" for e in entries])
    await message.answer(text)
    await state.set_state(EditEntryForm.choosing_entry)

@router.message(EditEntryForm.choosing_entry)
async def choose_entry(message: types.Message, state: FSMContext):
    try:
        entry_id = int(message.text.strip())
        await state.update_data(entry_id=entry_id)
        await message.answer("Введите новую сумму:")
        await state.set_state(EditEntryForm.entering_new_amount)
    except ValueError:
        await message.answer("Введите корректный ID записи (числом).")

@router.message(EditEntryForm.entering_new_amount)
async def enter_new_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        await state.update_data(new_amount=amount)
        await message.answer("Введите новое описание:")
        await state.set_state(EditEntryForm.entering_new_description)
    except ValueError:
        await message.answer("Введите сумму числом.")

@router.message(EditEntryForm.entering_new_description)
async def enter_new_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    update_entry(data['entry_id'], data['new_amount'], message.text)
    await message.answer("✅ Запись успешно обновлена.")
    await state.clear()
