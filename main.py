from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, PhotoSize)
from aiogram.types import (KeyboardButton, Message, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)
from config import tg_bot_token
from aiogram.types.input_file import InputFile
from aiogram.types import FSInputFile, URLInputFile, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

import cv2  # импорт модуля  из библиотеки Opencv
import numpy as np  # модуль обработки массивов
import sys  # системный модуль
import time
import os
from datetime import datetime
import datetime

import yadisk

y = yadisk.YaDisk(token="y0_AgAAAABwsItAAAp45QAAAADsX0aJYauTPJg6TASZT0E2wGkYgWVD6gE") #подключаемся к яндексу

from datetime import date
import gspread

gc = gspread.service_account()#подключаемся к гуглу
sh = gc.open_by_key('1tU_mrtqEe3Y_ElfjxXaXW3Duxgiy9a2pjGWX4K7FSqQ')

# Вместо BOT TOKEN HERE нужно вставить токен вашего бота,
# полученный у @BotFather
BOT_TOKEN = tg_bot_token

# Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
storage: MemoryStorage = MemoryStorage()

# Создаем объекты бота и диспетчера
bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher(storage=storage)

# Создаем "базу данных" пользователей
user_dict: dict[int, dict[str, str | int | bool]] = {}


# Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMFillForm(StatesGroup):
    # Создаем экземпляры класса State, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодействия с пользователем
    default_state = State()  # Состояние ожидания ввода новой даты поверки
    fill_date = State()        # Состояние ожидания ввода новой даты поверки
    change_info = State()         # Состояние ожидания смены информации описания прибора
    change_type = State()  # Состояние ожидания смены информации описания прибора
    change_status = State()      # Состояние ожидания выбора состояния
    upload_photo = State()     # Состояние ожидания загрузки нового фото
    change_location = State()   # Состояние ожидания выбора места текущего хранения
    change_storage = State()   # Состояние ожидания выбора получать ли новости
    fill_name = State()  # Состояние ожидания выбора получать ли новости
    fill_number = State()  # Состояние ожидания выбора получать ли новости
    show_from_list_state = State()  # Состояние ожидания выбора получать ли новости
    chiose_fnd_type = State()  #
    fnd_number = State()  #
    fnd_number_enter = State()  #
    fnd_name = State()  #
    fnd_name_enter = State()  #

# Этот хэндлер будет срабатывать на команду /start вне состояний
# и предлагать перейти к заполнению анкеты, отправив команду /fillform
@dp.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    # Создаем объекты кнопок
    button_1 = KeyboardButton(text='Неделя')
    button_2 = KeyboardButton(text='2 недели')
    button_3 = KeyboardButton(text='Месяц')
    button_4 = KeyboardButton(text='Поиск приборов')

    # Создаем объект клавиатуры, добавляя в него кнопки
    keyboard = ReplyKeyboardMarkup(keyboard=[[button_1], [button_2], [button_3], [button_4]], resize_keyboard=True)



    await message.answer(
        text='Чего желаете?',
        reply_markup=keyboard
    )


# Этот хэндлер будет срабатывать на ответ "неделя" и удалять клавиатуру
@dp.message(F.text == 'Неделя')
async def process_week_answer(message: Message, state: FSMContext):

    item_data = get_sheet()

    print(item_data)
    builder = InlineKeyboardBuilder()
    for button in item_data:

        builder.row(InlineKeyboardButton(
            text=f'{button[1]+" "+button[2]+" "+button[3]}',
            callback_data=f'{button[7]}'))
        print(button[7])
    await message.answer(
        "Выберите прибор для деталей",
        reply_markup=builder.as_markup()
    )
    await state.set_state(FSMFillForm.show_from_list_state)



# Этот хэндлер будет срабатывать на ответ "Поиск приборов" и удалять клавиатуру
@dp.message(F.text == 'Поиск приборов')
async def process_week_answer(message: Message, state: FSMContext):



    # Создаем объекты инлайн-кнопок
    photo_button = InlineKeyboardButton(text='По номеру',
                                        callback_data='fnd_number_enter')
    info_button = InlineKeyboardButton(text='По имени',
                                       callback_data='fnd_name_enter')

    # Добавляем кнопки в клавиатуру (две в одном ряду и одну в другом)
    keyboard: list[list[InlineKeyboardButton]] = [
        [photo_button, info_button]]
    # Создаем объект инлайн-клавиатуры
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    # Отправляем пользователю сообщение с клавиатурой


    await message.answer(
        text=f'Выберите тип поиска',


        reply_markup=markup)
    await state.set_state(FSMFillForm.chiose_fnd_type)

@dp.callback_query(StateFilter(FSMFillForm.chiose_fnd_type),  # введите номер прибора для поиска
                   F.data.in_(['fnd_number_enter']))
async def change_pribor_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Введите номер",

    )
    await state.set_state(FSMFillForm.fnd_number)


@dp.message(StateFilter(FSMFillForm.fnd_number) ) # поиск по номеру
async def fnd_number(message: Message, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "name"

    num = '45'
    name = message.text
    print(name)
    num = name

    x = sh.worksheet("sheet1").get_all_values()

    i = 0
    while i < len(x):
        x[i].append(i)
        i += 1

    i = 0
    z = []
    while i < len(x):
        if num in x[i][2] :
            z.append(x[i])
        i += 1
    print(z)

    builder = InlineKeyboardBuilder()
    for button in z:
        builder.row(InlineKeyboardButton(
            text=f'{button[1]+" "+button[2]+" "+button[3]}',
            callback_data=f'{button[7]}'))
        print(button[7])
    await message.answer(
        "Выберите прибор для деталей",
        reply_markup=builder.as_markup()
    )
    await state.set_state(FSMFillForm.show_from_list_state)



@dp.callback_query(StateFilter(FSMFillForm.chiose_fnd_type),  # введите номер прибора для поиска
                   F.data.in_(['fnd_name_enter']))
async def change_pribor_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Введите название",

    )
    await state.set_state(FSMFillForm.fnd_name)


@dp.message(StateFilter(FSMFillForm.fnd_name) ) # поиск по номеру
async def fnd_number(message: Message, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "name"

    num = '45'
    name = message.text
    print(name)
    num = name

    x = sh.worksheet("sheet1").get_all_values()

    i = 0
    while i < len(x):
        x[i].append(i)
        i += 1

    i = 0
    z = []
    while i < len(x):
        if num in x[i][1] :
            z.append(x[i])
        i += 1
    print(z)

    builder = InlineKeyboardBuilder()
    for button in z:
        builder.row(InlineKeyboardButton(
            text=f'{button[1]+" "+button[2]+" "+button[3]}', #здесь только три параметра так как есть ограниения по длдине запроса
            callback_data=f'{button[7]}'))
        print(button[7])
    await message.answer(
        "Выберите прибор для деталей",
        reply_markup=builder.as_markup()
    )
    await state.set_state(FSMFillForm.show_from_list_state)





@dp.callback_query(StateFilter(FSMFillForm.show_from_list_state)) #это обработчик показа карточки прибора из списка на поверку

async def show_pribor_from_list(callback: CallbackQuery, state: FSMContext):



    id_probor = callback.data
    await show_pribor_from_list(id_probor,callback,state)




def get_sheet(): #функция составления списка за неделю
    x = sh.worksheet("sheet1").get_all_values()

    i = 0
    while i < len(x):
        x[i].append(i)
        i += 1

    x.sort(key=lambda x: datetime.datetime.strptime(x[3], '%d %m %Y'))

    delta = datetime.timedelta(days=7)
    now = datetime.datetime.now()
    z = []

    i = 0
    while i < len(x):
        if datetime.datetime.strptime(x[i][3], '%d %m %Y') < now + datetime.timedelta(days=7):
            z.append(x[i])
        i += 1
    print(z)
    return z




@dp.message(StateFilter(FSMFillForm.upload_photo), #загрузка нового фото
            F.photo[-1].as_('largest_photo'))
async def process_photo_sent(message: Message,
                             state: FSMContext,
                             largest_photo: PhotoSize):

    pribor_id = await state.get_data()
    pribor_number = pribor_id['pribor']

    await bot.download(
        message.photo[-1],
        destination=f"{message.photo[-1].file_id}.jpg"
    )
    y.remove(f"{pribor_number}.jpg")
    y.upload(f"{message.photo[-1].file_id}.jpg", f"{pribor_number}.jpg")  # Загружает новый файл


    await message.answer(text='Спасибо!\n\nвсе загружено!')
    photo = FSInputFile(f"{message.photo[-1].file_id}.jpg")

    await message.answer_photo(photo)
    os.remove(f"{message.photo[-1].file_id}.jpg")
    await state.set_state(FSMFillForm.default_state)
    await show_pribor(pribor_number, message, state)



# Этот хэндлер будет срабатывать, если отправлено фото
# и переводить в состояние выбора образования
@dp.message(F.photo[-1].as_('largest_photo') )
async def download_photo(message: Message , state: FSMContext):

    await bot.download(
        message.photo[-1],
        destination=f"{message.photo[-1].file_id}.jpg"
    )

    inputImage = cv2.imread(f"{message.photo[-1].file_id}.jpg")  # стандартный метод opencv для считывания изображения#inputImage = photo # стандартный метод opencv для считывания изображения

    #y.upload(f"{message.photo[-1].file_id}.jpg",f"{message.photo[-1].file_id}.jpg")  # Загружает первый файл


    os.remove(f"{message.photo[-1].file_id}.jpg")
    # В Opencv имеется  встроенный метод детектор QR

    qrDecoder = cv2.QRCodeDetector()  # создание объекта детектора

    # Нахождение и декодирование нашего кода. Метод **detectAndDecode** возвращает  кортеж из трех  значений которыми кодируется QR, где первый аргумент data содержит декодированную строку, bbox - координаты вершин нашего изображения и rectifiedImage,  содержит **QR** изображение в виде массива пикселей.

    data, bbox, rectifiedImage = qrDecoder.detectAndDecode(inputImage)

    if len(data) > 0:

        await state.set_state(FSMFillForm.fill_date)



        print("Decoded Data : {}".format(data))  # вывод декодированной строки
        a = data
        # Разбиваем строку по самому правому 'A', берем левую часть
        b = a.rpartition('A')[2]
        print(b)  # Первый - второй
        await state.update_data(pribor=b) # запоминаем номер прибора в таблице

        y.download(f"{b}.jpg" , f"{b}.jpg")


        print(sh.worksheet("sheet1").get('A'+b+':G'+b))

        item_data = sh.worksheet("sheet1").get('A'+b+':G'+b)
        print(item_data[0][5])

        # Создаем объекты инлайн-кнопок
        photo_button = InlineKeyboardButton(text='Изменить фото',
                                                callback_data='ch_photo')
        info_button = InlineKeyboardButton(text='Изменить описание',
                                             callback_data='ch_info')

        # Добавляем кнопки в клавиатуру (две в одном ряду и одну в другом)
        keyboard: list[list[InlineKeyboardButton]] = [
            [photo_button, info_button]]
        # Создаем объект инлайн-клавиатуры
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        # Отправляем пользователю сообщение с клавиатурой
        photo = FSInputFile(f"{b}.jpg")



        await message.answer_photo(photo)




        await message.answer(
            photo = photo,

            text=f'Тип прибора: {item_data[0][0]}\n'
                    f'Название: {item_data[0][1]}\n'
                    f'Номер: {item_data[0][2]}\n'
                    f'Дата поверки: {item_data[0][3]}\n'
                    f'Состояние: {item_data[0][4]}\n'
                    f'Находится: {item_data[0][5]}\n'
                    f'Постоянное место: {item_data[0][6]}',
            reply_markup=markup)

        os.remove(f"{b}.jpg")






    else:

        print("QR Code not detected")
        photo = FSInputFile(f"nn.jpg")

        await message.answer_photo(photo)


# Этот хэндлер будет срабатывать на любые сообщения, кроме тех
# для которых есть отдельные хэндлеры, вне состояний
@dp.message(StateFilter(default_state))
async def send_echo(message: Message):
    await message.reply(text='Извините, моя твоя не понимать')



# Этот хэндлер будет срабатывать, если введено корректное имя
# и переводить в состояние ожидания ввода новой даты поверки
@dp.message(StateFilter(FSMFillForm.fill_date), lambda x: x.text.isdigit() )
async def process_name_sent(message: Message, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "name"
    #await state.update_data(name=message.text)
    date = list(message.text)
    new_date = date[0]+date[1]+' '+date[2]+date[3]+' 20'+date[4]+date[5]
    pribor_id = await state.get_data()
    pribor_number = pribor_id['pribor']
    sh.worksheet("sheet1").update_cell(pribor_number, 4, new_date)
    await show_pribor(pribor_number, message, state)

    # Устанавливаем состояние ожидания ввода возраста
    #await state.set_state(FSMFillForm.fill_age)



@dp.callback_query(StateFilter(FSMFillForm.fill_date), #это обработчик загрузки новых фото приборов
                   F.data.in_(['ch_photo']))
async def upload_new_photo(callback: CallbackQuery, state: FSMContext):
    # Cохраняем пол (callback.data нажатой кнопки) в хранилище,
    # по ключу "gender"
    #await state.update_data(gender=callback.data)
    # Удаляем сообщение с кнопками, потому что следующий этап - загрузка фото
    # чтобы у пользователя не было желания тыкать кнопки
    await callback.message.delete()
    await callback.message.answer(text='Загрузите новое фото')
    # Устанавливаем состояние ожидания загрузки фото
    await state.set_state(FSMFillForm.upload_photo)

@dp.callback_query(StateFilter(FSMFillForm.fill_date), #это обработчик загрузки новой информации
                   F.data.in_(['ch_info']))
async def upload_new_photo(callback: CallbackQuery, state: FSMContext):
    # Cохраняем пол (callback.data нажатой кнопки) в хранилище,
    # по ключу "gender"
    #await state.update_data(gender=callback.data)
    # Удаляем сообщение с кнопками, потому что следующий этап - загрузка фото
    # чтобы у пользователя не было желания тыкать кнопки
    # Создаем объекты инлайн-кнопок

    pribor_id = await state.get_data()
    pribor_number = pribor_id['pribor']

    item_data = sh.worksheet("sheet1").get('A' + pribor_number + ':G' + pribor_number)


    typ_button = InlineKeyboardButton(text=f'Тип прибора: {item_data[0][0]}', callback_data='pr_type')
    nam_button = InlineKeyboardButton(text=f'Название: {item_data[0][1]}', callback_data='pr_name')
    num_button = InlineKeyboardButton(text=f'Номер: {item_data[0][2]}', callback_data='pr_number')
    dat_button = InlineKeyboardButton(text=f'Дата поверки: {item_data[0][3]}', callback_data='pr_date')
    sta_button = InlineKeyboardButton(text=f'Состояние: {item_data[0][4]}', callback_data='pr_status')
    loc_button = InlineKeyboardButton(text=f'Находится: {item_data[0][5]}', callback_data='pr_location')
    sto_button = InlineKeyboardButton(text=f'Постоянное место: {item_data[0][6]}', callback_data='pr_storage')

    # Добавляем кнопки в клавиатуру (две в одном ряду и одну в другом)
    keyboard: list[list[InlineKeyboardButton]] = [
        [typ_button], [nam_button],[num_button], [dat_button],[sta_button], [loc_button], [sto_button]]
    # Создаем объект инлайн-клавиатуры
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    # Отправляем пользователю сообщение с клавиатурой


    await callback.message.answer(


        text=f'Тип прибора: {item_data[0][0]}\n'
             f'Название: {item_data[0][1]}\n'
             f'Номер: {item_data[0][2]}\n'
             f'Дата поверки: {item_data[0][3]}\n'
             f'Состояние: {item_data[0][4]}\n'
             f'Находится: {item_data[0][5]}\n'
             f'Постоянное место: {item_data[0][6]}',
        reply_markup=markup)
    await state.set_state(FSMFillForm.change_info)



@dp.callback_query(StateFilter(FSMFillForm.change_info), #это обработчик смены типа прибора
                   F.data.in_(['pr_type']))
async def change_pribor_type(callback: CallbackQuery, state: FSMContext):
    pribor_id = await state.get_data()
    pribor_number = pribor_id['pribor']

    item_data = sh.worksheet("sheet2").col_values(1)
    print(item_data)
    builder = InlineKeyboardBuilder()
    for button in item_data:
        builder.row(InlineKeyboardButton(
            text=f'{button}',
            callback_data=f'{button}'))
    await callback.message.answer(
        "Выберите тип прибора",
        reply_markup=builder.as_markup()
    )
    await state.set_state(FSMFillForm.change_type)

@dp.callback_query(StateFilter(FSMFillForm.change_type)) #это обработчик смены типа прибора когда сделан выбор

async def change_pribor_type(callback: CallbackQuery, state: FSMContext):
    pribor_id = await state.get_data()
    pribor_number = pribor_id['pribor']


    print(callback.data)

    sh.worksheet("sheet1").update_cell(pribor_number, 1, callback.data)
    await show_pribor_info_list(callback, state)


@dp.callback_query(StateFilter(FSMFillForm.change_info), #это обработчик смены состояния прибора
                   F.data.in_(['pr_status']))
async def change_pribor_type(callback: CallbackQuery, state: FSMContext):
    pribor_id = await state.get_data()
    pribor_number = pribor_id['pribor']

    item_data = sh.worksheet("sheet2").col_values(2)
    print(item_data)
    builder = InlineKeyboardBuilder()
    for button in item_data:
        builder.row(InlineKeyboardButton(
            text=f'{button}',
            callback_data=f'{button}'))
    await callback.message.answer(
        "Выберите состояние прибора",
        reply_markup=builder.as_markup()
    )
    await state.set_state(FSMFillForm.change_status)

@dp.callback_query(StateFilter(FSMFillForm.change_status)) #это обработчик смены соятояния прибора когда сделан выбор

async def change_pribor_type(callback: CallbackQuery, state: FSMContext):
    pribor_id = await state.get_data()
    pribor_number = pribor_id['pribor']


    print(callback.data)

    sh.worksheet("sheet1").update_cell(pribor_number, 5, callback.data)
    await show_pribor_info_list(callback, state)

@dp.callback_query(StateFilter(FSMFillForm.change_info), #это обработчик смены места нахождения прибора
                   F.data.in_(['pr_location']))
async def change_pribor_type(callback: CallbackQuery, state: FSMContext):
    pribor_id = await state.get_data()
    pribor_number = pribor_id['pribor']

    item_data = sh.worksheet("sheet2").col_values(3)
    print(item_data)
    builder = InlineKeyboardBuilder()
    for button in item_data:
        builder.row(InlineKeyboardButton(
            text=f'{button}',
            callback_data=f'{button}'))
    await callback.message.answer(
        "Выберите место нахождения прибора",
        reply_markup=builder.as_markup()
    )
    await state.set_state(FSMFillForm.change_location)

@dp.callback_query(StateFilter(FSMFillForm.change_location)) #это обработчик смены места нахождения прибора когда сделан выбор

async def change_pribor_type(callback: CallbackQuery, state: FSMContext):
    pribor_id = await state.get_data()
    pribor_number = pribor_id['pribor']


    print(callback.data)

    sh.worksheet("sheet1").update_cell(pribor_number, 6, callback.data)
    await show_pribor_info_list(callback, state)



@dp.callback_query(StateFilter(FSMFillForm.change_info), #это обработчик смены места хранения прибора
                   F.data.in_(['pr_storage']))
async def change_pribor_storage(callback: CallbackQuery, state: FSMContext):
    pribor_id = await state.get_data()
    pribor_number = pribor_id['pribor']

    item_data = sh.worksheet("sheet2").col_values(3)
    print(item_data)
    builder = InlineKeyboardBuilder()
    for button in item_data:
        builder.row(InlineKeyboardButton(
            text=f'{button}',
            callback_data=f'{button}'))
    await callback.message.answer(
        "Выберите место нахождения прибора",
        reply_markup=builder.as_markup()
    )
    await state.set_state(FSMFillForm.change_storage)

@dp.callback_query(StateFilter(FSMFillForm.change_storage)) #это обработчик смены места хранения прибора когда сделан выбор

async def change_pribor_storage(callback: CallbackQuery, state: FSMContext):
    pribor_id = await state.get_data()
    pribor_number = pribor_id['pribor']


    print(callback.data)

    sh.worksheet("sheet1").update_cell(pribor_number, 7, callback.data)
    await show_pribor_info_list(callback, state)



@dp.callback_query(StateFilter(FSMFillForm.change_info), #это обработчик смены даты прибора из общего списка
                   F.data.in_(['pr_date']))
async def change_pribor_date(callback: CallbackQuery, state: FSMContext):

    await callback.message.answer(
        "Выберите новую дату поверки прибора",

    )
    await state.set_state(FSMFillForm.fill_date)


@dp.callback_query(StateFilter(FSMFillForm.change_info),  # это обработчик смены названия прибора из общего списка
                   F.data.in_(['pr_name']))
async def change_pribor_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Выберите новое имя прибора",

    )
    await state.set_state(FSMFillForm.fill_name)


@dp.message(StateFilter(FSMFillForm.fill_name) ) # это обработчик смены названия прибора из общего списка когда сделан выбор
async def change_pribor_newname(message: Message, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "name"

    name = message.text

    pribor_id = await state.get_data()
    pribor_number = pribor_id['pribor']
    sh.worksheet("sheet1").update_cell(pribor_number, 2, name)
    await show_pribor(pribor_number, message,state)


@dp.callback_query(StateFilter(FSMFillForm.change_info),  # это обработчик смены номера прибора из общего списка
                   F.data.in_(['pr_number']))
async def change_pribor_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Выберите новый номер прибора",

    )
    await state.set_state(FSMFillForm.fill_number)


@dp.message(StateFilter(FSMFillForm.fill_number) ) # это обработчик смены номера прибора из общего списка когда сделан выбор
async def change_pribor_newname(message: Message, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "name"

    number = message.text

    pribor_id = await state.get_data()
    pribor_number = pribor_id['pribor']
    sh.worksheet("sheet1").update_cell(pribor_number, 3, number)
    await show_pribor(pribor_number, message,state)






async def show_pribor(b,message,state):


    item_data = sh.worksheet("sheet1").get('A' + b + ':G' + b)
    # Создаем объекты инлайн-кнопок
    photo_button = InlineKeyboardButton(text='Изменить фото',
                                        callback_data='ch_photo')
    info_button = InlineKeyboardButton(text='Изменить описание',
                                       callback_data='ch_info')

    # Добавляем кнопки в клавиатуру (две в одном ряду и одну в другом)
    keyboard: list[list[InlineKeyboardButton]] = [
        [photo_button, info_button]]
    # Создаем объект инлайн-клавиатуры
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    # Отправляем пользователю сообщение с клавиатурой
    photo = FSInputFile(f"{b}.jpg")

    await message.answer(


        text=f'Тип прибора: {item_data[0][0]}\n'
             f'Название: {item_data[0][1]}\n'
             f'Номер: {item_data[0][2]}\n'
             f'Дата поверки: {item_data[0][3]}\n'
             f'Состояние: {item_data[0][4]}\n'
             f'Находится: {item_data[0][5]}\n'
             f'Постоянное место: {item_data[0][6]}',
        reply_markup=markup)
    await state.set_state(FSMFillForm.fill_date)


async def show_pribor_from_list(pribor_number,callback,state): #показывает карточку прибора из списка поверки

    pribor_number = int(pribor_number) + 1
    pribor_number = str(pribor_number)

    y.download(f"{pribor_number}.jpg", f"{pribor_number}.jpg")
    photo = FSInputFile(f"{pribor_number}.jpg")
    await callback.message.reply_photo(photo)




    item_data = sh.worksheet("sheet1").get('A' + pribor_number+ ':G' + pribor_number)

    await callback.message.answer(


        text=f'Тип прибора: {item_data[0][0]}\n'
             f'Название: {item_data[0][1]}\n'
             f'Номер: {item_data[0][2]}\n'
             f'Дата поверки: {item_data[0][3]}\n'
             f'Состояние: {item_data[0][4]}\n'
             f'Находится: {item_data[0][5]}\n'
             f'Постоянное место: {item_data[0][6]}' )


    os.remove(f"{pribor_number}.jpg")
    await state.set_state(FSMFillForm.show_from_list_state)

async def show_pribor_info_list(callback, state):
    pribor_id = await state.get_data()
    pribor_number = pribor_id['pribor']

    item_data = sh.worksheet("sheet1").get('A' + pribor_number + ':G' + pribor_number)

    typ_button = InlineKeyboardButton(text=f'Тип прибора: {item_data[0][0]}', callback_data='pr_type')
    nam_button = InlineKeyboardButton(text=f'Название: {item_data[0][1]}', callback_data='pr_name')
    num_button = InlineKeyboardButton(text=f'Номер: {item_data[0][2]}', callback_data='pr_number')
    dat_button = InlineKeyboardButton(text=f'Дата поверки: {item_data[0][3]}', callback_data='pr_date')
    sta_button = InlineKeyboardButton(text=f'Состояние: {item_data[0][4]}', callback_data='pr_status')
    loc_button = InlineKeyboardButton(text=f'Находится: {item_data[0][5]}', callback_data='pr_location')
    sto_button = InlineKeyboardButton(text=f'Постоянное место: {item_data[0][6]}', callback_data='pr_storage')

    # Добавляем кнопки в клавиатуру (две в одном ряду и одну в другом)
    keyboard: list[list[InlineKeyboardButton]] = [
        [typ_button], [nam_button], [num_button], [dat_button], [sta_button], [loc_button], [sto_button]]
    # Создаем объект инлайн-клавиатуры
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    # Отправляем пользователю сообщение с клавиатурой

    await callback.message.answer(

        text=f'Тип прибора: {item_data[0][0]}\n'
             f'Название: {item_data[0][1]}\n'
             f'Номер: {item_data[0][2]}\n'
             f'Дата поверки: {item_data[0][3]}\n'
             f'Состояние: {item_data[0][4]}\n'
             f'Находится: {item_data[0][5]}\n'
             f'Постоянное место: {item_data[0][6]}',
        reply_markup=markup)
    await state.set_state(FSMFillForm.change_info)






# Запускаем поллинг
if __name__ == '__main__':
    dp.run_polling(bot)