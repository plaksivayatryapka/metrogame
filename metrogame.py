#! /usr/bin/env python
# -*- coding: utf-8 -*-

import telepot  # библиотека для телеграм
from datetime import datetime  # библиотека для времени
from functions.functions import to_int, to_float, logwrite, save_vars, load_vars  # мои функции для проверки на натуральное число, действительное, запись лога, сохранение и загрузка переменных на случай остановки скрипта
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton  # импорт клавиатуры для телеграм
from random import randint  # импорт библиотеки для генератора случайных чисел
import threading  # импорт библиотеки для распараллеливания процессов
import time  # другая библиотека для времени

token = ''  # MetroGame_bot  # идентфикатор моего бота телеграм
TelegramBot = telepot.Bot(token)
logfilename = 'logs/metrogame.txt'  # сюда писать лог
dumpfilename = 'data/metrogame_variables.pickle'  # сюда сохранять переменные
send_message = TelegramBot.sendMessage
startmessage = 'welcome! your game id is %s'
helpmessage = ''
timer = 15  # время раунда

# пример переменной, которая всё хранит. тут словарь, вложенный в другой словарь. словарь это типа массива, только тут элементы не только по номерам, но и по тексту. разделяются двоеточием.
# example: storage = {123 : {'ids' : [123, 465], 'moves_count' : None, 'game_type' : 'square', 'move_owner' : 123, 'number1' : 24, 'answers' : [450, 460], 'accuracy' : [0.95, 0.9]}}


def get_game_id(chat_id, storage):  # функция поиска номера игры по написавшему
    for key, value in storage.items():  # цикл по содержимому словаря (полю и его значению).
        if chat_id in value['ids']:  # если поле равно тому что нужно, то
            return key  # возвращает название поля
    return None


def remove_id(chat_id, storage):    # функция убрать id из игры
    for key, value in storage.items():
        if chat_id in value['ids']:
            value['ids'].remove(chat_id)


def change_move_owner(game_id, chat_id):    # смена ходящего
    if chat_id == storage[game_id]['ids'][0]:
        storage[game_id]['move_owner'] = storage[game_id]['ids'][1]
    elif chat_id == storage[game_id]['ids'][1]:
        storage[game_id]['move_owner'] = storage[game_id]['ids'][0]


def another_player(i):  # функция смены индекса с одного игрока на другого
    if i == 0:
        i = 1
    elif i == 1:
        i = 0
    return i


def start(chat_id, storage):  # функция запускаемая при вводе /start
    game_id = chat_id
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=u'Возвести в квадрат', callback_data='square')],
                                                     [InlineKeyboardButton(text=u'Перемножение чисел', callback_data='multiply')]])  # клавиатура в телеграм
    send_message(chat_id, startmessage % game_id, reply_markup=keyboard)  # отправка сообщения для клавиатуры

    if chat_id not in storage:
        remove_id(chat_id, storage)
        storage[game_id] = dict()  # обнуление всякого хлама
        storage[game_id]['ids'] = [chat_id]
        storage[game_id]['game_type'] = None
    storage[game_id]['moves_count'] = 0
    storage[game_id]['move_owner'] = storage[game_id]['ids'][0]


def connect(text, chat_id, storage):  # функция присоединения к игре
    if int(text[8:]) == chat_id:  # если первые восемь символов это число, равное идентификатору чата, то...
        send_message(chat_id, u'нельзя присоединиться к своей же игре')
        return
    if int(text[8:]) not in storage:  # if game_id exists
        send_message(chat_id, u'такой игры нет')
        return
    remove_id(chat_id, storage)
    if chat_id in storage:
        del storage[chat_id]
    storage[int(text[8:])]['ids'].append(chat_id)  # добавить айди в массив
    send_message(chat_id, u'Вы присоединились')
    for i in storage[int(text[8:])]['ids']:
        if i != chat_id:
            send_message(i, u'К вам присоединились')


def on_callback_query(msg):  # функция если нажата кнопка в телеграм
    global storage
    chat_id = msg['message']['chat']['id']
    game_id = get_game_id(chat_id, storage)
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')

    if game_id is None:
        return
    if query_data == 'square':
        storage[game_id]['game_type'] = 'square'
        storage[game_id]['moves_count'] = 0
        storage[game_id]['answers'] = list([None, None])
        storage[game_id]['accuracy'] = list([None, None])
        storage[game_id]['number1'] = None
        for i in storage[game_id]['ids']:
            send_message(i, u'Выбрана игра: квадрат. Введите разрядность числа для генератора случайных чисел')


def start_timer(game_id, chat_id, sleep_time):  # функция при старте кона. отсчитывает 15 секунд и потом проверяет кто что ответил и высылает результаты. запускается параллельным процессом
    time.sleep(sleep_time)

    if storage[game_id]['game_type'] == 'square':
        result = storage[game_id]['number1'] ** 2

    # calculating accuracy. If none - looser.

    for i in range(len(storage[game_id]['ids'])):
        if storage[game_id]['answers'][i] is None:
            storage[game_id]['accuracy'][i] = 0
            send_message(storage[game_id]['ids'][i], 'Time elapsed, you loose')
        else:
            storage[game_id]['accuracy'][i] = min(result, storage[game_id]['answers'][i]) / max(result, storage[game_id]['answers'][i])  # check accuracy?

    # comparing accuracy and sending results

    for i in range(len(storage[game_id]['ids'])):
        if storage[game_id]['accuracy'][0] == storage[game_id]['accuracy'][1]:
            send_message(storage[game_id]['ids'][i], 'same as opponent. your accuracy = %s' % str(storage[game_id]['accuracy'][i] * 100)[:4] + '%')
        elif storage[game_id]['accuracy'][i] == max(storage[game_id]['accuracy'][0], storage[game_id]['accuracy'][1]):
            send_message(storage[game_id]['ids'][i], "you win! result = %s, your accuracy = %s, opponent's accuracy = %s, opponent's answer = %s" % (result, str(storage[game_id]['accuracy'][i] * 100)[:4] + '%', str(storage[game_id]['accuracy'][another_player(i)] * 100)[:4] + '%', storage[game_id]['answers'][another_player(i)]))
        elif storage[game_id]['accuracy'][i] == min(storage[game_id]['accuracy'][0], storage[game_id]['accuracy'][1]):
            send_message(storage[game_id]['ids'][i], "you loose. result = %s, your accuracy = %s, opponent's accuracy = %s, opponent's answer = %s" % (result, str(storage[game_id]['accuracy'][i] * 100)[:4] + '%', str(storage[game_id]['accuracy'][another_player(i)] * 100)[:4] + '%', storage[game_id]['answers'][another_player(i)]))

    # if players answered, reset moves_count to zero

    while 1:  # постоянный цикл, ждёт ответа пользователя и обнуляет всё
        if storage[game_id]['moves_count'] == 3:
            storage[game_id]['moves_count'] = 0
            storage[game_id]['answers'] = list([None, None])
            storage[game_id]['accuracy'] = list([None, None])
            storage[game_id]['number1'] = None
            change_move_owner(game_id, chat_id)
            save_vars(dumpfilename, storage)  # функция сохраняет переменные
            return

        time.sleep(1)


def on_chat_message(msg):  # функция, запускаемая при отправке пользователем чё-нить в чат
    if __name__ != '__main__':
        return
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type != 'text':
        return
    print 'text = ', msg['text']
    game_id = get_game_id(chat_id, storage)
    if game_id is None:  # запись в лог времени и переменных
        logwrite(logfilename, str(datetime.now())[:-4], chat_id, msg['text'])
    else:
        logwrite(logfilename, str(datetime.now())[:-4], game_id, chat_id, storage[game_id]['moves_count'], msg['text'], storage[game_id]['game_type'])

    text = msg['text'].lower()

    if text == '/start':
        start(chat_id, storage)
        return

    elif text == '/help':
        send_message(chat_id, helpmessage)
        return

    elif text[:7] == 'connect' and to_int(text[8:]):
        connect(msg['text'], chat_id, storage)

    elif text == '/disconnect':
        remove_id(chat_id, storage)

    elif text == 'st':
        print storage
        logwrite(logfilename, str(storage))
        return

    elif text == '/kickall' and chat_id == game_id:
        for i in storage[game_id]['ids']:
            if i != chat_id:
                storage[game_id]['ids'].remove(i)

    elif text == '/games':
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=u'Возвести в квадрат', callback_data='square')],
                                                         [InlineKeyboardButton(text=u'Перемножение чисел', callback_data='multiply')]])
        send_message(chat_id, 'Игры:', reply_markup=keyboard)

    # return if no game

    elif get_game_id(chat_id, storage) is None:
        send_message(chat_id, u'кликните /start чтобы начать')
        return

    elif storage[game_id]['game_type'] is None:
        send_message(chat_id, u'выберите тип игры')
        return

    elif storage[game_id]['game_type'] == 'square':  # если игра = квадрат, то ...
        if storage[game_id]['moves_count'] == 0 and chat_id == storage[game_id]['move_owner'] and to_float(text):  # если игра квадрат, нуль ходов, ход игрока и в сообщении число, то...

            storage[game_id]['number1'] = randint(10 ** (int(text) - 1), 10 ** int(text))
            for i in storage[game_id]['ids']:
                send_message(i, u'возведите в квадрат: %s' % storage[game_id]['number1'])

            storage[game_id]['moves_count'] += 1
            timer_thread = threading.Thread(target=start_timer, args=(game_id, chat_id, timer))  # запуск функции в отдельном процессе (thread), чтобы его sleep не тормозил всю программу
            timer_thread.daemon = True
            timer_thread.start()  # сам запуск

        elif (storage[game_id]['moves_count'] == 1 or storage[game_id]['moves_count'] == 2) and to_float(text):  # если ход второй или третий, то ...
            if chat_id == storage[game_id]['ids'][0]:
                storage[game_id]['answers'][0] = float(text)
            elif chat_id == storage[game_id]['ids'][1]:
                storage[game_id]['answers'][1] = float(text)
            storage[game_id]['moves_count'] += 1

    save_vars(dumpfilename, storage)  # сохранение переменной

# функции кончились, теперь тело программы

storage = load_vars(dumpfilename)  # загрузка переменной из бекапа
if storage == 'error':
    storage = dict()

TelegramBot.message_loop({'chat': on_chat_message,
                          'callback_query': on_callback_query})  # хренотень, которая ждёт сообщения для бота в телеграм. при сообщении боту постоянно выполняется.

print ('Listening ...')

while 1:  # Keep the program running. Постоянный цикл, который не даёт программе завершиться и ждёт чего-то от бота.
    time.sleep(10)
