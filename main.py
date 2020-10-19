from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from config import TOKEN
import logging
from DbHandler import DBHandler
import re



logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

START, STOP = map(chr, range(2))
SELECTING_PLACE, KITCHEN, BAR, ZEH, ADD_NEW_POSITION, ADD = map(chr, range(2, 8))
CREATING_ORDER, SENDING_ORDER, HISTORY, CHANGING_ORDER, CLOSING_ORDER, DELETING_ORDER, TYPING = map(chr, range(8, 15))
END = ConversationHandler.END

DELETE_MESSAGE_PAUSE = 5

db = DBHandler('bot.db')


def text_order_list(ls, order) :
    main_dict = {1: dict(), 2: dict(), 3: dict()}

    for i in ls :
        main_dict[i[3]][i[0]] = (i[1], i[2])

    kitchen_txt = ''
    bar_txt = ''
    zeh_txt = ''

    if order is not None:
        for i in order:
            if i[0] in main_dict[1].keys():
                kitchen_txt += main_dict[1][i[0]][0] + ' ' + str(i[1]) + ' ' + main_dict[1][i[0]][1] + '\n'
                # += main_dict[1]['names'][0] + ' ' + str(i[1]) + main_dict[1]['names'][1] + '\n'
            if i[0] in main_dict[2].keys():
                bar_txt += main_dict[2][i[0]][0] + ' ' + str(i[1]) + ' ' + main_dict[2][i[0]][1] + '\n'
                # main_dict[2]['names'][0] + ' ' + str(i[1]) + main_dict[1]['names'][1] + '\n'
            if i[0] in main_dict[3].keys():
                zeh_txt += main_dict[3][i[0]][0] + ' ' + str(i[1]) + ' ' + main_dict[3][i[0]][1] + '\n'
                # += main_dict[3]['names'][0] + ' ' + str(i[1]) + main_dict[1]['names'][1] + '\n'
    else:
        return ''

    def str_sort(st):
        tmp = st.splitlines()
        tmp.sort()
        rs = ''
        for line in tmp:
            rs += line + '\n'
        return rs

    kitchen_txt = '**Кухня** \n\n' + str_sort(kitchen_txt)
    bar_txt = '\n** Бар ** \n\n' + str_sort(bar_txt)
    zeh_txt = '\n** Цех ** \n\n' + str_sort(zeh_txt)

    result = kitchen_txt + bar_txt + zeh_txt

    return result


def start(update, context):

    order_is_present = db.order_is_present()
    order = None
    if order_is_present:
        text, order = db.get_current_order()
        places = [[InlineKeyboardButton("Добавить продукты", callback_data=str(SELECTING_PLACE)),
                   InlineKeyboardButton("Закрыть заказ", callback_data=str(CLOSING_ORDER)),
                   InlineKeyboardButton("Удалить заказ", callback_data=str(DELETING_ORDER))

                   ]]
    else:
        places = [[InlineKeyboardButton("Создать заказ", callback_data=str(CREATING_ORDER)),
                   InlineKeyboardButton("Выбрать из истории", callback_data=str(CHANGING_ORDER))
                   ]]
        text = "Сейчас у вас нет заказа"

    goods_list = db.get_goods_list(1) + db.get_goods_list(2) + db.get_goods_list(3)

    all_text = text_order_list(goods_list, order)

    text = all_text + 'Ваш заказ: ' + text
    kb = InlineKeyboardMarkup(places)

    # если /start не в первый раз запукается, то отрабатывает try
    try:
        update.callback_query.answer()
        update.callback_query.edit_message_text(text, reply_markup=kb)
    except Exception as e:
        update.message.reply_text(text, reply_markup=kb)

    return START


def add_to_order(update, context):
    places = [[InlineKeyboardButton("Кухня", callback_data=str(KITCHEN)),
               InlineKeyboardButton("Бар", callback_data=str(BAR)),
               InlineKeyboardButton("Цех", callback_data=str(ZEH))],
              [InlineKeyboardButton('Назад', callback_data=str(END))]
              ]
    kb = InlineKeyboardMarkup(places)

    update.callback_query.answer()
    update.callback_query.edit_message_text('Куда? ', reply_markup=kb)

    return SELECTING_PLACE


def create_order(update, context):
    buttons = [[InlineKeyboardButton('Назад', callback_data=str(END))]]
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
    db.delete_order()
    return start(update, context)


def change_order(update, context):
    order_list = db.get_order_list()
    orders = []
    for i in order_list:
        orders.append([InlineKeyboardButton(str(i[0]) + ' ' + i[1], callback_data=str(CHANGING_ORDER)+str(i[0]))])
    orders.append([InlineKeyboardButton('Назад', callback_data=str(END))])
    kb = InlineKeyboardMarkup(orders)

    update.callback_query.answer()
    update.callback_query.edit_message_text("Прошлые заказы: ", reply_markup=kb)


def choose_old_order(update, context):
    db.set_current_order_from_history(int(update.callback_query.data))

    update.callback_query.answer()
    return start(update, context)


def close_order(update, context):
    db.close_order()
    buttons = [[InlineKeyboardButton("Окей", callback_data=str(END))]]
    kb = InlineKeyboardMarkup(buttons)

    db.close_order()

    update.callback_query.answer()
    update.callback_query.edit_message_text(text='Ваш заказ успешно закрыт, наверное', reply_markup=kb)

    return START


def send_order(update, context):
    pass
    # TODO


def select_kitchen(update, context):
    goods = []
    for i in db.get_goods_list(1):
        goods.append([InlineKeyboardButton(i[1] + str(' + 1 ') + i[2], callback_data=str(i[0]))])

    # TODO MAKE 2 COLUMNS OUTPUT
    goods.append([InlineKeyboardButton("Добавить позицию", callback_data=str(ADD_NEW_POSITION)+str(KITCHEN)),
                  InlineKeyboardButton("Назад", callback_data=str(END))])

    kb = InlineKeyboardMarkup(goods)

    update.callback_query.answer()
    update.callback_query.edit_message_text("Заказ кухни: \n", reply_markup=kb)


def select_bar(update, context):
    goods = []
    for i in db.get_goods_list(2):
        goods.append([InlineKeyboardButton(i[1] + str(' + 1 ') + i[2], callback_data=str(i[0]))])
    goods.append([InlineKeyboardButton("Добавить позицию", callback_data=str(ADD_NEW_POSITION)+str(BAR)),
                  InlineKeyboardButton("Назад", callback_data=str(END))])
    kb = InlineKeyboardMarkup(goods)

    update.callback_query.answer()
    update.callback_query.edit_message_text("Заказ бар: ", reply_markup=kb)


def select_zeh(update, context):
    goods = []
    for i in db.get_goods_list(3):
        goods.append ([InlineKeyboardButton (i[1] + str (' + 1 ') + i[2], callback_data=str (i[0]))])
    goods.append ([InlineKeyboardButton ("Добавить позицию", callback_data=str (ADD_NEW_POSITION) + str (BAR)),
                   InlineKeyboardButton ("Назад", callback_data=str (END))])
    kb = InlineKeyboardMarkup (goods)

    update.callback_query.answer ( )
    update.callback_query.edit_message_text ("Заказ Цех: ", reply_markup=kb)



def product_handler(update, context):
    db.add_to_order(gid=update.callback_query.data)
    current_product = db.get_goods_by_id(int(update.callback_query.data))
    update.callback_query.answer()
    try:
        update.callback_query.edit_message_text(
            '1 ' + current_product[2] + ' ' + current_product[1] + " добавлен в заказ",
            reply_markup=update.callback_query.message['reply_markup']
        )
    except BadRequest as e:
        print(e)


def add_new_position(update, context):
    text = "Введите название позиции, через запятую введите единицы измерения, затем через запятую введите" \
           " идентификатор(К - кухня, Ц - цех, или Б - бар)\nНапример: Куриное филе, кг., К"

    buttons = [[
        InlineKeyboardButton("Назад",    callback_data=str(END))
    ]]
    kb = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=kb)
    return TYPING


def new_position_handler(update, context):
    data = update.message.text
    if re.match(r'^(\s*\w+\s*)+,(\s*\w+\.*)+,\s*[КЦБкцб]+\s*$', data) is not None:
        name, units, group = data.split(',')
        try:
            db.add_to_goods(name.strip(), units.strip(), group.strip())
            s_mes = context.bot.send_message (update.message.chat_id,
                                              'Позиция "' + name.strip() + '" успешно добавлена')

        except Exception as e:
            if str(e) == 'UNIQUE constraint failed: goods.name':
                text = 'Ошибка.\nДанный товар уже присутствует в таблице'
            else:
                text = 'Произошла ошибка, обратитесь к разработчику'
            print("Oopse, someth wrong \n" + str(e))

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
            START: [CallbackQueryHandler(create_order, pattern='^'+str(CREATING_ORDER)+'$'),
                    CallbackQueryHandler(change_order, pattern='^'+str(CHANGING_ORDER)+'$'),
                    CallbackQueryHandler(delete_order, pattern='^'+str(DELETING_ORDER)+'$'),
                    CallbackQueryHandler(choose_old_order, pattern='^'+str(CHANGING_ORDER)+'\d*$'),
                    CallbackQueryHandler(close_order,  pattern='^'+str(CLOSING_ORDER)+'$'),
                    CallbackQueryHandler(add_to_order, pattern='^'+str(SELECTING_PLACE)+'$'),
                    CallbackQueryHandler(start,        pattern='^'+str(END)+'$')],

            SELECTING_PLACE: [CallbackQueryHandler(select_kitchen, pattern='^'+str(KITCHEN)+'$'),
                              CallbackQueryHandler(select_bar, pattern='^'+str(BAR)+'$'),
                              CallbackQueryHandler(select_zeh, pattern='^'+str(ZEH)+'$'),
                              CallbackQueryHandler(start, pattern='^'+str(END)+'$'),
                              CallbackQueryHandler(product_handler, pattern='^\d*$'),
                              CallbackQueryHandler(
                                  add_new_position, pattern='^'+str(ADD_NEW_POSITION)+str(KITCHEN) +
                                                            '|'+str(ADD_NEW_POSITION)+str(BAR)+'$')
                              ],
            TYPING: [MessageHandler(Filters.text & ~Filters.command, new_position_handler),
                     CallbackQueryHandler(add_to_order, pattern='^'+str(END)+'$')]
        },
        fallbacks=[CommandHandler("stop", stop)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('clear', cleaner))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
