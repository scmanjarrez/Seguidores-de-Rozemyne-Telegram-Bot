# SPDX-License-Identifier: MIT

# Copyright (c) 2021-2022 scmanjarrez. All rights reserved.
# This work is licensed under the terms of the MIT license.

import ferdinand_gui as gui
import database as db
import utils as ut


HELP = (
    "Esto es lo que puedo hacer por ti:"
    "\n\n"

    "❔ /menu - Interactúa con el bot mediante botones."
    "\n\n"

    "❔ /biblioteca - Lista de libros en la biblioteca."
    "\n"
    "❔ /estanteria <code>&lt;parte&gt; &lt;volúmen&gt;</code> - "
    "Lista de libros en la estantería."
    "\n"
    "❔ /anuarios - Lista de libros en la biblioteca (PDF)."
    "\n"
    "❔ /archivos - Archivos del sótano (WebNovel)."
    "\n"
    "❔ /altares - Lista de altares a los dioses."
    "\n"
    "❔ /semanal - Libros que se imprimen cada semana."
    "\n"
    "❔ /ordonnanz - Permite/prohíbe el envío de ordonnanz."
    "\n\n"

    "❔ /ayuda - Pide consejos a Ferdinand."
    "\n"
    "❔ /parar - Renuncia a la ciudadanía de Ehrenfest."
    "\n\n"
)

GROUP = ("Es posible que hayan espías de Ahrensbach escuchando, usemos "
         "un método seguro.")


VOLUME = {
    '1': 'I',
    '2': 'II',
    '3': 'III',
    '4': 'IV',
    '5': 'V',
    '6': 'VI',
    '7': 'VII',
    '8': 'VIII',
    '9': 'IX'
}


def _redirect(update, context, command):
    sent = ut.send_bot(context.bot, ut.uid(update), GROUP,
                       reply_markup=gui.button_redirect(context.bot, command))
    ut.antiflood(update, context, sent)


def start(update, context):
    uid = ut.uid(update)
    if not context.args:
        if not ut.is_group(uid):
            fname = update.effective_message.chat.first_name
            msg = f"<b>{fname}</b>, ya eres un noble de Ehrenfest."
        elif ut.is_group(uid) and ut.is_admin(update, context):
            msg = "Esta provincia ya pertenece a Ehrenfest."
        else:
            msg = "Sólo la facción del Aub puede controlar las fronteras."

        if not db.cached(uid) and not ut.is_group(uid):
            db.add_user(uid)
            msg = (f"<b>{fname}</b>, acabas de ser bautizado "
                   f"como un noble de Ehrenfest.\n\n{HELP}")
        elif (not db.cached(uid) and ut.is_group(uid)
              and ut.is_admin(update, context)):
            db.add_user(uid)
            fname = update.effective_message.chat.title
            msg = (f"La provincia <b><i>{fname}</i></b> "
                   f"se ha incorporado a Ehrenfest.\n\n{HELP}")
        sent = ut.send(update, msg)
        if ut.is_group(uid):
            ut.antiflood(update, context, sent)
    else:
        if not db.cached(uid):
            db.add_user(uid)
        if context.args[0] == 'deep_week':
            weekly(update, context)
        elif context.args[0] == 'deep_lib':
            library(update, context)
        elif context.args[0] == 'deep_ybook':
            yearbook(update, context)
        elif context.args[0].startswith('deep_book'):
            context.args = context.args[0].split('-')[1:]
            bookshelf(update, context)
        elif context.args[0] == 'deep_sh':
            shrines(update, context)


def weekly(update, context):
    uid = ut.uid(update)
    if not db.cached(uid):
        ut.not_started(update)
    else:
        if ut.is_group(uid):
            _redirect(update, context, "deep_week")
        else:
            msg = ["Los libros que se imprimirán esta semana son:\n\n"]
            chapters = db.mestionora_chapters()
            for ch_title in chapters:
                msg.append(f"<b>{ch_title}\n</b>")
            url_msg = ut.url('Biblioteca de Mestionora',
                             ut.config('channel'))
            msg.append(f"\nPuedes leerlos en la {url_msg}")
            ut.send(update, "".join(msg))


def library(update, context):
    uid = ut.uid(update)
    if not db.cached(uid):
        ut.not_started(update)
    else:
        if ut.is_group(uid):
            _redirect(update, context, "deep_lib")
        else:
            msg = ["Las estanterías que hay en la biblioteca son:\n"]
            parts = db.parts()
            for part, volume, title, url in parts:
                msg.append(ut.url(f"Parte {part}: {title} {volume}", url))
            ut.send(update, "\n".join(msg))


def yearbook(update, context):
    uid = ut.uid(update)
    if not db.cached(uid):
        ut.not_started(update)
    else:
        yearbooks = ut.url('anuarios', ut.config('pdfs'))
        ut.send(update,
                f"Aquí puedes encontrar los {yearbooks} (PDFs).")


def archive(update, context):
    uid = ut.uid(update)
    if not db.cached(uid):
        ut.not_started(update)
    else:
        archive = ut.url('archivos', ut.config('webnovel'))
        ut.send(update,
                f"Aquí puedes encontrar los {archive} "
                f"del sótano (WebNovel).")


def bookshelf(update, context):
    uid = ut.uid(update)
    if not db.cached(uid):
        ut.not_started(update)
    else:
        if ut.is_group(uid):
            _redirect(update, context, f"deep_book-{'-'.join(context.args)}")
        else:
            msg = ["Es necesario que me digas "
                   "la parte y el volúmen que quieras revisar. "
                   "Ej: /estanteria 4 1"]
            if len(context.args) == 2:
                part, volume = context.args
                if (int(part) in range(1, db.n_parts() + 1) and
                    int(volume) in range(1, db.n_volumes(part) + 1)):  # noqa
                    msg = ["Estos son los libros que me has pedido:\n"]
                    chapters = db.chapters(part, VOLUME[volume])
                    for ch_title, ch_url in chapters:
                        msg.append(ut.url(ch_title, ch_url))
                else:
                    msg = ["Esa parte y/o volúmen "
                           "no se encuentran en la biblioteca."]
            ut.send(update, "\n".join(msg))


def shrines(update, context):
    uid = ut.uid(update)
    if not db.cached(uid):
        ut.not_started(update)
    else:
        if ut.is_group(uid):
            _redirect(update, context, "deep_sh")
        else:
            msg = ["Puedes rezar a los dioses en los siguientes altares:\n\n",
                   ut.url("- Seguidores de Rozemyne [grupo]\n",
                          ut.config('group')),
                   ut.url("- Seguidores de Rozemyne (Spoilers) [grupo]\n",
                          ut.config('spoilers')),
                   ut.url("- Biblioteca de Mestionora [canal]\n",
                          ut.config('channel')),
                   ut.url("- Los Gutenbergs [youtube]\n",
                          ut.config('youtube')),
                   ut.url("- Fans de Ascendance of a Bookworm [discord]\n",
                          ut.config('discord')),
                   ut.url("- Honzuki no Gekokujou (Myne y sus Bookworms) "
                          "LatinoFans Y más! [facebook]\n",
                          ut.config('facebook'))
                   ]
            ut.send(update, "".join(msg))


def ordonnanz(update, context):
    uid = ut.uid(update)
    if not db.cached(uid):
        ut.not_started(update)
    else:
        if ut.is_group(uid) and not ut.is_admin(update, context):
            msg = ("Sólo la facción del Aub puede controlar la Ordonnanz.")
        else:
            db.toggle_notifications(uid)
            if db.notifications(uid) == 1:
                msg = (f"Se {'' if ut.is_group(uid) else 'te '}"
                       f"enviará una ordonnanz cada vez "
                       f"que se imprima un nuevo libro.")

            else:
                msg = (f"Ya no se {'' if ut.is_group(uid) else 'te '}"
                       f"enviarán más ordonnanz.")
        sent = ut.send(update, msg)
        if ut.is_group(uid):
            ut.antiflood(update, context, sent)


def bot_help(update, context):
    uid = ut.uid(update)
    if not db.cached(uid):
        ut.not_started(update)
    else:
        sent = ut.send(update, HELP)
        if ut.is_group(uid):
            ut.antiflood(update, context, sent)


def stop(update, context):
    uid = ut.uid(update)
    msg = "No eres un noble de Ehrenfest."
    if ut.is_group(uid):
        msg = "Esta provincia no pertenece a Ehrenfest."
    if db.cached(uid):
        if ut.is_group(uid) and not ut.is_admin(update, context):
            msg = "Sólo la facción del Aub puede controlar las fronteras."
        else:
            ut.blocked(uid)
            msg = "Ya no eres un noble de Ehrenfest."
            if ut.is_group(uid):
                msg = "Esta provincia ha dejado de pertenecer a Ehrenfest."
    ut.send(update, msg)


def update_db(update, context):
    uid = ut.uid(update)
    admin = int(ut.config('admin'))
    if uid == admin:
        ut.check_volumes(context.job_queue)


def publish(update, context):
    uid = ut.uid(update)
    publisher = int(ut.config('publisher'))
    admin = int(ut.config('admin'))
    if uid in (admin, publisher):
        titles = [line.strip() for line in " ".join(context.args).split('_')]
        multi = any(el.startswith('+') for el in titles)
        sep = "\n" if multi else "\n\n"
        st = "" if multi else "<b>"
        en = "" if multi else "</b>"
        channel = ut.url('Biblioteca de Mestionora',
                         ut.config('channel'))
        db.add_mestionora(titles)
        b_titles = [f"- {st}<i>{tit}</i>{en}\n" if not tit.startswith('+')
                    else f"\n<b>{tit[1:]}:</b>\n"
                    for tit in titles]
        msg = (f"✨ Has recibido la bendición semanal de Mestionora ✨\n\n"
               f"Los libros que se imprimirán esta semana son:{sep}"
               f"{''.join(b_titles)}\n"
               f"Puedes leerlos en la {channel}")
        ut.notify_publication(context.job_queue, msg)


def notify(update, context):
    uid = ut.uid(update)
    admin = int(ut.config('admin'))
    if uid == admin:
        ut.notify_publication(context.job_queue, " ".join(context.args))
