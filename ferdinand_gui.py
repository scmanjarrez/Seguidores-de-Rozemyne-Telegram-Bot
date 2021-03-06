# SPDX-License-Identifier: MIT

# Copyright (c) 2021-2022 scmanjarrez. All rights reserved.
# This work is licensed under the terms of the MIT license.

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import database as db
import utils as ut


def button(buttons):
    return [InlineKeyboardButton(bt[0], callback_data=bt[1]) for bt in buttons]


def button_url(buttons):
    return [InlineKeyboardButton(bt[0], bt[1]) for bt in buttons]


def button_redirect(bot, command):
    return InlineKeyboardMarkup(
        [button_url([("β‘ Pulsa para usar herramienta inhibidora de sonido β¬",
                      ut.deeplink(bot, command))])])


def menu(update, context):
    uid = ut.uid(update)
    if not db.cached(uid):
        ut.not_started(update)
    else:
        main_menu(update)


def main_menu(update):
    kb = [button([("π Biblioteca π", 'library_menu')]),
          button_url([("π Anuarios π",
                       ut.config('pdfs'))]),
          button_url([("π Archivos del sΓ³tano π",
                       ut.config('webnovel'))]),
          button([("π Altares a los Dioses π", 'shrines_menu')]),
          button([("π Libros Semanales π", 'weekly_menu')]),
          button([("π Ordonnanz π", 'notifications_menu')])]
    resp = ut.send
    if update.callback_query is not None:
        resp = ut.edit
    resp(update, "Templo", reply_markup=InlineKeyboardMarkup(kb))


def library_menu(update):
    kb = [button([("Β« Volver al Templo", 'main_menu')])]
    parts = db.total_parts()
    for idx, (part, title) in enumerate(parts):
        kb.insert(idx, button([(f"Parte {part}: {title}", f'part_{part}')]))
    ut.edit(update, "Biblioteca", InlineKeyboardMarkup(kb))


def part_menu(update, part):
    kb = [button([("Β« Volver a la Biblioteca", 'library_menu'),
                  ("Β« Volver al Templo", 'main_menu')])]
    volumes = db.total_volumes(part)
    for idx, (volume,) in enumerate(volumes):
        kb.insert(idx,
                  button([(f"VolΓΊmen {volume}", f'volume_{part}_{volume}')]))
    ut.edit(update, f"Parte {part}: {db.name_part(part)}",
            InlineKeyboardMarkup(kb))


def volume_menu(update, part, volume):
    kb = [button([(f"Β« Volver a la Parte {part}", f'part_{part}'),
                  ("Β« Volver al Templo", 'main_menu')])]
    chapters = db.chapters(part, volume)
    for idx, (ch_title, ch_url) in enumerate(chapters):
        kb.insert(idx, button_url([(f"{ch_title}", ch_url)]))
    ut.edit(update, f"Parte {part}: {db.name_part(part)}, volΓΊmen {volume}",
            InlineKeyboardMarkup(kb))


def shrines_menu(update):
    kb = [button_url([("π₯ Seguidores de Rozemyne π₯",
                       ut.config('group'))]),
          button_url([("π₯ SalΓ³n de Eruditos (Spoilers) π₯",
                       ut.config('spoilers'))]),
          button_url([("π’ Biblioteca de Mestionora π’",
                       ut.config('channel'))]),
          button_url([("π§ Los Gutenbergs de Rozemyne (Youtube) π§",
                       ut.config('youtube'))]),
          button_url([("π£ Fans de Ascendance of a Bookworm (Discord) π£",
                       ut.config('discord'))]),
          button_url([("π₯ Honzuki no Gekokujou (Facebook) π₯",
                       ut.config('facebook'))]),
          button([("Β« Volver al Templo", 'main_menu')])]
    ut.edit(update, "Altares de los Dioses", InlineKeyboardMarkup(kb))


def weekly_menu(update):
    kb = [button([("Β« Volver al Templo", 'main_menu')])]
    chapters = db.mestionora_chapters()
    for idx, ch_title in enumerate(chapters):
        if not ch_title.startswith('+'):
            kb.insert(idx,
                      button_url([(f"{ch_title}",
                                   ut.config('channel'))]))
        else:
            kb.insert(idx,
                      button([(f"π {ch_title[1:]} π", 'nop')]))
    ut.edit(update, "Libros Semanales", InlineKeyboardMarkup(kb))


def notifications_menu(update, context):
    uid = ut.uid(update)
    kb = [button([("Β« Volver al Templo", 'main_menu')])]
    tit = "Ordonnanz"
    if not ut.is_group(uid) or (ut.is_group(uid) and
                                ut.is_admin(update, context,
                                            callback=True)):
        notification_icon = 'π' if db.notifications(uid) == 1 else 'π'
        kb.insert(0,
                  button([(f"Recibir Ordonnanz: {notification_icon}",
                           'notification_toggle')]))
    else:
        tit = "SΓ³lo disponible para la facciΓ³n del Aub."
    ut.edit(update, tit, InlineKeyboardMarkup(kb))


def notification_toggle(update, context):
    uid = ut.uid(update)
    db.toggle_notifications(uid)
    notifications_menu(update, context)
