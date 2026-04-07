import sqlite3
import tkinter as tk


class UserManager:
    def __init__(self, header_label, status_label, window, hide_frame_func, show_frame_func,
                 read_insert_func, change_butt, top_frame, toggle_frame, user_chose_box,
                 new_user_entry, chose_butt, create_butt):

        self.header_label = header_label
        self.status_label = status_label
        self.window = window
        self.hide_frame_func = hide_frame_func
        self.show_frame_func = show_frame_func
        self.read_insert_func = read_insert_func
        self.change_butt = change_butt
        self.top_frame = top_frame
        self.toggle_frame = toggle_frame
        self.user_chose_box = user_chose_box
        self.new_user_entry = new_user_entry
        self.chose_butt = chose_butt
        self.create_butt = create_butt

        self.current_user = ''
        self.last_user = ''
        self.last_preset = ''

    def get_current_user(self):
        return self.current_user

    def set_current_user(self, user):
        self.current_user = user
        self.last_user = user
        self.header_label.config(text=f"Current User: {self.current_user}")

    def get_last_preset(self):
        return self.last_preset

    def set_last_preset(self, preset_name):
        self.last_preset = preset_name

    def init_database(self):
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_keys = ON")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT UNIQUE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preset_name TEXT,
                user TEXT,
                updated_date TEXT,
                FOREIGN KEY (user) REFERENCES users(user_name) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workout_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preset_id INTEGER,
                workout_number INTEGER,
                workout_name TEXT,
                exercise_name TEXT,
                weight_mode TEXT,
                weight TEXT,
                repeats TEXT,
                FOREIGN KEY (preset_id) REFERENCES presets (id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                workout_name TEXT,
                workout_number INTEGER,
                date TEXT,
                exercise_name TEXT,
                weight_mode TEXT,
                weight TEXT,
                repeats TEXT,
                FOREIGN KEY (user) REFERENCES users(user_name) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS last_user_data (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                user_name TEXT,
                preset_name TEXT,
                FOREIGN KEY (user_name) REFERENCES users(user_name) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        conn.close()
        print("Database initialized")

    def extract_users(self):
        try:
            conn = sqlite3.connect('user_data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT user_name FROM users ORDER BY user_name")
            names = [row[0] for row in cursor.fetchall()]
            conn.close()
            return names
        except Exception as e:
            print(f"User extraction error: {e}")
            return []

    def create_new_user(self):
        new_user_name = self.new_user_entry.get().strip()

        if not new_user_name:
            self.status_label.config(text='No user name', fg='red')
            return

        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()

        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT UNIQUE
        )""")

        try:
            cursor.execute("INSERT INTO users (user_name) VALUES (?)", (new_user_name,))
            conn.commit()

            self.current_user = new_user_name
            self.last_user = new_user_name
            self.last_preset = ''

            self.header_label.config(text=f"Current User: {self.current_user}")
            self.hide_frame_func()
            self.save_last_user()

            self.user_chose_box.config(values=self.extract_users())
            self.status_label.config(text='User created', fg='green')

        except sqlite3.IntegrityError:
            self.status_label.config(text='User already exists', fg='red')
        except Exception as e:
            print(f"User creation error: {e}")
            self.status_label.config(text='User creation failed', fg='red')
        finally:
            conn.close()

    def chose_user(self):
        chosen_user = self.user_chose_box.get()

        if not chosen_user:
            self.status_label.config(text='Select a user', fg='orange')
            return

        self.current_user = chosen_user
        self.last_user = chosen_user

        self.save_last_user()

        self.header_label.config(text=f"Current User: {self.current_user}")
        self.status_label.config(text=f"Oh, hi, {self.current_user}", fg='green')

        self.hide_frame_func()

    def save_last_user(self):
        self.set_last_preset(self.last_preset)

        try:
            conn = sqlite3.connect('user_data.db')
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS last_user_data (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    user_name TEXT,
                    preset_name TEXT
                )
            """)

            cursor.execute("""
                REPLACE INTO last_user_data (id, user_name, preset_name)
                VALUES (1, ?, ?)
            """, (self.current_user, self.last_preset))

            conn.commit()
            conn.close()
            print(f"Last user saved: {self.current_user}, preset: {self.last_preset}")
        except Exception as e:
            print(f"Last user saving error: {e}")

    def load_last_user(self):
        try:
            conn = sqlite3.connect('user_data.db')
            cursor = conn.cursor()

            cursor.execute("SELECT user_name, preset_name FROM last_user_data")
            result = cursor.fetchone()
            conn.close()

            if result:
                return result[0], result[1]
            return None, None
        except Exception as e:
            print(f"Last user loading error: {e}")
            return None, None

    def refresh_user_list(self):
        self.user_chose_box.config(values=self.extract_users())

    def delete_user(self, user_name=None):
        if user_name is None:
            user_name = self.user_chose_box.get()

        if not user_name:
            self.status_label.config(text='Select a user', fg='orange')
            return False

        confirm_dialog = tk.Toplevel(self.window)
        confirm_dialog.title("Confirm Delete")
        confirm_dialog.geometry("220x80")
        confirm_dialog.transient(self.window)
        confirm_dialog.grab_set()

        confirm_dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - (confirm_dialog.winfo_width() // 2)
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - (confirm_dialog.winfo_height() // 2)
        confirm_dialog.geometry(f"+{x}+{y}")

        tk.Label(confirm_dialog, text=f"Delete user '{user_name}' and all their data?",
                 justify=tk.LEFT, padx=20, pady=10).pack()

        def confirm_delete():
            conn = sqlite3.connect('user_data.db')
            cursor = conn.cursor()

            cursor.execute("PRAGMA foreign_keys = ON")

            try:
                cursor.execute("DELETE FROM users WHERE user_name = ?", (user_name,))
                conn.commit()

                deleted = cursor.rowcount > 0

                if deleted:
                    if self.current_user == user_name:
                        self.current_user = ''
                        self.last_user = ''
                        self.last_preset = ''
                        self.header_label.config(text="Current User: ")
                        self.show_frame_func()

                    self.refresh_user_list()
                    self.status_label.config(text=f"{user_name} deleted", fg='orange')
                    confirm_dialog.destroy()
                else:
                    self.status_label.config(text=f"User {user_name} not found", fg='red')

                return deleted

            except Exception as e:
                conn.rollback()
                print(f"User deletion error: {e}")
                self.status_label.config(text=f"Deletion failed: {e}", fg='red')
                return False
            finally:
                conn.close()

        btn_frame = tk.Frame(confirm_dialog)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Delete", command=confirm_delete, width=10, height=1).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=confirm_dialog.destroy, width=10, height=1).pack(side=tk.LEFT, padx=5)