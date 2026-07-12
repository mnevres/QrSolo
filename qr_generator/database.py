import sqlite3

class Database:
    def __init__(self, db_name="qr_code_archive.db"):
        self.db_name = db_name
        self.create_tables()

    def create_tables(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS url_archive
                                 (id INTEGER PRIMARY KEY, url TEXT UNIQUE)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS vcard_archive
                                 (id INTEGER PRIMARY KEY, name TEXT, fn TEXT, ln TEXT, org TEXT, title TEXT, email TEXT, phone TEXT, mobile TEXT, url TEXT, vcard TEXT)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS settings
                                 (id INTEGER PRIMARY KEY, language TEXT, resolution INTEGER)''')

            # Migration for color and transparency
            try:
                conn.execute("ALTER TABLE settings ADD COLUMN fg_color TEXT DEFAULT '#000000'")
            except sqlite3.OperationalError: pass
            try:
                conn.execute("ALTER TABLE settings ADD COLUMN bg_color TEXT DEFAULT '#ffffff'")
            except sqlite3.OperationalError: pass
            try:
                conn.execute("ALTER TABLE settings ADD COLUMN is_transparent INTEGER DEFAULT 0")
            except sqlite3.OperationalError: pass
            try:
                conn.execute("ALTER TABLE settings ADD COLUMN show_sidebar INTEGER DEFAULT 1")
            except sqlite3.OperationalError: pass

            # Migration: vcard identity used to be the UNIQUE `name` column, which
            # silently merged different people sharing a name. Drop that constraint
            # while preserving existing rows/ids so `id` becomes the real identity.
            row = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='vcard_archive'"
            ).fetchone()
            if row and row[0] and 'UNIQUE' in row[0]:
                conn.execute('''CREATE TABLE vcard_archive_new
                                     (id INTEGER PRIMARY KEY, name TEXT, fn TEXT, ln TEXT, org TEXT, title TEXT, email TEXT, phone TEXT, mobile TEXT, url TEXT, vcard TEXT)''')
                conn.execute('''INSERT INTO vcard_archive_new (id, name, fn, ln, org, title, email, phone, mobile, url, vcard)
                                     SELECT id, name, fn, ln, org, title, email, phone, mobile, url, vcard FROM vcard_archive''')
                conn.execute('DROP TABLE vcard_archive')
                conn.execute('ALTER TABLE vcard_archive_new RENAME TO vcard_archive')

    def add_url(self, url):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("INSERT OR IGNORE INTO url_archive (url) VALUES (?)", (url.strip(),))
            conn.commit()

    def get_urls(self):
        with sqlite3.connect(self.db_name) as conn:
            return conn.execute("SELECT url FROM url_archive").fetchall()

    def delete_url(self, url):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("DELETE FROM url_archive WHERE url = ?", (url,))

    def add_vcard(self, name, fn, ln, org, title, email, phone, mobile, url, vcard):
        with sqlite3.connect(self.db_name) as conn:
            cur = conn.execute('''INSERT INTO vcard_archive (name, fn, ln, org, title, email, phone, mobile, url, vcard)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (name.strip(), fn, ln, org, title, email, phone, mobile, url, vcard))
            conn.commit()
            return cur.lastrowid

    def update_vcard(self, vcard_id, name, fn, ln, org, title, email, phone, mobile, url, vcard):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('''UPDATE vcard_archive SET name=?, fn=?, ln=?, org=?, title=?, email=?, phone=?, mobile=?, url=?, vcard=?
                                 WHERE id=?''', (name.strip(), fn, ln, org, title, email, phone, mobile, url, vcard, vcard_id))
            conn.commit()

    def get_vcards(self):
        with sqlite3.connect(self.db_name) as conn:
            return conn.execute("SELECT id, name, fn, ln, org, title, email, phone, mobile, url, vcard FROM vcard_archive").fetchall()

    def delete_vcard(self, vcard_id):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("DELETE FROM vcard_archive WHERE id = ?", (vcard_id,))
            conn.commit()

    def get_settings(self):
        with sqlite3.connect(self.db_name) as conn:
            return conn.execute("SELECT language, resolution, fg_color, bg_color, is_transparent, show_sidebar FROM settings WHERE id=1").fetchone()

    def set_settings(self, language, resolution, fg_color="#000000", bg_color="#ffffff", is_transparent=0, show_sidebar=1):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('''INSERT OR REPLACE INTO settings (id, language, resolution, fg_color, bg_color, is_transparent, show_sidebar)
                                 VALUES (1, ?, ?, ?, ?, ?, ?)''', (language, resolution, fg_color, bg_color, is_transparent, show_sidebar))
            conn.commit()
