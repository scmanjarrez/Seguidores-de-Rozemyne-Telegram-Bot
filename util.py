# SPDX-License-Identifier: MIT

# Copyright (c) 2021 scmanjarrez. All rights reserved.
# This work is licensed under the terms of the MIT license.

from telegram.error import Unauthorized, BadRequest
from telegram.utils import helpers
from telegram import ParseMode
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


CONFIG_FILE = '.config'
CONFIG = None


def load_config():
    global CONFIG
    if CONFIG is None:
        with open(CONFIG_FILE, 'r') as f:
            CONFIG = {k: v for k, v in
                      [line.split('=') for line in f.read().splitlines()]}
    return CONFIG


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
        update.message.reply_html(msg, quote=quote, reply_markup=reply_markup,
                                  disable_web_page_preview=disable_preview)
    except Unauthorized:
        blocked(update.effective_message.chat.id)


def send_bot(bot, uid, msg, reply_markup=None, disable_preview=True):
    try:
        bot.send_message(uid, msg, ParseMode.HTML, reply_markup=reply_markup,
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
    if uid < 0:
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


def new_member(update, context):
    new = []
    for member in update.message.new_chat_members:  # will I get more than one?
        new.append(url(member['first_name'], f"tg://user?id={member['id']}"))
    if len(new) == 1:
        msg = (f"Bienvenido al templo {', '.join(new)}. "
               f"A partir de este momento, "
               f"eres reconocido como un noble de Ehrenfest.")
    else:
        msg = (f"Bienvenidos al templo {', '.join(new)}. "
               f"A partir de este momento, "
               f"sois reconocidos como nobles de Ehrenfest.")
    send(update, msg)


def _remove_job(queue, name):
    current_jobs = queue.get_jobs_by_name(name)
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()
    else:
        print(f"No job named {name}")


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


def scrape_index(empty=False):
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


def check_index(queue):
    tmp = db.unfinished_part()
    if tmp is not None:
        part, volume, _, url = tmp
    else:
        scrape_index()
        part, volume, _, url = db.unfinished_part()
    cached_n_chap = db.n_chapters(part, volume)
    current_chap = db.new_chapters()
    scraped_chap, ended = scrape_chapters(url)
    if ended:
        db.set_finished(part, volume)
    if cached_n_chap != len(scraped_chap):
        _remove_job(queue, 'tuesday_hourly')
        for cur in current_chap:
            ch_part, ch_volume, ch_title = cur
            db.unset_new(ch_part, ch_volume, ch_title)
        for ch_title, ch_url in scraped_chap:
            if not db.chapter_cached(part, volume, ch_title):
                db.add_chapter(part, volume, ch_title, ch_url)


def titles_callback(context):
    queue = context.job.context
    if db.unfinished_part() is None:
        scrape_index()
    else:
        check_index(queue)


def tuesday_callback(context):
    queue = context.job.context
    queue.run_repeating(titles_callback, 1 * 60 * 60, 1,
                        context=queue, name='tuesday_hourly')


def check_weekly(queue):
    midnight = datetime.time(hour=0, tzinfo=pytz.timezone('Europe/Madrid'))
    queue.run_daily(tuesday_callback, midnight, days=(1,),
                    context=queue, name='tuesday_weekly')
