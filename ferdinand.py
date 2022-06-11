#!/usr/bin/env python3

# SPDX-License-Identifier: MIT

# Copyright (c) 2021-2022 scmanjarrez. All rights reserved.
# This work is licensed under the terms of the MIT license.

from telegram.ext import (CallbackQueryHandler, CommandHandler, MessageHandler,
                          Filters, Updater)
from telegram.error import BadRequest

import ferdinand_cli as cli
import ferdinand_gui as gui
import database as db
import logging as log
import utils as ut
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
        elif query.data == 'yearbook_menu':
            gui.yearbook_menu(update)
        elif query.data.startswith('ybook_'):
            args = query.data.split('_')
            gui.ybook_menu(update, args[1])
        elif query.data == 'shrines_menu':
            gui.shrines_menu(update)
        elif query.data == 'weekly_menu':
            gui.weekly_menu(update)
        elif query.data == 'notifications_menu':
            gui.notifications_menu(update, context)
        elif query.data == 'notification_toggle':
            gui.notification_toggle(update, context)


def setup_handlers(dispatch, job_queue):
    status_update_handler = MessageHandler(Filters.status_update,
                                           ut.status_update)
    dispatch.add_handler(status_update_handler)

    dispatch.add_handler(CallbackQueryHandler(button_handler))

    scrape_handler = CommandHandler('actualizar', cli.update_db,
                                    filters=~Filters.update.edited_message)
    dispatch.add_handler(scrape_handler)

    publish_handler = CommandHandler('publicar', cli.publish,
                                     filters=~Filters.update.edited_message)
    dispatch.add_handler(publish_handler)

    notify_handler = CommandHandler('notificar', cli.notify,
                                    filters=~Filters.update.edited_message)
    dispatch.add_handler(notify_handler)

    start_handler = CommandHandler('start', cli.start,
                                   filters=~Filters.update.edited_message)
    dispatch.add_handler(start_handler)

    menu_handler = CommandHandler('menu', gui.menu,
                                  filters=~Filters.update.edited_message)
    dispatch.add_handler(menu_handler)

    weekly_handler = CommandHandler('semanal', cli.weekly,
                                    filters=~Filters.update.edited_message)
    dispatch.add_handler(weekly_handler)

    library_handler = CommandHandler('biblioteca', cli.library,
                                     filters=~Filters.update.edited_message)
    dispatch.add_handler(library_handler)

    yearbook_handler = CommandHandler('anuarios', cli.yearbook,
                                      filters=~Filters.update.edited_message)
    dispatch.add_handler(yearbook_handler)

    bookshelf_handler = CommandHandler('estanteria', cli.bookshelf,
                                       filters=~Filters.update.edited_message)
    dispatch.add_handler(bookshelf_handler)

    shrine_handler = CommandHandler('altares', cli.shrines,
                                    filters=~Filters.update.edited_message)
    dispatch.add_handler(shrine_handler)

    ordonnanz_handler = CommandHandler('ordonnanz', cli.ordonnanz,
                                       filters=~Filters.update.edited_message)
    dispatch.add_handler(ordonnanz_handler)

    help_handler = CommandHandler('ayuda', cli.bot_help,
                                  filters=~Filters.update.edited_message)
    dispatch.add_handler(help_handler)

    stop_handler = CommandHandler('parar', cli.stop,
                                  filters=~Filters.update.edited_message)
    dispatch.add_handler(stop_handler)


if __name__ == '__main__':
    log.basicConfig(format=('%(asctime)s - %(name)s - '
                            '%(levelname)s - %(message)s'),
                    level=log.INFO)
    if os.path.isfile(ut.CONF_FILE):
        db.setup_db()
        if not len(db.parts()):
            ut.scrape_volumes(empty=True)

        updater = Updater(token=ut.config('bot'), use_context=True)
        dispatcher = updater.dispatcher

        ut.check_weekly(updater.job_queue)
        setup_handlers(dispatcher, updater.job_queue)

        updater.start_webhook(listen=ut.config('listen'),
                              port=ut.config('port'),
                              url_path=ut.config('bot'),
                              cert=ut.config('cert'),
                              webhook_url=(f"https://"
                                           f"{ut.config('ip')}/"
                                           f"{ut.config('bot')}")
                              )
        updater.idle()
    else:
        print(f"File {ut.CONF_FILE} not found.")
