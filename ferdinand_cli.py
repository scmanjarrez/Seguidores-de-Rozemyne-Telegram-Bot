import database as db
import util as ut


HELP = (
    "Esto es lo que puedo hacer por ti:"
    "\n\n"

    "❔ /menu - Interactuar usando una interfaz gráfica. <b>[beta]</b>"
    "\n\n"

    "❔ /semanal - Libros semanales (se actualiza cada martes)."
    "\n"
    "❔ /biblioteca - Lista de libros en la biblioteca."
    "\n"
    "❔ /estanteria <code>parte volúmen</code> - "
    "Lista de libros en la estantería."
    "\n"
    "❔ /ordonnanz - Activa/desactiva la ordonnanz."
    "\n\n"

    "❔ /ayuda - Lista de comandos."
    "\n"
    "❔ /parar - Elimina tu información del bot."
    "\n\n"
)


def _available(state, url):
    if state == 1:
        return f"<a href='{url}'>liberado</a>"
    else:
        return "<code>no liberado</code>"


def _to_volume(volume):
    if volume == '1':
        return 'I'
    if volume == '2':
        return 'II'
    if volume == '3':
        return 'III'
    if volume == '4':
        return 'IV'
    if volume == '5':
        return 'V'
    if volume == '6':
        return 'VI'
    if volume == '7':
        return 'VII'
    if volume == '8':
        return 'VIII'
    if volume == '9':
        return 'IX'


def start(update, context):
    uid = update.effective_message.chat.id
    fname = update.effective_message.chat.first_name
    msg = f"<b>{fname}</b>, ya eres un noble de Ehrenfest."
    if not db.cached(uid):
        db.add_user(uid)
        msg = (f"<b>{fname}</b>, acabas de ser bautizado "
               f"como un noble de Ehrenfest.\n\n{HELP}")
    ut.send(update, msg)


def weekly(update, context):
    uid = update.effective_message.chat.id
    if not db.cached(uid):
        ut.not_started(update)
    else:
        msg = ["Los libros que se imprimirán esta semana son:\n"]
        chapters = db.new_chapters()
        for idx, (part, volume, ch_title, ch_url, ch_available) in enumerate(
                chapters):
            msg.append(
                f"<b>{ch_title}:</b> {_available(ch_available, ch_url)}")
        ut.send(update, "\n".join(msg))


def library(update, context):
    uid = update.effective_message.chat.id
    if not db.cached(uid):
        ut.not_started(update)
    else:
        msg = ["Las estanterías que hay en la biblioteca son:\n"]
        parts = db.parts()
        for part, volume, title, url in parts:
            msg.append(ut.url(f"Parte {part}: {title} {volume}", url))
        ut.send(update, "\n".join(msg))


def bookshelf(update, context):
    uid = update.effective_message.chat.id
    if not db.cached(uid):
        ut.not_started(update)
    else:
        msg = ["Es necesario que me digas "
               "la parte y el volúmen que quieras revisar."]
        if len(context.args) == 2:
            part, volume = context.args
            if (int(part) in range(1, db.n_parts() + 1) and
                int(volume) in range(1, db.n_volumes(part) + 1)):  # noqa
                msg = ["Estos son los libros que me has pedido:\n"]
                chapters = db.chapters(part, _to_volume(volume))
                for ch_title, ch_url in chapters:
                    msg.append(ut.url(ch_title, ch_url))
            else:
                msg = ["La parte o el volúmen "
                       "no se encuentran en la biblioteca."]
        ut.send(update, "\n".join(msg))


def ordonnanz(update, context):
    uid = update.effective_message.chat.id
    if not db.cached(uid):
        ut.not_started(update)
    else:
        db.toggle_notifications(uid)
        if db.notifications(uid) == 1:
            msg = ("Se te enviará una Ordonnanz cada vez "
                   "que se imprima un nuevo libro.")
        else:
            msg = "Ya no se te enviarán más Ordonnanz."
        ut.send(update, msg)


def bot_help(update, context):
    uid = update.effective_message.chat.id
    if not db.cached(uid):
        ut.not_started(update)
    else:
        ut.send(update, HELP)


def stop(update, context):
    uid = update.effective_message.chat.id
    msg = "No eres un noble de Ehrenfest."
    if db.cached(uid):
        ut.blocked(uid)
        msg = "Se te ha eliminado la ciudadanía de Ehrenfest."
    ut.send(update, msg)
