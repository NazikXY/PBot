from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import *
# from main import make_pairlist_from_list
from DbHandler import db

def make_pairlist_from_list(gl):
    f = []
    s = []
    flag = 0
    res = []
    for i in gl:
        if flag:
            f.append(i)
            flag = 0
        else:
            s.append(i)
            flag = 1
    while True:
        if len(f) + len(s) <= 0:
            break
        tmp = []
        if len(f) > 0:
            tmp.append(f.pop())
        if len (s) > 0:
            tmp.append (s.pop ( ))
        res.append (tmp)
    return res

def text_order_list(order) :

    result = '\n'

    if order is not None:
        for i in order:
            product = db.get_goods_by_id(i[0])
            if product is None:
                continue
            result += product[1] + ' ' + str(i[1]) +' '+ product[2] +'\n'


    def str_sort(st):
        tmp = st.splitlines()
        tmp.sort()
        rs = ''
        for line in tmp:
            rs += line + '\n'
        return rs

    result = str_sort(result)

    return result


def orders_start(update, context):
    pass
#
#     order_is_present = db.order_is_present()
#     order = None
#     if order_is_present:
#         text, order = db.get_current_order()
#         places = [[InlineKeyboardButton("Добавить продукты", callback_data=str(SELECTING_PLACE))],
#                   [InlineKeyboardButton("Закрыть", callback_data=str(CLOSING_ORDER)),
#                    InlineKeyboardButton("Удалить", callback_data=str(DELETING_ORDER))],
#                   [InlineKeyboardButton("Назад ⬅️", callback_data=str(START))]]
#     else:
#         places = [[InlineKeyboardButton("Создать заказ", callback_data=str(CREATING_ORDER)),
#                    InlineKeyboardButton("Выбрать из истории", callback_data=str(HISTORY))
#                    ],
#                   [InlineKeyboardButton("Назад ⬅️", callback_data=str(START))]]
#         text = "Сейчас у вас нет заказа"
#
#     goods_list = db.get_goods_list_by_category()
#
#     all_text = text_order_list(goods_list, order)
#
#     text = all_text + 'Ваш заказ: ' + text
#     kb = InlineKeyboardMarkup(places)
#
#     # если /start не в первый раз запукается, то отрабатывает try
#     try:
#         update.callback_query.answer()
#         update.callback_query.edit_message_text(text, reply_markup=kb)
#     except Exception as e:
#         update.message.reply_text(text, reply_markup=kb)
#
#     return ORDERS_START


def add_to_order(update, context):
    places = [[InlineKeyboardButton("Кухня", callback_data=str(KITCHEN)),
               InlineKeyboardButton("Бар", callback_data=str(BAR)),
               InlineKeyboardButton("Цех", callback_data=str(ZEH)),
               InlineKeyboardButton("Ц-6", callback_data=str(Z_6)),
               ],
              [InlineKeyboardButton('Назад ⬅️', callback_data=str(START))]
              ]
    kb = InlineKeyboardMarkup(places)

    update.callback_query.answer()
    update.callback_query.edit_message_text('Куда? ', reply_markup=kb)

    return SELECTING_PLACE

def delete_from_order(update, context):
    command, place = update.callback_query.data.split(';')
    table_name, order = db.get_order(place)
    button_list = []

    for i in order:
        button_list.append(InlineKeyboardButton(db.get_goods_name_by_id(i[0]) + " ➖", callback_data=str(DELETE_FROM_ORDER)+';'+str(i[0])+';'+str(place)))
    buttons = make_pairlist_from_list(button_list)
    buttons.append([InlineKeyboardButton("Назад", callback_data=str(place))])

    kb = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text('Что хотите удалить?', reply_markup=kb)


def delete_order_item(update, context):
    command, id, place = update.callback_query.data.split(';')
    update.callback_query.answer()
    db.delete_from_order_by_id(place, id)
    return

def change_order(update, context):
    order_list = db.get_order_list()
    orders = []
    for i in order_list:
        orders.append([InlineKeyboardButton(str(i[0]) + ' ' + i[1], callback_data=str(HISTORY) + str(i[0]))])
    orders.append([InlineKeyboardButton('Назад ⬅️', callback_data=str(END))])
    kb = InlineKeyboardMarkup(orders)

    update.callback_query.answer()
    update.callback_query.edit_message_text("Прошлые заказы: ", reply_markup=kb)


def close_order(update, context):
    command, place = update.callback_query.data.split(';')
    context.user_data["place"] = place
    context.user_data["query_messg"] = update.callback_query.message.message_id

    buttons = [[InlineKeyboardButton ("Назад", callback_data=str (place))]]

    kb = InlineKeyboardMarkup (buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text='Введите и отправьте номер: ', reply_markup=kb)

    return TYPING_TNUMBER

def number_handler(update, context):
    context.bot.delete_message (update.message.chat_id, context.user_data["query_messg"])
    context.bot.delete_message (update.message.chat_id, update.message.message_id)

    db.close_order(context.user_data["place"], update.message.text)
    buttons = [[InlineKeyboardButton("Кухня", callback_data=str(KITCHEN)),
               InlineKeyboardButton("Бар", callback_data=str(BAR)),
               InlineKeyboardButton("Цех", callback_data=str(ZEH)),
               InlineKeyboardButton("Ц-6", callback_data=str(Z_6)),
               ],
              [InlineKeyboardButton('Назад ⬅️', callback_data=str(START))]
              ]

    kb = InlineKeyboardMarkup(buttons)

    update.message.reply_text("Готово, заказ отправлен к абоненту с номером "+update.message.text, reply_markup=kb)
    return SELECTING_PLACE
