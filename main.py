from threading import Thread
from time import sleep

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from auth import TOKEN
from config import *
from reporting import *
import logging
from DbHandler import DBHandler
import re

# TODO настроить работу бд, работу  таблицами кухни и прочего


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


db = DBHandler('bot.db')

class PlaceHolder:
    place = None
    table = 0
    category = None
    product = None

    def __init__(self, place):
        self.place = place

class Holder:
    places = {
        KITCHEN : PlaceHolder(KITCHEN),
        BAR : PlaceHolder(BAR),
        ZEH : PlaceHolder(ZEH),
        Z_6 : PlaceHolder(Z_6)
    }


# def hidden_process():
#     while True:
#         db.close_old_order()
#         sleep(60)


def start(update, context):
    text = 'Что будете делать?'
    buttons = [[InlineKeyboardButton('Отчетность', callback_data=str(REPORTING)),
                # InlineKeyboardButton ('Приход', callback_data=str (REPORTING)),
                # InlineKeyboardButton ('Списание', callback_data=str (REPORTING)),
                InlineKeyboardButton('Базар', callback_data=str(ORDERS_START))]]
    kb = InlineKeyboardMarkup(buttons)
    # Thread(target=hidden_process, daemon=True).start()


    # если /start не в первый раз запукается, то отрабатывает try
    try:
        update.callback_query.answer()
        update.callback_query.edit_message_text(text, reply_markup=kb)
    except Exception as e:
        update.message.reply_text(text, reply_markup=kb)

    return START

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
    #
    # kitchen_txt = '\n\n**Кухня** \n\n' #+ str_sort(kitchen_txt)
    # bar_txt = '\n** Бар ** \n\n'# + str_sort(bar_txt)
    # zeh_txt = '\n** Цех ** \n\n'# + str_sort(zeh_txt)
    #
    # result = kitchen_txt + bar_txt + zeh_txt

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



def create_order(update, context):
    buttons = [[InlineKeyboardButton('Назад ⬅️', callback_data=str(END))]]
    kb = InlineKeyboardMarkup(buttons)

    new_order = db.create_order()

    update.callback_query.answer()

    if not new_order[1]:
        update.callback_query.edit_message_text(
            'Новый заказ не был создан. \nДля создания нового заказа закройте текущий, текущий заказ: ' + new_order[0],
            reply_markup=kb)
    else:
        update.callback_query.edit_message_text(
            'Заказ успешно создан, название таблицы: ' + new_order[0], reply_markup=kb)


def delete_order(update, context):
    # db.delete_order()
    return orders_start(update, context)


def change_order(update, context):
    order_list = db.get_order_list()
    orders = []
    for i in order_list:
        orders.append([InlineKeyboardButton(str(i[0]) + ' ' + i[1], callback_data=str(HISTORY) + str(i[0]))])
    orders.append([InlineKeyboardButton('Назад ⬅️', callback_data=str(END))])
    kb = InlineKeyboardMarkup(orders)

    update.callback_query.answer()
    update.callback_query.edit_message_text("Прошлые заказы: ", reply_markup=kb)



def choose_old_order(update, context):
    db.set_current_order_from_history(int(update.callback_query.data))

    update.callback_query.answer()
    return orders_start(update, context)


def close_order(update, context):
    command, place = update.callback_query.data.split(';')
    db.close_order(place)
    buttons = [[InlineKeyboardButton("Окей", callback_data=str(place))]]

    kb = InlineKeyboardMarkup(buttons)


    update.callback_query.answer()
    update.callback_query.edit_message_text(text='Ваш заказ успешно закрыт, наверное', reply_markup=kb)



def send_order(update, context):
    pass
    # TODO


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


def choose_category(update, context, place=None):
    place_names = {KITCHEN: 'Кухня\n',
                  BAR:'Бар\n',
                  ZEH:'Цех\n',
                  Z_6:'Ц-6\n'}
    order_name, order = db.get_order(place.place)
    text = text_order_list(order)
    print(text)

    buttons = [
        [
            InlineKeyboardButton("Овощи 🍆🥕🥔", callback_data=str(VEGS)+';'+str(place.place)),
            InlineKeyboardButton("Фрукты 🍉🍎🍇", callback_data=str(FRUIT)+';'+str(place.place)),
            InlineKeyboardButton("Зелень 🌿", callback_data=str(GREENS)+';'+str(place.place)),
            InlineKeyboardButton("Мясное 🍖", callback_data=str(MEAT)+';'+str(place.place))
        ],
        [
            InlineKeyboardButton("Орехи/сухофрукты 🌰", callback_data=str(NUTS_DRIED_FRUIT)+';'+str(place.place)),
            InlineKeyboardButton("Молочное 🥛", callback_data=str(MILK)+';'+str(place.place)),
            InlineKeyboardButton("Напитки 🧃", callback_data=str(DRINK)+';'+str(place.place))
        ],
        [
            InlineKeyboardButton ("Удалить из заказа ❌", callback_data=str (DELETE_FROM_ORDER) + ';' + str(place.place)),
            InlineKeyboardButton ("Закрыть заказ! ✅", callback_data=str(CLOSING_ORDER)+';'+place.place)
        ],
        [
            InlineKeyboardButton ("Назад ⬅️", callback_data=str(END)),
        ]
    ]

    kb = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(place_names[place.place] + text + "\nВыберите категорию: ", reply_markup=kb)



def make_goods_buttons(category, place):
    goods = []
    gl = db.get_goods_list_by_category(category)
    res = make_pairlist_from_list (gl)
    for pair in res :
        IKB_pair = []
        for item in pair :
            IKB_pair.append (InlineKeyboardButton (item[1], callback_data=str(item[0])+';'+str(category)+';'+str(place)))
        goods.append (IKB_pair)
    return goods

def make_goods_buttons_for_delete(category, place):
    goods = []
    gl = db.get_goods_list_by_category(category)
    res = make_pairlist_from_list (gl)
    for pair in res :
        IKB_pair = []
        for item in pair :
            IKB_pair.append (InlineKeyboardButton (item[1], callback_data=str(DELETE_POSITION)+';'+str(item[0])+';'+str(category)+';'+str(place)))
            print(str(DELETE_POSITION)+';'+str(item[0])+';'+str(category)+';'+str(place))
        goods.append (IKB_pair)
    return goods

def select_place(update, context):

    place = update.callback_query.data
    if Holder.places[place].table is None:
        buttons = [[InlineKeyboardButton("Создать заказ", callback_data=str(CREATING_ORDER) + str(place))],
                   [InlineKeyboardButton("Назад ⬅️", callback_data=str(END))]]
        kb = InlineKeyboardMarkup(buttons)
        update.callback_query.answer()
        update.callback_query.edit_message_text("Предыдущий заказ закрыт, создайте новый", reply_markup=kb)
    else: return choose_category(update, context, place=Holder.places[place])



def select_goods(update, context):
    data = update.callback_query.data
    categ, place = data.split(';')
    place_names = {KITCHEN : 'Кухня\n',
                   BAR : 'Бар\n',
                   ZEH : 'Цех\n',
                   Z_6 : 'Ц-6\n'}
    order_name, order = db.get_order (place)
    text = text_order_list (order)
    print(categ)
    print(place)
    goods = make_goods_buttons(categ, place)

    goods.append([InlineKeyboardButton("Редактировать 🛠", callback_data=str(HANDLE_POSITION)+';'+str(categ)+';'+str(place)),
                  InlineKeyboardButton("Назад ⬅️", callback_data=str(place))])

    kb = InlineKeyboardMarkup(goods)

    update.callback_query.answer()
    update.callback_query.edit_message_text(place_names[place] + text + "Заказ: ", reply_markup=kb)

    return SELECTING_PLACE


def product_handler(update, context):
    gid, categ, place = update.callback_query.data.split(';')

    buttons = [[InlineKeyboardButton("Назад ⬅️", callback_data=str(categ)+';'+str(place))]]
    kb = InlineKeyboardMarkup(buttons)
    context.user_data['gid'] = gid
    context.user_data['categ'] = categ
    context.user_data['place'] = place

    update.callback_query.answer()
    try:
        current_product = db.get_goods_by_id(gid)
        update.callback_query.edit_message_text(
            "Введите сколько {} {} нужно добавить\nЧто бы уменьшить количество напишите число с минусом ( -5, -7)"
                .format(current_product[2] , current_product[1]), reply_markup=kb)
    except Exception as e:
        print(e)

    return TYPING_COUNT

def product_deleter(update, context):
    command, product, categ, place = update.callback_query.data.split(';')
    butons = [[InlineKeyboardButton("Назад ⬅️", callback_data=command+';'+categ+';'+place)]]
    update.callback_query.answer()
    db.delete_from_goods(product)


    # for i in dir(update.callback_query.message):
    #     print(eval("update.callback_query.message."+i))
    update.callback_query.edit_message_text("Успешно удалено", reply_markup=InlineKeyboardMarkup(butons))


def add_goods_count(update, context):
    data = update.message.text
    res = re.match(r'^\s*-*((\d+\.+\d{1,2})|(\d+))\s*$', data)

    if res is not None:
        gid = context.user_data['gid']
        categ = context.user_data['categ']
        place = context.user_data['place']
        count = res[0]
        current_product = db.get_goods_by_id(gid)
        try:
            db.add_to_order(gid=gid, category=categ, place=place, count=count)
            s_mes = context.bot.send_message (update.message.chat_id,
                                              count + ' ' + current_product[2] + ' ' + current_product[1] + " Готово!")

            def message_deleter(cont) :
                cont.bot.delete_message (update.message.chat_id, update.message.message_id)
                cont.bot.delete_message (update.message.chat_id, s_mes['message_id'])

            context.job_queue.run_once (message_deleter, DELETE_MESSAGE_PAUSE - 2)

        except Exception as e:
            print(e)


def returning(update, context):

    update.callback_query.answer()
    select_goods(update, context)

    return SELECTING_PLACE

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
    update.callback_query.answer ( )
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


def stop(update, context):
    pass


def cleaner(update, context):
    context.bot.delete_message(update.message.chat_id, update.message.message_id)
    for i in range(3, update.message.message_id):
        try:
            context.bot.delete_message(update.message.chat_id, update.message.message_id-i-1)
        except Exception as e:
            pass


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [CallbackQueryHandler(add_to_order,              pattern='^' + str(ORDERS_START)+'$'),
                    CallbackQueryHandler(reporting,                 pattern='^' + str(REPORTING)+'$')],

            REPORTING: [CallbackQueryHandler(get_report,            pattern='^' + str(GET_REPORT)+'$'),
                        CallbackQueryHandler(get_report_xlsx,       pattern='^' + str(GET_REPORT_XLSX)+'$'),
                        CallbackQueryHandler(reporting,             pattern='^' + str(REPORTING)+'$'),
                        CallbackQueryHandler(deep_report,           pattern='^' + str (KITCHEN_REPORT) +
                                                                            '|' + str(BAR_REPORT) +
                                                                            '|' + str(ZEH_REPORT) + '$'),
                        CallbackQueryHandler(start,                 pattern='^' + str(START)+'$')],

            ORDERS_START: [CallbackQueryHandler(create_order,       pattern='^' + str(CREATING_ORDER)+'$'),
                           CallbackQueryHandler(change_order,       pattern='^' + str(HISTORY) + '$'),
                           CallbackQueryHandler(delete_order,       pattern='^' + str(DELETING_ORDER)+'$'),
                           CallbackQueryHandler(choose_old_order,   pattern='^' + str(HISTORY) + '\d*$'),
                           CallbackQueryHandler(close_order,        pattern='^' + str(CLOSING_ORDER)+'$'),
                           CallbackQueryHandler(add_to_order,       pattern='^' + str(SELECTING_PLACE) + '$'),
                           CallbackQueryHandler(start,              pattern='^' + str(START)+'$'),
                           CallbackQueryHandler(orders_start,       pattern='^' + str(END)+'$')],

            SELECTING_PLACE: [CallbackQueryHandler(select_place,    pattern='^' + reg_place_str+'$'),
                              CallbackQueryHandler(close_order,     pattern='^' + str(CLOSING_ORDER) + ';+'+reg_place_str+'$'),
                              CallbackQueryHandler(select_goods,    pattern='^' + reg_category_str+';+'+reg_place_str+'$'),
                              CallbackQueryHandler(add_to_order,    pattern='^' + str(END)+'$'),
                              CallbackQueryHandler(delete_from_order,    pattern='^' + str(DELETE_FROM_ORDER)+';+'+reg_place_str+'$'),
                              CallbackQueryHandler(delete_order_item,    pattern='^' + str(DELETE_FROM_ORDER)+';+'+'\d+'+';+'+reg_place_str+'$'),
                              CallbackQueryHandler(start,    pattern='^' + str(START)+'$'),
                              CallbackQueryHandler(product_handler, pattern='^\d+'
                                                                            + ';+'
                                                                            + reg_category_str
                                                                            + ';+'
                                                                            + reg_place_str + '$'),
                              CallbackQueryHandler(product_deleter, pattern='^'+str(DELETE_POSITION)
                                                                            + ';+'
                                                                            + '\d+' ## number
                                                                            + ';+'
                                                                            + reg_category_str
                                                                            + ';+'
                                                                            + reg_place_str+'$'),
                              CallbackQueryHandler(handle_position,
                                                   pattern='^' + str(HANDLE_POSITION)+';+'+reg_category_str+';+'+reg_place_str+'$'),
                              CallbackQueryHandler(add_new_position,
                                                   pattern='^' + str(ADD_NEW_POSITION)+';+'+reg_category_str+';+'+reg_place_str+'$'),
                              CallbackQueryHandler(delete_position,
                                                   pattern='^' + str(DELETE_POSITION)+';+'+reg_category_str+';+'+reg_place_str+'$')
                              ],

            TYPING_COUNT:[MessageHandler(Filters.text & ~Filters.command, add_goods_count),
                          CallbackQueryHandler(select_goods,        pattern='^'+reg_category_str+';+'+reg_place_str+'$')
                          ],

            TYPING: [MessageHandler(Filters.text & ~Filters.command, new_position_handler),
                     CallbackQueryHandler(select_goods,             pattern='^'+reg_category_str+';+'+reg_place_str+'$')]
        },
        fallbacks=[CommandHandler("stop", stop)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('clear', cleaner))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

