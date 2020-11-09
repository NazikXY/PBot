from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import *
from DbHandler import db
from order import text_order_list, make_pairlist_from_list


def get_categories_btn(value):
    blist = []
    Categories = db.get_categories_list ( )

    for i in Categories :
        blist.append (InlineKeyboardButton (i[1], callback_data=str (i[0]) + ';' + str (value)))

    result = make_pairlist_from_list (blist)
    return result

def choose_category(update, context, place=None):
    place_names = {KITCHEN : '*** Кухня ***\n',
                   BAR : '*** Бар ***\n',
                   ZEH : '*** Цех ***\n',
                   Z_6 : '*** Ц-6 ***\n'}
    order_name, order = db.get_order(place.place)
    text = text_order_list(order)
    result = get_categories_btn(place.place)
    result.append([
            InlineKeyboardButton ("Удалить из заказа ❌", callback_data=str (DELETE_FROM_ORDER) + ';' + str(place.place)),
            InlineKeyboardButton ("Закрыть заказ! ✅", callback_data=str(CLOSING_ORDER)+';'+place.place)
    ])
    result.append([InlineKeyboardButton("Ред. категории 🛠", callback_data=str(EDIT_CATEGORY)+ ';' + str(place.place)),
                   InlineKeyboardButton("Назад ⬅️", callback_data=str(END))])

    kb = InlineKeyboardMarkup(result)

    update.callback_query.answer()
    update.callback_query.edit_message_text(place_names[place.place] + text + "\nВыберите категорию: ", reply_markup=kb)


def edit_category(update, context):
    command, place = update.callback_query.data.split(';')
    buttons=[[InlineKeyboardButton("➕ Добавить категорию", callback_data=str(ADD_CATEGORY)+';'+str(place)),
              InlineKeyboardButton("➖ Удалить категорию", callback_data=str(REMOVE_CATEGORY)+';'+str(place))],
             [InlineKeyboardButton("Назад", callback_data=str(place))]]


    kb = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text("Редактировать категории: \n При удалении категории все товары в ней так же удаляются", reply_markup=kb)

    return SELECTING_PLACE

def add_category(update, context):
    command, place = update.callback_query.data.split(';')
    kb = InlineKeyboardMarkup.from_button(InlineKeyboardButton("Назад", callback_data=str(EDIT_CATEGORY)+';'+str(place)))
    update.callback_query.answer()
    update.callback_query.edit_message_text("Ведите и отправьте имя категории: ", reply_markup=kb)

    return TYPING_CATEGORY

def add_category_typing(update, context):

    try :
        db.new_category(update.message.text[:12])
        s_mes = context.bot.send_message (update.message.chat_id,
                                          'Категория "' + update.message.text[:12] + '" успешно добавлена')

    except Exception as e :
        if str (e) == 'UNIQUE constraint failed: goods.name' :
            text = 'Ошибка.\nДанная категория уже присутствует в таблице'
        else :
            text = 'Произошла ошибка, обратитесь к разработчику'
        print ("Oopse, someth wrong \n" + str (e) + str (e.args))
        s_mes = context.bot.send_message (update.message.chat_id, text)

    def message_deleter(cont) :
        cont.bot.delete_message (update.message.chat_id, update.message.message_id)
        cont.bot.delete_message (update.message.chat_id, s_mes['message_id'])

    context.job_queue.run_once (message_deleter, DELETE_MESSAGE_PAUSE)


def remove_category(update, context):
    command, place = update.callback_query.data.split(';')
    categories = db.get_categories_list()
    btn_list = []
    for i in categories:
        btn_list.append(InlineKeyboardButton(i[1], callback_data=str(REMOVE_CATEGORY)+';'+str(i[0])+';'+str(place)))
    result = make_pairlist_from_list(btn_list)
    result.append([InlineKeyboardButton("Назад", callback_data=str(EDIT_CATEGORY)+';'+str(place))])

    kb = InlineKeyboardMarkup(result)
    update.callback_query.answer()
    update.callback_query.edit_message_text("Выберите категорию для удаления: \n!!!Предупреждение!!!: все товары в категории так же удалятся", reply_markup=kb)

def category_remover(update, context):
    command, categ, place = update.callback_query.data.split(';')
    db.delete_category(categ)

    update.callback_query.answer()

    new_update = update
    new_update.callback_query.data = command + ';' + place
    return remove_category(new_update, context)

