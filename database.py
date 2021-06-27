from contextlib import closing
import sqlite3 as sql

DB = 'diptico.db'


def setup_db():
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.executescript(
                """
                CREATE TABLE IF NOT EXISTS parts (
                    part INTEGER,
                    volume INTEGER,
                    title TEXT,
                    url TEXT,
                    finished INTEGER DEFAULT 0,
                    PRIMARY KEY (part, volume)
                );

                CREATE TABLE IF NOT EXISTS chapters (
                    part INTEGER,
                    volume INTEGER,
                    title TEXT,
                    url TEXT,
                    new INTEGER DEFAULT 1,
                    available INTEGER DEFAULT 0,
                    FOREIGN KEY (part) REFERENCES parts(part),
                    FOREIGN KEY (volume) REFERENCES parts(volume),
                    PRIMARY KEY (part, volume, title)
                );

                CREATE TABLE IF NOT EXISTS users (
                    uid INTEGER,
                    notifications INTEGER DEFAULT 1
                );
                """
            )


def parts():
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('SELECT part, volume, title, url FROM parts')
            return cur.fetchall()


def total_parts():
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('SELECT part, title '
                        'FROM parts '
                        'ORDER BY rowid')
            ret = cur.fetchall()
            group = [[(p, t) for p, t in ret if p == r]
                     for r in range(1, ret[-1][0] + 1)]
            return [max(set(g), key=g.count) for g in group]


def n_parts():
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('SELECT count(DISTINCT part) '
                        'FROM parts')
            return cur.fetchone()[0]


def n_volumes(part):
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('SELECT count(volume) '
                        'FROM parts '
                        'WHERE part = ?',
                        [part])
            return cur.fetchone()[0]


def total_volumes(part):
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('SELECT volume '
                        'FROM parts '
                        'WHERE part = ? '
                        'ORDER BY rowid',
                        [part])
            return cur.fetchall()


def unfinished_part():
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('SELECT part, volume, title, url '
                        'FROM parts '
                        'WHERE finished = 0')
            ret = cur.fetchone()
            if ret is not None:
                ret = ret[0]
            return ret


def add_part(part, volume, title, url):
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('INSERT INTO parts '
                        '(part, volume, title, url) '
                        'VALUES (?, ?, ?, ?)',
                        [part, volume, title, url])
            db.commit()


def part_cached(part, volume):
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute(
                'SELECT EXISTS ('
                'SELECT 1 FROM parts '
                'WHERE part = ? AND volume = ?'
                ')',
                [part, volume])
            return cur.fetchone()[0]


def set_finished(part, volume):
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('UPDATE parts '
                        'SET finished = 1 '
                        'WHERE part = ? AND volume = ?',
                        [part, volume])
            db.commit()


def chapters(part, volume):
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('SELECT title, url '
                        'FROM chapters '
                        'WHERE part = ? AND volume = ? '
                        'ORDER BY rowid',
                        [part, volume])
            return cur.fetchall()


def n_chapters(part, volume):
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('SELECT count(title) '
                        'FROM chapters '
                        'WHERE part = ? AND volume = ?',
                        [part, volume])
            return cur.fetchall()


def unavailable_chapters():
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('SELECT part, volume, title, url '
                        'FROM chapters '
                        'WHERE available = 0')
            return cur.fetchall()


def new_chapters():
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('SELECT part, volume, title, url, available '
                        'FROM chapters '
                        'WHERE new = 1')
            return cur.fetchall()


def add_chapter(part, volume, title, url):
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('INSERT INTO chapters '
                        '(part, volume, title, url) '
                        'VALUES (?, ?, ?, ?)',
                        [part, volume, title, url])
            db.commit()


def chapter_cached(part, volume, title):
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute(
                'SELECT EXISTS ('
                'SELECT 1 FROM chapters '
                'WHERE part = ? AND volume = ? AND title = ?)',
                [part, volume, title])
            return cur.fetchone()[0]


def set_available(part, volume, title):
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('UPDATE chapters '
                        'SET available = 1 '
                        'WHERE part = ? AND volume = ? '
                        'AND title = ?',
                        [part, volume, title])
            db.commit()


def unset_new(part, volume, title):
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('UPDATE chapters '
                        'SET new = 0 '
                        'WHERE part = ? AND volume = ? '
                        'AND title = ?',
                        [part, volume, title])
            db.commit()


def users():
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('SELECT uid FROM users')
            return cur.fetchall()


def cached(uid):
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute(
                'SELECT EXISTS ('
                'SELECT 1 FROM users WHERE uid = ?'
                ')',
                [uid])
            return cur.fetchone()[0]


def add_user(uid):
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('INSERT INTO users (uid) VALUES (?)',
                        [uid])
            db.commit()


def del_user(uid):
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('DELETE FROM users '
                        'WHERE uid = ?',
                        [uid])
            db.commit()


def notifications(uid):
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('SELECT notifications FROM users '
                        'WHERE uid = ?',
                        [uid])
            return cur.fetchone()[0]  # (x,)


def toggle_notifications(uid):
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('UPDATE users SET notifications = -notifications '
                        'WHERE uid = ?',
                        [uid])
            db.commit()


def all_users_notify():
    with closing(sql.connect(DB)) as db:
        with closing(db.cursor()) as cur:
            cur.execute('SELECT uid FROM users '
                        'WHERE notifications = 1')
            return cur.fetchall()
