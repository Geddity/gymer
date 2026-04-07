import tkinter as tk
import sqlite3
import json
import time

from exercises import PlaceholderEntry

class PresetManager:
    def __init__(self, workout_managers, workout_names, workout_tab, add_workout_tab_func,
                 ExerciseManager, validate_float_func, validate_int_func, read_insert_func,
                 get_current_user_func, get_last_workout_data_func, save_last_user_func,
                 hide_frame_func, update_header_label_func, set_current_user_func,
                 set_last_preset_func, status_label, window):

        self.workout_managers = workout_managers
        self.workout_names = workout_names
        self.workout_tab = workout_tab
        self.add_workout_tab_func = add_workout_tab_func
        self.ExerciseManager = ExerciseManager
        self.validate_float_func = validate_float_func
        self.validate_int_func = validate_int_func
        self.read_insert_func = read_insert_func
        self.get_current_user_func = get_current_user_func
        self.get_last_workout_data_func = get_last_workout_data_func
        self.save_last_user_func = save_last_user_func
        self.hide_frame_func = hide_frame_func
        self.update_header_label_func = update_header_label_func
        self.set_current_user_func = set_current_user_func
        self.set_last_preset_func = set_last_preset_func
        self.status_label = status_label
        self.window = window

    def save_preset(self):
        current_user = self.get_current_user_func()

        if not current_user:
            print('No user')
            self.status_label.config(text='Chose user', fg='red')
            return

        if not self.workout_managers:
            print('No workout data')
            self.status_label.config(text='No workout data', fg='red')
            return

        dialog = tk.Toplevel(self.window)
        dialog.title("Save workout preset")
        dialog.geometry("300x150")
        dialog.transient(self.window)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="Preset name:", font=("Helvetica", 10, "bold")).pack(pady=10)
        preset_name_entry = tk.Entry(dialog, width=30)
        preset_name_entry.insert(0, f"{current_user}_preset_{time.strftime('%Y%m%d')}")
        preset_name_entry.pack(pady=5)

        def confirm_save():
            preset_name = preset_name_entry.get().strip()
            if not preset_name:
                print('No preset name')
                self.status_label.config(text='No preset name', fg='red')
                return

            self.set_last_preset_func(preset_name)
            self.save_last_user_func()

            conn = sqlite3.connect('user_data.db')
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS presets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    preset_name TEXT,
                    user TEXT,
                    updated_date TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workout_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    preset_id INTEGER,
                    workout_number INTEGER,
                    workout_name TEXT,
                    exercise_name TEXT,
                    weight_mode TEXT,
                    weight TEXT,
                    repeats TEXT,
                    FOREIGN KEY (preset_id) REFERENCES presets (id)
                )
            """)

            try:
                cursor.execute("""
                    SELECT id FROM presets
                    WHERE preset_name = ? AND user = ?
                """, (preset_name, current_user))

                existing = cursor.fetchone()

                if existing:
                    preset_id = existing[0]
                    cursor.execute("""
                        UPDATE presets
                        SET updated_date = ?
                        WHERE id = ?
                    """, (time.strftime("%Y-%m-%d"), preset_id))

                    cursor.execute("DELETE FROM workout_data WHERE preset_id = ?", (preset_id,))
                else:
                    cursor.execute("""
                        INSERT INTO presets (preset_name, user, updated_date)
                        VALUES (?, ?, ?)
                    """,(
                        preset_name,
                        current_user,
                        time.strftime("%Y-%m-%d")
                    ))
                    preset_id = cursor.lastrowid

                saved_count = 0
                for workout_num, manager in self.workout_managers.items():
                    tab_index = workout_num - 1
                    if 0 <= tab_index < self.workout_tab.index('end'):
                        workout_name = self.workout_tab.tab(tab_index, 'text')
                    else:
                        workout_name = self.workout_names.get(workout_num, f"Workout {workout_num}")

                    exercises = manager.get_all_data()

                    for exercise in exercises:
                        current_row = None
                        for row in manager.rows:
                            if row.exercise_name.cget('text') == exercise['name']:
                                current_row = row
                                break

                        if current_row:
                            if current_row.weight_is_label:
                                weight_mode = 'label'
                                weight_value = current_row.weight_label.cget('text')
                            else:
                                weight_mode = 'entry'
                                weight_value = exercise['weight']
                        else:
                            weight_mode = 'entry'
                            weight_value = exercise['weight']

                        cursor.execute("""
                            INSERT INTO workout_data (preset_id, workout_number, workout_name, exercise_name, 
                            weight_mode, weight, repeats)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,(
                            preset_id,
                            workout_num,
                            workout_name,
                            exercise['name'],
                            weight_mode,
                            weight_value,
                            json.dumps(exercise['repeats'], ensure_ascii=False)
                        ))
                        saved_count += 1

                conn.commit()

                self.status_label.config(text='Preset saved', fg='green')

                dialog.destroy()

            except Exception as e:
                conn.rollback()
                print(f"Save error: {e}")
                self.status_label.config(text='Preset not saved', fg='red')
            finally:
                conn.close()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text='Save', command=confirm_save, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text='Cancel', command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=5)

    def load_preset(self):
        current_user = self.get_current_user_func()

        if not current_user:
            print('No user')
            self.status_label.config(text='Select user', fg='red')
            return

        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, preset_name, updated_date
            FROM presets
            WHERE user = ?
            ORDER BY updated_date DESC
        """, (current_user,))

        presets = cursor.fetchall()
        conn.close()

        if not presets:
            print('No saved presets')
            self.status_label.config(text='No saved presets', fg='red')
            return

        dialog = tk.Toplevel(self.window)
        dialog.title("Load preset")
        dialog.geometry("420x380")
        dialog.transient(self.window)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - (dialog.winfo_height() // 5 * 3)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text='Select preset:', font=('Helvetica', 10, 'bold')).pack(pady=10)

        list_frame = tk.Frame(dialog)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)

        canvas = tk.Canvas(list_frame)
        scrollbar = tk.Scrollbar(list_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        selected_preset = tk.IntVar()

        for preset in presets:
            preset_id, name, updated = preset

            preset_frame = tk.Frame(scrollable_frame, relief='groove', bd=1)
            preset_frame.pack(fill='x', pady=5, padx=5)

            radio = tk.Radiobutton(preset_frame, variable=selected_preset, value=preset_id)
            radio.pack(side=tk.LEFT, padx=5)

            info_frame = tk.Frame(preset_frame)
            info_frame.pack(side=tk.LEFT, fill='x', expand=True)

            tk.Label(info_frame, text=name, font=('Arial', 10, 'bold'), anchor='w').pack(fill='x')
            tk.Label(info_frame, text=f"Updated: {updated}", font=('Arial', 8), fg='gray', anchor='w').pack(fill='x')

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        def confirm_load():
            preset_id = selected_preset.get()
            if not preset_id:
                print('No preset chosen')
                self.status_label.config(text='Select preset to load', fg='orange')
                return

            conn = sqlite3.connect('user_data.db')
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    SELECT preset_name FROM presets
                    WHERE id = ? AND user = ?
                """, (preset_id, current_user))

                preset_info = cursor.fetchone()
                if not preset_info:
                    print('Preset not found')
                    self.status_label.config(text='Preset not found', fg='red')
                    return

                preset_name = preset_info[0]
                self.set_last_preset_func(preset_name)
                self.save_last_user_func()

                cursor.execute("""
                    SELECT workout_number, workout_name, exercise_name, weight_mode, weight, repeats
                    FROM workout_data
                    WHERE preset_id = ?
                    ORDER BY workout_number
                """, (preset_id,))

                workout_data = cursor.fetchall()

                if not workout_data:
                    print('No workout data')
                    self.status_label.config(text='Workout data is empty', fg='red')
                    return

                for manager in self.workout_managers.values():
                    manager.delete_all_rows()

                while self.workout_tab.index('end') > 0:
                    self.workout_tab.forget(0)

                self.workout_managers.clear()
                self.workout_names.clear()

                workouts = {}
                for workout_num, workout_name, ex_name, weight_mode, weight, repeats_json in workout_data:
                    if workout_num not in workouts:
                        workouts[workout_num] = {
                            'workout_name': workout_name,
                            'exercises': []
                        }
                    workouts[workout_num]['exercises'].append({
                        'name': ex_name,
                        'weight_mode': weight_mode,
                        'weight': weight,
                        'repeats': json.loads(repeats_json)
                    })

                for workout_num in sorted(workouts.keys()):
                    workout_name = workouts[workout_num]['workout_name']
                    self.add_workout_tab_func(workout_num, workout_name)

                for workout_num, workout_data in workouts.items():
                    manager = self.workout_managers.get(workout_num)
                    if manager:
                        exercises = workout_data['exercises']

                        for ex in exercises:
                            manager.add_row(ex['name'], skip_initial_reps=True)

                            if manager.rows:
                                last_row = manager.rows[-1]

                                if ex['weight_mode'] == 'label':
                                    last_row.weight_entry.pack_forget()
                                    last_row.weight_label.config(text=ex['weight'])
                                    last_row.weight_label.pack(side=tk.LEFT)
                                    last_row.weight_is_label = True
                                else:
                                    last_row.weight_label.pack_forget()
                                    last_row.weight_entry.delete(0, tk.END)
                                    validate = (last_row.parent.register(self.validate_float_func), '%P')
                                    last_row.weight_entry.config(validate='key', validatecommand=validate)
                                    last_row.weight_entry.insert(0, ex['weight'])
                                    last_row.weight_entry.pack(side=tk.LEFT)
                                    last_row.weight_is_label = False

                                for entry in last_row.rep_entries:
                                    entry.destroy()

                                last_row.rep_entries.clear()
                                last_row.rep_entry_count = 0

                                for rep in ex['repeats']:
                                    new_entry = tk.Entry(last_row.repeats_frame, width=3)
                                    validate = (last_row.parent.register(self.validate_int_func), '%P')
                                    new_entry.config(validate='key', validatecommand=validate)
                                    new_entry.insert(0, rep)
                                    new_entry.pack(side=tk.LEFT, padx=1)
                                    last_row.rep_entries.append(new_entry)
                                    last_row.rep_entry_count += 1

                                last_row.update_butt_state()

                self.status_label.config(text='Preset loaded', fg='green')

                dialog.destroy()

            except Exception as e:
                print(f"Load error {e}")
                self.status_label.config(text='Loading failed', fg='red')
            finally:
                conn.close()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text='Load', command=confirm_load, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text='Cancel', command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=5)

    def delete_preset(self):
        current_user = self.get_current_user_func()

        if not current_user:
            print('No user')
            self.status_label.config(text='Select user', fg='orange')
            return

        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, preset_name, updated_date
            FROM presets
            WHERE user = ?
            ORDER BY updated_date DESC
        ''', (current_user,))

        presets = cursor.fetchall()
        conn.close()

        if not presets:
            print('No presets')
            self.status_label.config(text='No presets found', fg='red')
            return

        dialog = tk.Toplevel(self.window)
        dialog.title("Delete preset")
        dialog.geometry("420x380")
        dialog.transient(self.window)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - (dialog.winfo_height() // 5 * 3)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text='Select preset:', font=('Arial', 10, 'bold')).pack(pady=10)

        list_frame = tk.Frame(dialog)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)

        canvas = tk.Canvas(list_frame)
        scrollbar = tk.Scrollbar(list_frame, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        selected_preset = tk.IntVar()

        for preset in presets:
            preset_id, name, date = preset

            preset_frame = tk.Frame(scrollable_frame, relief='groove', bd=1)
            preset_frame.pack(fill='x', pady=5, padx=5)

            radio = tk.Radiobutton(preset_frame, variable=selected_preset, value=preset_id)
            radio.pack(side=tk.LEFT, padx=5)

            info_frame = tk.Frame(preset_frame)
            info_frame.pack(side=tk.LEFT, fill='x', expand=True)

            tk.Label(info_frame, text=name, font=('Arial', 10, 'bold'), anchor='w').pack(fill='x')
            tk.Label(info_frame, text=f"Date: {date}", font=('Arial', 8), fg='gray', anchor='w').pack(fill='x')

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        def confirm_delete():
            selection = selected_preset.get()
            if not selection:
                print('No preset selected')
                self.status_label.config(text='Select preset to delete', fg='orange')
                return

            preset_id = selected_preset.get()

            confirm_dialog = tk.Toplevel(dialog)
            confirm_dialog.title("Confirm delete")
            confirm_dialog.geometry("300x100")
            confirm_dialog.transient(dialog)
            confirm_dialog.grab_set()

            confirm_dialog.update_idletasks()
            x = dialog.winfo_x() + (dialog.winfo_width() // 2) - (confirm_dialog.winfo_width() // 2)
            y = dialog.winfo_y() + (dialog.winfo_height() // 2) - (confirm_dialog.winfo_height() // 2)
            confirm_dialog.geometry(f"+{x}+{y}")

            tk.Label(confirm_dialog, text='Delete selected preset?', pady=10).pack()

            def do_delete():
                conn = sqlite3.connect('user_data.db')
                cursor = conn.cursor()

                try:
                    cursor.execute('DELETE FROM workout_data WHERE preset_id = ?', (preset_id,))
                    cursor.execute('DELETE FROM presets WHERE id = ?', (preset_id,))
                    conn.commit()

                    print(f"Preset {preset_id} deleted")
                    self.status_label.config(text='Preset deleted', fg='green')
                    confirm_dialog.destroy()
                    dialog.destroy()

                except Exception as e:
                    conn.rollback()
                    print(f"Delete error: {e}")
                finally:
                    conn.close()

            btn_frame = tk.Frame(confirm_dialog)
            btn_frame.pack(pady=10)

            tk.Button(btn_frame, text='Delete', command=do_delete, width=10).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text='Cancel', command=confirm_dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text='Delete', command=confirm_delete, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text='Cancel', command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=5)

    def load_specific_preset(self, preset_name, user_name):
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id FROM presets
                WHERE preset_name = ? AND user = ?
            """, (preset_name, user_name))

            chosen_preset = cursor.fetchone()

            if not chosen_preset:
                print(f"Preset {preset_name} not found")
                return False

            preset_id = chosen_preset[0]

            cursor.execute("""
                SELECT workout_number, workout_name, exercise_name, weight_mode, weight, repeats
                FROM workout_data
                WHERE preset_id = ?
                ORDER BY workout_number
            """, (preset_id,))

            workout_data = cursor.fetchall()

            if not workout_data:
                print("No data in preset")
                return False

            last_data_for_workout = {}
            for workout_num, workout_name, ex_name, weight_mode, weight, repeats_json in workout_data:
                if workout_num not in last_data_for_workout:
                    last_data_for_workout[workout_num] = self.get_last_workout_data_func(user_name, workout_num)

            for manager in self.workout_managers.values():
                manager.delete_all_rows()

            while self.workout_tab.index('end') > 0:
                self.workout_tab.forget(0)

            self.workout_managers.clear()
            self.workout_names.clear()

            workouts = {}
            for workout_num, workout_name, ex_name, weight_mode, weight, repeats_json in workout_data:
                if workout_num not in workouts:
                    workouts[workout_num] = {
                        'workout_name': workout_name,
                        'exercises': []
                    }
                workouts[workout_num]['exercises'].append({
                    'name': ex_name,
                    'weight_mode': weight_mode,
                    'weight': weight,
                    'repeats': json.loads(repeats_json)
                })

            for workout_num in sorted(workouts.keys()):
                workout_info = workouts[workout_num]
                workout_name = workout_info['workout_name']

                self.add_workout_tab_func(workout_num, workout_name)

            for workout_num, workout_data_item in workouts.items():
                manager = self.workout_managers.get(workout_num)
                if manager:
                    last_data = last_data_for_workout.get(workout_num, {})

                    for ex in workout_data_item['exercises']:
                        ex_name = ex['name']
                        last_ex_data = last_data.get(ex_name, {})

                        manager.add_row(ex['name'], skip_initial_reps=True)

                        if manager.rows:
                            last_row = manager.rows[-1]

                            if ex['weight_mode'] == 'label':
                                last_row.weight_entry.pack_forget()

                                if last_ex_data.get('weight'):
                                    weight_value = last_ex_data['weight']
                                else:
                                    weight_value = ex['weight']

                                last_row.weight_label.config(text=weight_value)
                                last_row.weight_label.pack(side=tk.LEFT)
                                last_row.weight_is_label = True
                            else:
                                last_row.weight_label.pack_forget()
                                last_row.weight_entry.delete(0, tk.END)

                                if last_ex_data.get('weight'):
                                    weight_value = last_ex_data['weight']
                                else:
                                    weight_value = ex['weight']

                                last_row.weight_entry.insert(0, weight_value)
                                last_row.weight_entry.pack(side=tk.LEFT)
                                last_row.weight_is_label = False

                            for entry in last_row.rep_entries:
                                entry.destroy()
                            last_row.rep_entries.clear()
                            last_row.rep_entry_count = 0

                            if last_ex_data.get('repeats'):
                                reps_to_load = last_ex_data['repeats']
                            else:
                                reps_to_load = ex['repeats']

                            for rep in reps_to_load:
                                new_entry = PlaceholderEntry(last_row.repeats_frame, width=3)
                                validate = (last_row.parent.register(self.validate_int_func), '%P')
                                new_entry.config(validate='key', validatecommand=validate)
                                new_entry.set_placeholder(rep)
                                new_entry.pack(side=tk.LEFT, padx=1)
                                last_row.rep_entries.append(new_entry)
                                last_row.rep_entry_count += 1

                            last_row.update_butt_state()

            if self.workout_tab.index('end') > 0:
                self.workout_tab.select(0)

            print(f"Preset {preset_name} loaded")
            self.status_label.config(text='Preset loaded', fg='green')
            return True

        except Exception as e:
            print(f"Preset loading error: {e}")
            self.status_label.config(text='Preset loading failed', fg='red')
            return False
        finally:
            conn.close()

    def auto_load_last_preset(self):
        try:
            conn = sqlite3.connect('user_data.db')
            cursor = conn.cursor()

            cursor.execute("""SELECT user_name, preset_name FROM last_user_data""")
            last_data = cursor.fetchall()

            if not last_data:
                print("No last user data")
                return False

            last_user_name, last_preset_name = last_data[0]

            if not last_user_name or not last_preset_name:
                print("No last preset data")
                return False

            self.set_current_user_func(last_user_name)
            self.set_last_preset_func(last_preset_name)

            cursor.execute("""
                SELECT user_name FROM last_user_data WHERE user_name = ?
            """, (last_user_name,))

            user_exists = cursor.fetchone()

            if not user_exists:
                print(f"User {last_user_name} not found")
                conn.close()
                return False

            cursor.execute("""
                SELECT id FROM presets
                WHERE preset_name = ? AND user = ?
            """, (last_preset_name, last_user_name))

            preset_exists = cursor.fetchone()
            conn.close()

            if not preset_exists:
                print(f"Preset {last_preset_name} not found")
                return False

            self.update_header_label_func(last_user_name)
            self.hide_frame_func()

            result = self.load_specific_preset(last_preset_name, last_user_name)

            if result:
                print(f"Autoloaded user: {last_user_name}")
                print(f"Autoloaded preset: {last_preset_name}")
                self.status_label.config(text=f"Autoloaded: {last_user_name} - {last_preset_name}", fg='green')
                return True
            else:
                print(f"Failed to load: {last_preset_name}")
                return False

        except Exception as e:
            print(f"Autoload error: {e}")
            return False