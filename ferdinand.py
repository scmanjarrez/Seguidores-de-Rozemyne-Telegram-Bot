#!/usr/bin/env python3
from telegram.ext import (CallbackQueryHandler, CommandHandler, MessageHandler,
                          Filters, Updater)
from telegram.error import BadRequest
import ferdinand_cli as cli
import ferdinand_gui as gui
import database as db
import logging as log
import util as ut
import os


def button_handler(update, context):
    uid = update.effective_message.chat.id
    query = update.callback_query
    try:
        query.answer()
    except BadRequest:
        pass

    if not db.cached(uid):
        ut.not_started_gui(update)
    else:
        if query.data == 'main_menu':
            gui.main_menu(update)
        elif query.data == 'library_menu':
            gui.library_menu(update)
        elif query.data.startswith('part_'):
            args = query.data.split('_')
            gui.part_menu(update, args[1])
        elif query.data.startswith('volume_'):
            args = query.data.split('_')
            gui.volume_menu(update, args[1], args[2])
        elif query.data == 'shrine_menu':
            gui.shrine_menu(update)
        elif query.data == 'weekly_menu':
            gui.weekly_menu(update)
        elif query.data == 'notifications_menu':
            gui.notifications_menu(update)
        elif query.data == 'notification_toggle':
            gui.notification_toggle(update)


def setup_handlers(dispatch, job_queue):
    start_handler = CommandHandler('start', cli.start,
                                   filters=~Filters.update.edited_message)
    dispatch.add_handler(start_handler)

    new_member_handler = MessageHandler(Filters.status_update.new_chat_members,
                                        ut.new_member)
    dispatch.add_handler(new_member_handler)

    stop_handler = CommandHandler('parar', cli.stop,
                                  filters=~Filters.update.edited_message)
    dispatch.add_handler(stop_handler)

    help_handler = CommandHandler('ayuda', cli.bot_help,
                                  filters=~Filters.update.edited_message)
    dispatch.add_handler(help_handler)

    menu_handler = CommandHandler('menu', gui.menu,
                                  filters=~Filters.update.edited_message)
    dispatch.add_handler(menu_handler)

    library_handler = CommandHandler('biblioteca', cli.library,
                                     filters=~Filters.update.edited_message)
    dispatch.add_handler(library_handler)

    bookshelf_handler = CommandHandler('estanteria', cli.bookshelf,
                                       filters=~Filters.update.edited_message)
    dispatch.add_handler(bookshelf_handler)

    shrine_handler = CommandHandler('altar', cli.shrine,
                                    filters=~Filters.update.edited_message)
    dispatch.add_handler(shrine_handler)

    weekly_handler = CommandHandler('semanal', cli.weekly,
                                    filters=~Filters.update.edited_message)
    dispatch.add_handler(weekly_handler)

    ordonnanz_handler = CommandHandler('ordonnanz', cli.ordonnanz,
                                       filters=~Filters.update.edited_message)
    dispatch.add_handler(ordonnanz_handler)

    scrape_handler = CommandHandler('forcescrape', cli.force_scrape,
                                    filters=~Filters.update.edited_message)
    dispatch.add_handler(scrape_handler)

    update_handler = CommandHandler('forceupdate', cli.force_check,
                                    filters=~Filters.update.edited_message)
    dispatch.add_handler(update_handler)

    publish_handler = CommandHandler('publicar', cli.publish_translation,
                                     filters=~Filters.update.edited_message)
    dispatch.add_handler(publish_handler)

    dispatch.add_handler(CallbackQueryHandler(button_handler))


if __name__ == '__main__':
    log.basicConfig(format=('%(asctime)s - %(name)s - '
                            '%(levelname)s - %(message)s'),
                    level=log.INFO)

    with open(".apikey", 'r') as f:
        API_KEY = f.read().strip()

    db.setup_db()
    if not os.path.exists(db.DB):
        ut.scrape_index(empty=True)

    updater = Updater(token=API_KEY, use_context=True)
    dispatcher = updater.dispatcher

    ut.check_weekly(updater.job_queue)
    setup_handlers(dispatcher, updater.job_queue)

    updater.start_polling()
    updater.idle()
