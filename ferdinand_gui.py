from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import database as db
import util as ut


def _floor_name(part):
    name = "Sótano"
    if part == '1':
        name = "Primer Piso"
    elif part == '2':
        name = "Segundo Piso"
    elif part == '3':
        name = "Tercer Piso"
    elif part == '4':
        name = "Cuarto Piso"
    elif part == '5':
        name = "Quinto Piso"
    return name


def _available(status):
    if status == 1:
        return '🟢'
    else:
        return '🔴'


def button(buttons):
    return [InlineKeyboardButton(bt[0], callback_data=bt[1]) for bt in buttons]


def button_url(buttons):
    return [InlineKeyboardButton(bt[0], bt[1]) for bt in buttons]


def menu(update, context):
    uid = update.effective_message.chat.id
    if not db.cached(uid):
        ut.not_started(update)
    else:
        main_menu(update)


def main_menu(update):
    kb = [button([("📚 La Biblioteca 📚", 'library_menu')]),
          button([("📆 Libros Semanales 📆", 'weekly_menu')]),
          button([("🕊 Ordonnanz 🕊", 'notifications_menu')])]
    resp = ut.send
    if update.callback_query is not None:
        resp = ut.edit
    resp(update, "El Templo", reply_markup=InlineKeyboardMarkup(kb))


def library_menu(update):
    kb = [button([("« Volver al Templo", 'main_menu')])]
    parts = db.total_parts()
    print(parts)
    for idx, (part, title) in enumerate(parts):
        kb.insert(idx, button([(f"Parte {part}: {title}", f'part_{part}')]))
    ut.edit(update, "La Biblioteca", InlineKeyboardMarkup(kb))


def part_menu(update, part):
    kb = [button([("« Volver a La Biblioteca", 'library_menu'),
                  ("« Volver al Templo", 'main_menu')])]
    volumes = db.total_volumes(part)
    for idx, (volume,) in enumerate(volumes):
        kb.insert(idx,
                  button([(f"Volúmen {volume}", f'volume_{part}_{volume}')]))
    ut.edit(update, _floor_name(part), InlineKeyboardMarkup(kb))


def volume_menu(update, part, volume):
    kb = [button([(f"« Volver al {_floor_name(part)}", f'part_{part}'),
                  ("« Volver al Templo", 'main_menu')])]
    chapters = db.chapters(part, volume)
    for idx, (ch_title, ch_url) in enumerate(chapters):
        kb.insert(idx, button_url([(f"{ch_title}", ch_url)]))
    ut.edit(update, f"Parte {part}: Volúmen {volume}",
            InlineKeyboardMarkup(kb))


def weekly_menu(update):
    kb = [button([("« Volver al Templo", 'main_menu')])]
    chapters = db.new_chapters()
    for idx, (ch_title, ch_url, ch_available) in enumerate(chapters):
        kb.insert(idx,
                  button_url([(f"{ch_title}: {_available(ch_available)}",
                               ch_url)]))
    ut.edit(update, "Libros Semanales", InlineKeyboardMarkup(kb))


def notifications_menu(update):
    uid = update.effective_message.chat.id
    notification_icon = '🔔' if db.notifications(uid) == 1 else '🔕'
    kb = [button([(f"Recibir Ordonnanz: {notification_icon}",
                   'notification_toggle')]),
          button([("« Volver al Templo", 'main_menu')])]
    ut.edit(update, "Ordonnanz", InlineKeyboardMarkup(kb))


def notification_toggle(update):
    uid = update.effective_message.chat.id
    db.toggle_notifications(uid)
    notifications_menu(update)
