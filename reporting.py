from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from config import *
import logging
from DbHandler import DBHandler
import re


def reporting(update, context):
    text = 'Отчетность'
    buttons = [[InlineKeyboardButton("Кухня", callback_data=str(KITCHEN_REPORT)),
                InlineKeyboardButton("Бар", callback_data=str(BAR_REPORT)),
                InlineKeyboardButton("Цех", callback_data=str(ZEH_REPORT))],
               [InlineKeyboardButton ("Получить отчет в .xlsx", callback_data=str (GET_REPORT_XLSX))],
               [InlineKeyboardButton("Назад", callback_data=str(START))]]
    kb = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text, reply_markup=kb)

    return REPORTING


def get_report(update, context):
    text = 'Ваша отчетность'
    buttons = [[InlineKeyboardButton('Back', callback_data=str(REPORTING))]]
    kb = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text, reply_markup=kb)


def get_report_xlsx(update, context):
    # print(dir(update.callback_query.message.chat_id))
    doc = context.bot.send_document(update.callback_query.message.chat_id, document=open('test.xlsx', 'rb'))

    def message_deleter(cont) :
        cont.bot.delete_message (update.callback_query.message.chat_id, doc['message_id'])

    context.job_queue.run_once(message_deleter, DELETE_MESSAGE_PAUSE)

    update.callback_query.answer()
    # return reporting(update, context)


def deep_report(update, context):
    data = update.callback_query.data
    targets = {KITCHEN_REPORT: 'kitchen',
               BAR_REPORT: 'bar',
               ZEH_REPORT: 'zeh'}
    target = targets[data]
    doc = context.bot.send_document (update.callback_query.message.chat_id, document=open (target + '.xlsx', 'rb'))

    def message_deleter(cont) :
        cont.bot.delete_message (update.callback_query.message.chat_id, doc['message_id'])

    context.job_queue.run_once (message_deleter, DELETE_MESSAGE_PAUSE)

    update.callback_query.answer()


