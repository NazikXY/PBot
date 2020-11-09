from threading import Thread
from time import sleep

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

from order import *
from position import *
from categories import choose_category, edit_category, add_category, remove_category, add_category_typing, \
    category_remover
from auth import TOKEN
from config import *
from reporting import *
import logging
from DbHandler import DBHandler
import re



logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)




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
    place_names = {KITCHEN : '*** Кухня ***\n',
                   BAR : '*** Бар ***\n',
                   ZEH : '*** Цех ***\n',
                   Z_6 : '*** Ц-6 ***\n'}
    order_name, order = db.get_order (place)
    text = text_order_list (order)
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

            # ORDERS_START: [CallbackQueryHandler(create_order,       pattern='^' + str(CREATING_ORDER)+'$'),
            #                CallbackQueryHandler(change_order,       pattern='^' + str(HISTORY) + '$'),
                           # CallbackQueryHandler(delete_order,       pattern='^' + str(DELETING_ORDER)+'$'),
                           # CallbackQueryHandler(choose_old_order,   pattern='^' + str(HISTORY) + '\d*$'),
                           # CallbackQueryHandler(close_order,        pattern='^' + str(CLOSING_ORDER)+'$'),
                           # CallbackQueryHandler(add_to_order,       pattern='^' + str(SELECTING_PLACE) + '$'),
                           # CallbackQueryHandler(start,              pattern='^' + str(START)+'$'),
                           # CallbackQueryHandler(orders_start,       pattern='^' + str(END)+'$')],

            SELECTING_PLACE: [CallbackQueryHandler(select_place,    pattern='^' + reg_place_str+'$'),
                              CallbackQueryHandler(close_order,     pattern='^' + str(CLOSING_ORDER) + ';+'+reg_place_str+'$'),
                              CallbackQueryHandler(select_goods,    pattern='^' + '\d+'+';+'+reg_place_str+'$'),
                              CallbackQueryHandler(add_to_order,    pattern='^' + str(END)+'$'),
                              CallbackQueryHandler(delete_from_order,    pattern='^' + str(DELETE_FROM_ORDER)+';+'+reg_place_str+'$'),
                              CallbackQueryHandler(delete_order_item,    pattern='^' + str(DELETE_FROM_ORDER)+';+'+'\d+'+';+'+reg_place_str+'$'),
                              CallbackQueryHandler(start,           pattern='^' + str(START)+'$'),
                              CallbackQueryHandler(edit_category,    pattern='^' + str(EDIT_CATEGORY)+';+'+reg_place_str+'$'),
                              CallbackQueryHandler(add_category,    pattern='^' + str(ADD_CATEGORY)+';+'+reg_place_str+'$'),
                              CallbackQueryHandler(remove_category,    pattern='^' + str(REMOVE_CATEGORY)+';+'+reg_place_str+'$'),
                              CallbackQueryHandler(category_remover,    pattern='^' + str(REMOVE_CATEGORY)+';+'+'\d+'+';+'+reg_place_str+'$'),


                              CallbackQueryHandler(product_handler, pattern='^\d+'
                                                                            + ';+'
                                                                            + '\d+'
                                                                            + ';+'
                                                                            + reg_place_str + '$'),
                              CallbackQueryHandler(product_deleter, pattern='^'+str(DELETE_POSITION)
                                                                            + ';+'
                                                                            + '\d+' ## number
                                                                            + ';+'
                                                                            + '\d+'
                                                                            + ';+'
                                                                            + reg_place_str+'$'),
                              CallbackQueryHandler(handle_position,
                                                   pattern='^' + str(HANDLE_POSITION)+';+'+'\d+'+';+'+reg_place_str+'$'),
                              CallbackQueryHandler(add_new_position,
                                                   pattern='^' + str(ADD_NEW_POSITION)+';+'+'\d+'+';+'+reg_place_str+'$'),
                              CallbackQueryHandler(delete_position,
                                                   pattern='^' + str(DELETE_POSITION)+';+'+'\d+'+';+'+reg_place_str+'$')
                              ],

            TYPING_COUNT:[MessageHandler(Filters.text & ~Filters.command, add_goods_count),
                          CallbackQueryHandler(select_goods,        pattern='^'+'\d+'+';+'+reg_place_str+'$')
                          ],

            TYPING: [MessageHandler(Filters.text & ~Filters.command, new_position_handler),
                     CallbackQueryHandler(select_goods,             pattern='^'+'\d+'+';+'+reg_place_str+'$')],

            TYPING_CATEGORY:[MessageHandler(Filters.text & ~Filters.command, add_category_typing),
                             CallbackQueryHandler(edit_category,       pattern='^'+str(EDIT_CATEGORY)+';+'+reg_place_str+'$')],

            TYPING_TNUMBER:[MessageHandler(Filters.text & ~Filters.command, number_handler),
                             CallbackQueryHandler(select_place,        pattern='^'+reg_place_str+'$')]
        },
        fallbacks=[CommandHandler("stop", stop)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('clear', cleaner))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

