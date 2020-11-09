from config import *
# from main import  make_goods_buttons_for_delete
from DbHandler import db
import re
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from main import make_goods_buttons_for_delete


def handle_position(update, context):
    text = "Добавить/Удалить позицию из категории"
    command, categ, place = update.callback_query.data.split (';')

    buttons = [[
        InlineKeyboardButton("Добавить позицию", callback_data=str(ADD_NEW_POSITION)+';'+str(categ)+';'+str(place)),
        InlineKeyboardButton("удалить позицию", callback_data=str(DELETE_POSITION)+';'+str(categ)+';'+str(place))],
        [InlineKeyboardButton("Назад ⬅️", callback_data=str(categ)+';'+str(place))]
    ]
    kb = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text (text=text, reply_markup=kb)


def add_new_position(update, context):
    text = "Введите название позиции, через запятую введите единицы измерения\nНапример: Куриное филе, кг."
    command ,categ, place = update.callback_query.data.split(';')
    context.user_data['categ'] = categ
    context.user_data['place'] = place

    buttons = [[
        InlineKeyboardButton("Назад ⬅️",    callback_data=str(categ)+';'+str(place))
    ]]
    kb = InlineKeyboardMarkup(buttons)

    update.callback_query.answer ( )
    update.callback_query.edit_message_text (text=text, reply_markup=kb)

    return TYPING

def delete_position(update, context):
    text = "Выберите позицию для удаления: "
    command, categ, place = update.callback_query.data.split(';')
    goods = make_goods_buttons_for_delete(categ, place)
    goods.append([InlineKeyboardButton("Назад ⬅️", callback_data=str(categ)+';'+str(place))])

    kb = InlineKeyboardMarkup(goods)
    update.callback_query.answer()
    update.callback_query.edit_message_text (text=text, reply_markup=kb)

    return SELECTING_PLACE


def new_position_handler(update, context):
    data = update.message.text
    if re.match(r'^(\s*\w+\s*)+,(\s*\w+\.*)+\s*$', data) is not None:
        name, units = data.split(',')
        try:
            db.add_to_goods(name.strip(), units.strip(), context.user_data['categ'])
            # context.user_data['categ'] = None
            s_mes = context.bot.send_message (update.message.chat_id,
                                              'Позиция "' + name.strip() + '" успешно добавлена')

        except Exception as e:
            if str(e) == 'UNIQUE constraint failed: goods.name':
                text = 'Ошибка.\nДанный товар уже присутствует в таблице'
            else:
                text = 'Произошла ошибка, обратитесь к разработчику'
            print("Oopse, someth wrong \n" + str(e)+ str(e.args))
            s_mes = context.bot.send_message (update.message.chat_id, text)

        def message_deleter(cont) :
            cont.bot.delete_message (update.message.chat_id, update.message.message_id)
            cont.bot.delete_message (update.message.chat_id, s_mes['message_id'])

        context.job_queue.run_once(message_deleter, DELETE_MESSAGE_PAUSE)

    else:
        er_mes = context.bot.send_message(update.message.chat_id, 'Неверный ввод!')

        def message_deleter(cont) :
            cont.bot.delete_message (update.message.chat_id, update.message.message_id)
            cont.bot.delete_message (update.message.chat_id, er_mes['message_id'])

        context.job_queue.run_once (message_deleter, DELETE_MESSAGE_PAUSE)
