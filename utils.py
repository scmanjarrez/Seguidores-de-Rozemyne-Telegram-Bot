# SPDX-License-Identifier: MIT

# Copyright (c) 2021-2022 scmanjarrez. All rights reserved.
# This work is licensed under the terms of the MIT license.

from telegram.error import Unauthorized, BadRequest
from telegram.utils import helpers
from telegram import ParseMode

import configparser as cfg
import requests as req
import database as db
import traceback
import bs4 as bs
import datetime
import pytz
import re


URL = ('https://legacy.ralevon.com/jnl/'
       'ascendance-of-a-bookworm-%e2%9c%aenovela-ligera%e2%9c%ae-2/')
HEADER = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) '
                   'Gecko/20100101 Firefox/89.0')
}

TITLE = re.compile(r'Parte (\d+) – ([\w\s]+) ([IVX]+)')
USERS_TO_NOTIFY = 20
TIME_BETWEEN_NOTIFY = 2
TIME_CLEAN_MSG = 10 * 60


CONF_FILE = '.config'
_CONFIG = None


def _load_config():
    global _CONFIG
    if _CONFIG is None:
        parser = cfg.ConfigParser()
        parser.read(CONF_FILE)
        _CONFIG = {k: v for section in parser.sections()
                   for k, v in parser[section].items()}


def config(key):
    _load_config()
    return _CONFIG[key]


def blocked(uid):
    db.del_user(uid)


def uid(update):
    return update.effective_message.chat.id


def is_group(uid):
    return uid < 0


def is_admin(update, context, callback=False):
    if not callback:
        gid = update.effective_message.chat.id
        uid = update.effective_message.from_user.id
    else:
        gid = update.effective_message.chat.id
        uid = update.callback_query.from_user.id
    info = context.bot.get_chat_member(gid, uid)
    return info.status != 'member'


def send(update, msg, quote=True, reply_markup=None, disable_preview=True):
    try:
        return update.message.reply_html(
            msg, quote=quote, reply_markup=reply_markup,
            disable_web_page_preview=disable_preview)
    except Unauthorized:
        blocked(update.effective_message.chat.id)


def send_bot(bot, uid, msg, reply_markup=None, disable_preview=True):
    try:
        return bot.send_message(
            uid, msg, ParseMode.HTML, reply_markup=reply_markup,
            disable_web_page_preview=disable_preview)
    except Unauthorized:
        blocked(uid)


def edit(update, msg, reply_markup, disable_preview=True):
    try:
        update.callback_query.edit_message_text(msg, ParseMode.HTML,
                                                reply_markup=reply_markup,
                                                disable_web_page_preview=disable_preview)  # noqa
    except BadRequest as br:
        if not str(br).startswith("Message is not modified:"):
            print(f"***  Exception caught in edit "
                  f"({update.effective_message.chat.id}): ", br)
            traceback.print_stack()


def _msg_start(update):
    uid = update.effective_message.chat.id
    if is_group(uid):
        msg = ("Solicita que se anexe tu provincia a Ehrenfest "
               "con /start antes de continuar.")
    else:
        msg = ("Solicita la ciudadanía de Ehrenfest "
               "con /start antes de continuar.")
    return msg


def not_started(update):
    msg = _msg_start(update)
    send(update, msg)


def not_started_gui(update):
    msg = _msg_start(update)
    edit(update, msg, None)


def delete(bot, cid, mid):
    try:
        bot.delete_message(cid, mid)
    except BadRequest:
        pass
    except Unauthorized:
        blocked(cid)


def clean_old_messages(context):
    cid, mids = context.job.context
    for mid in mids:
        delete(context.bot, cid, mid)


def schedule_delete(queue, cid, mids):
    queue.run_once(
        clean_old_messages, TIME_CLEAN_MSG,
        context=(cid, mids))


def antiflood(update, context, sent):
    schedule_delete(context.job_queue, uid(update),
                    (update.message.message_id, sent.message_id))


def status_update(update, context):
    cid = uid(update)
    mid = update.message.message_id
    for member in update.message.new_chat_members:
        mention = url(member['first_name'], f"tg://user?id={member['id']}")
        msg = (f"Rezamos para que Dregarnuhr, la Diosa del Tiempo, "
               f"teja fuertemente los hilos de nuestro destino, {mention}. ")
        send(update, msg, quote=False)
    delete(context.bot, cid, mid)


def _remove_job(queue, name):
    current_jobs = queue.get_jobs_by_name(name)
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()


def notify_callback(context):
    uid, msg = context.job.context
    send_bot(context.bot, uid, msg)


def notify_publication(queue, msg):
    users = db.all_users_notify()
    cnt = USERS_TO_NOTIFY
    time = 0
    for uid, in users:
        if cnt == 0:
            cnt = USERS_TO_NOTIFY
            time += TIME_BETWEEN_NOTIFY
        queue.run_once(notify_callback, time,
                       context=(uid, msg),
                       name=f"{uid}: {msg[:15]}")
        cnt -= 1


def url(text, url):
    return f"<b><a href='{url}'>{text}</a></b>"


def deeplink(bot, command):
    return helpers.create_deep_linked_url(bot.username, command)


def scrape_chapters(part_volume_url):
    resp = req.get(part_volume_url, headers=HEADER)
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    content = soup.find('div', attrs={'class': 'entry-content'})
    chapters = content.find_all('a', href=True)
    ended = False
    title_url = []
    for ch in chapters:
        title = ch.get_text()
        if title and title.lower() != 'miya kazuki':
            title_url.append((title, ch['href']))
        if title.lower() in ('palabras del autor', 'palabras finales'):
            ended = True
    return (title_url, ended)


def scrape_volumes(empty=False):
    resp = req.get(URL, headers=HEADER)
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    volume_table = soup.find_all('tbody')[1]
    rows = volume_table.find_all('tr')
    for row in rows:
        try:
            url = row.find('a')['href']
        except TypeError:
            break
        else:
            txt = row.get_text().strip().split('\n')[0]
            match = TITLE.match(txt)
            if match is not None:
                part, title, volume = match.groups()
                if not db.part_cached(part, volume):
                    db.add_part(part, volume, title, url)
                    if empty:
                        chapters, ended = scrape_chapters(url)
                        if ended:
                            db.set_finished(part, volume)
                        for ch_title, ch_url in chapters:
                            if not db.chapter_cached(part, volume, ch_title):
                                db.add_chapter(part, volume, ch_title, ch_url)
            else:
                print(f"No match: {txt}")


def check_volumes(queue):
    tmp = db.unfinished_part()
    if tmp is not None:
        part, volume, _, url = tmp
    else:
        scrape_volumes()
        part, volume, _, url = db.unfinished_part()
    cached_n_chap = db.n_chapters(part, volume)
    current_chap = db.new_chapters()
    scraped_chap, ended = scrape_chapters(url)
    if ended:
        db.set_finished(part, volume)
    if cached_n_chap != len(scraped_chap):
        _remove_job(queue, 'check_hourly')
        for cur in current_chap:
            ch_part, ch_volume, ch_title = cur
            db.unset_new(ch_part, ch_volume, ch_title)
        for ch_title, ch_url in scraped_chap:
            if not db.chapter_cached(part, volume, ch_title):
                db.add_chapter(part, volume, ch_title, ch_url)


def volumes_callback(context):
    if db.unfinished_part() is None:
        scrape_volumes()
    else:
        check_volumes(context.job.context)


def check_hourly(context):
    queue = context.job.context
    queue.run_repeating(volumes_callback, 1 * 60 * 60, 1,
                        context=queue, name='check_hourly')


def check_weekly(queue):
    midnight = datetime.time(hour=0, tzinfo=pytz.timezone('Europe/Madrid'))
    queue.run_daily(check_hourly, midnight, days=(1,),
                    context=queue, name='check_weekly')
