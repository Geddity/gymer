import tkinter as tk
from tkinter import ttk
import json
import sqlite3
import time
from datetime import datetime, timedelta


class WorkoutManager:
    def __init__(self, workout_tab, workout_managers, workout_names, ExerciseManager,
                 validate_float_func, validate_int_func, read_insert_func, get_current_user_func,
                 status_label, window):

        self.workout_tab = workout_tab
        self.workout_managers = workout_managers
        self.workout_names = workout_names
        self.ExerciseManager = ExerciseManager
        self.validate_float_func = validate_float_func
        self.validate_int_func = validate_int_func
        self.read_insert_func = read_insert_func
        self.get_current_user_func = get_current_user_func
        self.status_label = status_label
        self.window = window

    def add_workout_tab(self, workout_num, custom_name=None):
        workout_frame = ttk.Frame(self.workout_tab)

        if custom_name:
            tab_name = custom_name
        else:
            tab_name = f"Workout {workout_num}"

        self.workout_tab.add(workout_frame, text=tab_name)

        column_widths = [170, 100, 130, 60, 40]
        for col, width in enumerate(column_widths):
            workout_frame.grid_columnconfigure(col, weight=0, minsize=width)

        manager = self.ExerciseManager(
            workout_frame,
            validate_float_func=self.validate_float_func,
            validate_int_func=self.validate_int_func,
            read_insert_func=self.read_insert_func,
            get_current_user_func=self.get_current_user_func
        )
        self.workout_managers[workout_num] = manager

        if custom_name:
            self.workout_names[workout_num] = custom_name

        return manager

    def add_new_workout_tab(self):
        if len(self.workout_managers) <= 5:
            next_tab = len(self.workout_managers) + 1
            self.add_workout_tab(next_tab)
            self.workout_tab.select(next_tab - 1)

    def remove_workout_tab(self):
        tab_count = self.workout_tab.index('end')

        if tab_count > 1:
            last_tab_index = tab_count - 1
            workout_num = tab_count

            if workout_num in self.workout_managers:
                self.workout_managers[workout_num].delete_all_rows()
                del self.workout_managers[workout_num]

            if workout_num in self.workout_names:
                del self.workout_names[workout_num]

            self.workout_tab.forget(last_tab_index)
        else:
            print("Workout remove error")
            self.status_label.config(text='Cannot remove last workout', fg='red')

    def rename_workout_tab(self, event=None):
        current_tab_index = self.workout_tab.index(self.workout_tab.select())
        workout_num = current_tab_index + 1
        current_name = self.workout_tab.tab(current_tab_index, "text")

        dialog = tk.Toplevel(self.window)
        dialog.title("Rename workout")
        dialog.geometry("200x150")
        dialog.transient(self.window)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text='New workout name:', font=('Helvetica', 10, 'bold')).pack(pady=10)

        name_entry = tk.Entry(dialog, width=25)
        name_entry.insert(0, current_name)
        name_entry.pack(pady=5)
        name_entry.select_range(0, tk.END)
        name_entry.focus()

        def save_name():
            new_name = name_entry.get().strip()
            if not new_name:
                self.status_label.config(text='Name cant be empty', fg='red')
                return

            self.workout_tab.tab(current_tab_index, text=new_name)
            self.workout_names[workout_num] = new_name

            self.status_label.config(text=f"Workout {current_name} renamed to {new_name}", fg='green')
            dialog.destroy()

        name_entry.bind('<Return>', lambda e: save_name())

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text='Save', command=save_name, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text='Cancel', command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def add_exercise_to_current_tab(self, new_ex_entry):
        current_tab = self.workout_tab.index(self.workout_tab.select()) + 1

        if current_tab in self.workout_managers:
            if new_ex_entry.get() == '':
                name = f"Exercise {len(self.workout_managers[current_tab].rows) + 1}"
            else:
                name = new_ex_entry.get()
                new_ex_entry.delete(0, tk.END)

            self.workout_managers[current_tab].add_row(name)
            self.status_label.config(text=f"Exercise '{name}' added", fg='green')
        else:
            self.status_label.config(text='No workout tab found', fg='red')

    def save_current_workout_data(self):
        current_tab = self.workout_tab.index(self.workout_tab.select()) + 1
        current_user = self.get_current_user_func()

        if current_tab not in self.workout_managers:
            self.status_label.config(text='Workout not found', fg='red')
            return

        manager = self.workout_managers[current_tab]
        exercises = manager.get_all_data()

        if not exercises:
            self.status_label.config(text='No exercises to save', fg='orange')
            return

        current_tab_name = self.workout_tab.tab(current_tab - 1, 'text')
        rows = manager.rows

        dialog = tk.Toplevel(self.window)
        dialog.title('Save workout')
        dialog.transient(self.window)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        save_header_frame = tk.Frame(dialog)
        save_header_frame.pack(fill='x', padx=5)

        current_workout_name = tk.Label(save_header_frame, text=current_tab_name)
        current_workout_name.pack(pady=5, anchor='w')

        current_date = time.strftime('%Y-%m-%d')

        date_entry = tk.Entry(save_header_frame, width=14)
        date_entry.insert(0, current_date)
        date_entry.pack(pady=5, anchor='w')

        check_status_label = tk.Label(save_header_frame, text="", fg="orange", font=("Helvetica", 9))
        check_status_label.pack(pady=2, anchor='w')

        exercises_frame = tk.Frame(dialog)
        exercises_frame.pack(fill='x', padx=5, pady=5)

        exercise_widgets = []

        for i, (exercise, row) in enumerate(zip(exercises, rows)):
            name_label = tk.Label(exercises_frame, text=f"{exercise['name']}")
            name_label.pack(side=tk.TOP, anchor='w')

            data_frame = tk.Frame(exercises_frame)
            data_frame.pack(side=tk.TOP, anchor='w')

            if row.weight_label.winfo_viewable():
                weight_data = tk.Label(data_frame, width=5, text=row.weight_label.cget('text'))
                weight_data.pack(side=tk.LEFT, padx=20)
                weight_mode = 'label'
            else:
                weight_data = tk.Entry(data_frame, width=6)
                validate = (weight_data.register(self.validate_float_func), '%P')
                weight_data.config(validate='key', validatecommand=validate)
                weight_data.insert(0, exercise['weight'])
                weight_data.pack(side=tk.LEFT, padx=20)
                weight_mode = 'entry'

            repeat_entries = []

            for rep in exercise['repeats']:
                rep_entry = tk.Entry(data_frame, width=4)
                validate = (rep_entry.register(self.validate_int_func), '%P')
                rep_entry.config(validate='key', validatecommand=validate)
                rep_entry.insert(0, rep)
                rep_entry.pack(side=tk.LEFT, padx=2)
                repeat_entries.append(rep_entry)

            exercise_widgets.append({
                'name_label': name_label,
                'weight_data': weight_data,
                'weight_mode': weight_mode,
                'repeat_entries': repeat_entries,
                'original_row': row
            })

        workout_exists = False
        existing_workout_info = None

        def check_workout_exists():
            nonlocal workout_exists, existing_workout_info
            workout_name = current_workout_name.cget('text').strip()
            workout_date = date_entry.get().strip()

            if not workout_name or not workout_date:
                check_status_label.config(text='')
                workout_exists = False
                existing_workout_info = None
                return False

            conn = sqlite3.connect('user_data.db')
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM saved_workouts
                    WHERE user = ? AND workout_name = ? AND date = ?
                """, (current_user, workout_name, workout_date))

                count = cursor.fetchone()[0]

                if count > 0:
                    check_status_label.config(
                        text=f"Workout '{workout_name}' already exists on {workout_date}!",
                        fg="orange"
                    )

                    workout_exists = True

                    cursor.execute("""
                        SELECT COUNT(*) FROM saved_workouts
                        WHERE user = ? AND workout_name = ? AND date = ?
                    """, (current_user, workout_name, workout_date))
                    existing_workout_info = {
                        'count': cursor.fetchone()[0]
                    }

                    return True
                else:
                    workout_exists = False
                    existing_workout_info = None
                    return False
            except Exception as e:
                print(f"Check error: {e}")
                check_status_label.config(text="")
                workout_exists = False
                existing_workout_info = None
                return False
            finally:
                conn.close()

        def on_date_change(event=None):
            check_workout_exists()

        date_entry.bind('<KeyRelease>', on_date_change)

        check_workout_exists()

        def confirm_save():
            nonlocal workout_exists
            workout_name = current_workout_name.cget('text').strip()

            if not workout_name:
                self.status_label.config(text='Enter workout name', fg='red')
                return

            workout_date = date_entry.get().strip()
            if not workout_date:
                workout_date = time.strftime('%Y-%m-%d')

            if workout_exists:
                confirm_dialog = tk.Toplevel(dialog)
                confirm_dialog.title("Confirm Overwrite")
                confirm_dialog.geometry("300x100")
                confirm_dialog.transient(dialog)
                confirm_dialog.grab_set()

                confirm_dialog.update_idletasks()
                x = dialog.winfo_x() + (dialog.winfo_width() // 2) - (confirm_dialog.winfo_width() // 2)
                y = dialog.winfo_y() + (dialog.winfo_height() // 2) - (confirm_dialog.winfo_height() // 2)
                confirm_dialog.geometry(f"+{x}+{y}")

                tk.Label(confirm_dialog, text='Overwrite workout?', justify=tk.CENTER).pack(pady=10)

                confirm_result = False

                def on_overwrite():
                    nonlocal confirm_result
                    confirm_result = True
                    confirm_dialog.destroy()
                    perform_save(workout_name, workout_date, dialog)

                def on_cancel():
                    nonlocal confirm_result
                    confirm_result = False
                    confirm_dialog.destroy()

                btn_frame = tk.Frame(confirm_dialog)
                btn_frame.pack(pady=10)

                tk.Button(btn_frame, text="Overwrite", command=on_overwrite, width=12).pack(side=tk.LEFT, padx=10)
                tk.Button(btn_frame, text="Cancel", command=on_cancel, width=12).pack(side=tk.LEFT, padx=10)

                return

            perform_save(workout_name, workout_date, dialog)

        def perform_save(workout_name, workout_date, parent_dialog):
            conn = sqlite3.connect('user_data.db')
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    DELETE FROM saved_workouts
                    WHERE user = ? AND workout_name = ? AND date = ?
                """, (current_user, workout_name, workout_date))

                for index, ex_widget in enumerate(exercise_widgets, start=1):
                    exercise_name = ex_widget['name_label'].cget('text')

                    if exercise_name.endswith(':'):
                        exercise_name = exercise_name[:-1]
                    exercise_name = exercise_name.strip()

                    print(f"Saving exercise: '{exercise_name}'")

                    if ex_widget['weight_mode'] == 'label':
                        weight_value = ex_widget['weight_data'].cget('text')
                    else:
                        weight_value = ex_widget['weight_data'].get()

                    repeats = [entry.get() for entry in ex_widget['repeat_entries']]

                    cursor.execute('''
                        INSERT INTO saved_workouts (
                        user, workout_name, workout_number, date, 
                        exercise_name, weight_mode, weight, repeats, exercise_number)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        current_user,
                        workout_name,
                        current_tab,
                        workout_date,
                        exercise_name,
                        ex_widget['weight_mode'],
                        weight_value,
                        json.dumps(repeats, ensure_ascii=False),
                        index
                    ))

                conn.commit()

                self.status_label.config(text=f"Workout '{workout_name}' saved", fg='green')
                parent_dialog.destroy()

            except Exception as e:
                conn.rollback()
                print(f"Saving error: {e}")
                self.status_label.config(text='Saving failed', fg='red')
            finally:
                conn.close()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text='Save', command=confirm_save, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text='Cancel', command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=5)

    def delete_specific_workout(self):
        current_user = self.get_current_user_func()

        if not current_user:
            self.status_label.config(text='User not chosen', fg='red')
            return

        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT workout_name, date
            FROM saved_workouts
            WHERE user = ?
            ORDER BY date DESC
        """, (current_user,))

        workouts = cursor.fetchall()
        conn.close()

        if not workouts:
            self.status_label.config(text='No saved workouts', fg='orange')
            return

        dialog = tk.Toplevel(self.window)
        dialog.title("Delete workout")
        dialog.geometry("420x380")
        dialog.transient(self.window)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - (dialog.winfo_height() // 5 * 3)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text='Workout to delete:', font=('Helvetica', 10, 'bold')).pack(pady=10)

        list_frame = tk.Frame(dialog)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)

        canvas = tk.Canvas(list_frame)
        canvas.pack(side='left', fill='both', expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')

        scrollable_frame = tk.Frame(canvas)
        scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')

        selected_workout = tk.IntVar(value=-1)

        for i, workout in enumerate(workouts):
            workout_name, date = workout

            workout_frame = tk.Frame(scrollable_frame, relief='groove', bd=1)
            workout_frame.pack(fill='x', pady=2, padx=2)

            radio = tk.Radiobutton(workout_frame, variable=selected_workout, value=i)
            radio.pack(side=tk.LEFT, padx=5)

            info_frame = tk.Frame(workout_frame)
            info_frame.pack(side=tk.LEFT, fill='x', expand=True)

            tk.Label(info_frame, text=workout_name, font=('Helvetica', 10, 'bold'), anchor='w').pack(fill='x')
            tk.Label(info_frame, text=f"Date: {date}", font=('Helvetica', 8), fg='gray', anchor='w').pack(fill='x')

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        def confirm_delete():
            selected = selected_workout.get()
            if selected == -1:
                self.status_label.config(text='Chose workout to delete', fg='orange')
                return

            workout_name, date = workouts[selected]

            confirm_dialog = tk.Toplevel(dialog)
            confirm_dialog.title("Confirm delete")
            confirm_dialog.geometry("300x100")
            confirm_dialog.transient(dialog)
            confirm_dialog.grab_set()

            confirm_dialog.update_idletasks()
            x = dialog.winfo_x() + (dialog.winfo_width() // 2) - (confirm_dialog.winfo_width() // 2)
            y = dialog.winfo_y() + (dialog.winfo_height() // 2) - (confirm_dialog.winfo_height() // 2)
            confirm_dialog.geometry(f"+{x}+{y}")

            tk.Label(confirm_dialog, text=f"Delete workout '{workout_name}' from {date}?", pady=10).pack()

            def do_delete():
                conn = sqlite3.connect('user_data.db')
                cursor = conn.cursor()

                try:
                    cursor.execute("""
                        DELETE FROM saved_workouts
                        WHERE user = ? AND workout_name = ? AND date = ?
                    """, (current_user, workout_name, date))

                    conn.commit()

                    deleted = cursor.rowcount
                    print(f"Deleted {deleted} records")

                    self.status_label.config(text=f"Workout '{workout_name}' deleted", fg='green')

                    confirm_dialog.destroy()
                    dialog.destroy()

                except Exception as e:
                    conn.rollback()
                    print(f"Delete error: {e}")
                    self.status_label.config(text='Delete failed', fg='red')
                finally:
                    conn.close()

            btn_frame = tk.Frame(confirm_dialog)
            btn_frame.pack(pady=10)

            tk.Button(btn_frame, text='Delete it!', command=do_delete, width=10).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text='Cancel', command=confirm_dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text='Delete', command=confirm_delete, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text='Cancel', command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def get_last_workout_data(self, user_name, workout_number=None):
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()

        try:
            cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='saved_workouts'
                """)

            table_exists = cursor.fetchone()
            if not table_exists:
                print("Table 'saved_workouts' does not exist")
                return {}

            cursor.execute('''
                    SELECT exercise_name, weight, repeats, date, workout_name
                    FROM saved_workouts 
                    WHERE user = ? AND workout_number = ?
                    ORDER BY exercise_name, date DESC
                ''', (user_name, workout_number))

            all_data = cursor.fetchall()

            result = {}
            for ex_name, weight, repeats_json, date, workout_name in all_data:
                if ex_name not in result:
                    try:
                        repeats = json.loads(repeats_json) if repeats_json else []
                    except:
                        repeats = []
                    result[ex_name] = {
                        'weight': weight,
                        'repeats': repeats,
                        'date': date,
                        'workout_name': workout_name
                    }

            print(f"Found {len(result)} exercises with last data for workout #{workout_number}")
            return result

        except Exception as e:
            print(f"Error getting last workout data: {e}")
            return {}
        finally:
            conn.close()

    def get_workout_progress(self):
        current_user = self.get_current_user_func()
        workout_num = self.workout_tab.index(self.workout_tab.select()) + 1
        current_tab_name = self.workout_tab.tab(workout_num - 1, "text")

        dialog = tk.Toplevel(self.window)
        dialog.title("Workout progress")
        dialog.transient(self.window)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        save_header_frame = tk.Frame(dialog)
        save_header_frame.pack(fill='x', padx=5)

        current_workout_name = tk.Label(save_header_frame, text=current_tab_name.upper(),
                                        font=("Helvetica", "12", "bold"))
        current_workout_name.pack(pady=5, anchor='w')

        data_frame = tk.Frame(dialog)
        data_frame.pack(fill='x', padx=5, pady=5)

        butt_frame = tk.Frame(dialog)
        butt_frame.pack(pady=15, fill='x')

        def detailed_stats():
            details_dialog = tk.Toplevel(dialog)
            details_dialog.title("Detailed stats")
            details_dialog.transient(dialog)
            details_dialog.grab_set()

            details_dialog.update_idletasks()
            x = dialog.winfo_x() + (dialog.winfo_width() // 2) - (details_dialog.winfo_width() // 2)
            y = dialog.winfo_y() + (dialog.winfo_height() // 2) - (details_dialog.winfo_height() // 2)
            details_dialog.geometry(f"+{x}+{y}")

            stats_frame = tk.Frame(details_dialog)
            stats_frame.pack(fill='x', padx=5, pady=5)

            def calculate_stats(show_limit):
                for widget in stats_frame.winfo_children():
                    widget.destroy()

                conn = sqlite3.connect('user_data.db')
                cursor = conn.cursor()

                try:
                    cursor.execute('''
                        SELECT DISTINCT date
                        FROM saved_workouts 
                        WHERE user = ? AND workout_number = ?
                        ORDER BY date DESC
                        LIMIT ?
                    ''', (current_user, workout_num, show_limit))

                    dates_to_show = cursor.fetchall()

                    if not dates_to_show:
                        info_label = tk.Label(stats_frame, text='Not enough data', fg='gray')
                        info_label.pack(pady=20)
                        return

                    sorted_dates = sorted([date[0] for date in dates_to_show])
                    workouts_by_date = {}
                    exercises_order = []

                    for date in sorted_dates:
                        cursor.execute('''
                            SELECT exercise_name, weight, repeats, workout_name
                            FROM saved_workouts 
                            WHERE user = ? AND workout_number = ? AND date = ?
                        ''', (current_user, workout_num, date))

                        records = cursor.fetchall()

                        if date not in workouts_by_date:
                            workouts_by_date[date] = {}

                        for exercise_name, weight, repeats_json, workout_name in records:
                            try:
                                repeats = json.loads(repeats_json) if repeats_json else []
                                repeats_str = ', '.join(repeats) if repeats else '-'
                            except:
                                repeats_str = '-'

                            workouts_by_date[date][exercise_name] = {
                                'weight': weight if weight else '-',
                                'repeats': repeats_str
                            }

                            if exercise_name not in exercises_order:
                                exercises_order.append(exercise_name)

                    for col, date in enumerate(sorted_dates, start=1):
                        tk.Label(stats_frame, text=date, font=('Helvetica', '10', 'bold'), bg='lightblue',
                                 relief='ridge', width=12, anchor='center').grid(row=0, column=col,
                                                                                 padx=1, pady=1, sticky='nsew')

                    for row, ex in enumerate(exercises_order, start=1):
                        tk.Label(stats_frame, text=ex, relief='ridge', width=20, anchor='w',
                                 padx=5).grid(row=row, column=0, padx=1, pady=1, sticky='nsew')

                        for col, date in enumerate(sorted_dates, start=1):
                            exercise_data = workouts_by_date.get(date, {}).get(ex)

                            if exercise_data:
                                weight = exercise_data['weight']
                                repeats = exercise_data['repeats']
                                text = f"{weight}\n{repeats}"
                            else:
                                text = '—\n—'

                            tk.Label(stats_frame, text=text, relief='ridge', width=12, anchor='center',
                                     justify='center').grid(row=row, column=col, padx=1, pady=1, sticky='nsew')

                    for col in range(len(sorted_dates) + 1):
                        stats_frame.grid_columnconfigure(col, weight=1)

                except Exception as e:
                    print(f"Error getting workout data: {e}")
                finally:
                    conn.close()

            det_butt_frame = tk.Frame(details_dialog)
            det_butt_frame.pack(side=tk.BOTTOM, pady=5)

            tk.Button(det_butt_frame, text='4 workouts', command=lambda: calculate_stats(4),
                      width=10).pack(side=tk.LEFT, padx=1)

            tk.Button(det_butt_frame, text='8 workouts', command=lambda: calculate_stats(8),
                      width=10).pack(side=tk.LEFT, padx=1)

            tk.Button(det_butt_frame, text='12 workouts', command=lambda: calculate_stats(12),
                      width=10).pack(side=tk.LEFT, padx=1)

            tk.Button(det_butt_frame, text='Close', command=details_dialog.destroy,
                      bg='lightcoral', width=8).pack(side=tk.LEFT, padx=1)

            calculate_stats(4)

        detailed_stats_butt = tk.Button(butt_frame, text='Detailed stats', width=12, command=detailed_stats)
        detailed_stats_butt.pack(side=tk.TOP, pady=2)

        butt_row_one = tk.Frame(butt_frame)
        butt_row_one.pack(side=tk.TOP, pady=2)

        butt_row_two = tk.Frame(butt_frame)
        butt_row_two.pack(side=tk.TOP, pady=2)

        def calculate_progress(time_period=0):
            conn = sqlite3.connect('user_data.db')
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    SELECT MAX(date) as last_date
                    FROM saved_workouts
                    WHERE user = ? AND workout_number = ?
                """, (current_user, workout_num))

                last_workout_date = cursor.fetchone()

                for widget in data_frame.winfo_children():
                    widget.destroy()

                if not last_workout_date or not last_workout_date[0]:
                    info = tk.Label(data_frame)
                    info.config(text="No data found", font=("Helvetica", "10", "bold"), fg='lightcoral')
                    info.pack(side=tk.TOP)

                    conn.close()
                    return []

                last_date = datetime.strptime(last_workout_date[0], "%Y-%m-%d")
                date_limit = last_date - timedelta(days=time_period)
                date_limit_str = date_limit.strftime("%Y-%m-%d")

                cursor.execute('''
                    SELECT exercise_name, weight, repeats, date, workout_name
                    FROM saved_workouts 
                    WHERE user = ? AND workout_number = ? AND date <= ?
                    ORDER BY date DESC
                ''', (current_user, workout_num, date_limit_str))

                first_data = cursor.fetchall()

                if not first_data:
                    conn.close()

                    for widget in data_frame.winfo_children():
                        widget.destroy()

                    info = tk.Label(data_frame)
                    info.config(text="No data found", font=("Helvetica", "10", "bold"), fg='lightcoral')
                    info.pack(side=tk.TOP)
                    return

                cursor.execute('''
                    SELECT exercise_name, weight, repeats, date, workout_name
                    FROM saved_workouts 
                    WHERE user = ? AND workout_number = ?
                    ORDER BY date DESC
                ''', (current_user, workout_num))

                last_data = cursor.fetchall()

                first_result = {}
                for ex_name, weight, repeats_json, date, workout_name in first_data:
                    if ex_name not in first_result:
                        try:
                            repeats = json.loads(repeats_json) if repeats_json else []
                        except:
                            repeats = []
                        first_result[ex_name] = {
                            'workout_name': workout_name,
                            'date': date,
                            'weight': weight,
                            'repeats': repeats
                        }

                last_result = {}
                exercises_order = []
                for ex_name, weight, repeats_json, date, workout_name in last_data:
                    if ex_name not in last_result:
                        try:
                            repeats = json.loads(repeats_json) if repeats_json else []
                        except:
                            repeats = []
                        last_result[ex_name] = {
                            'workout_name': workout_name,
                            'date': date,
                            'weight': weight,
                            'repeats': repeats
                        }
                        exercises_order.append(ex_name)

                print(first_result)
                print(last_result)

                stats_header = tk.Label(data_frame)
                stats_header.config(text=f"{date_limit_str} -> {last_date.strftime("%Y-%m-%d")}",
                                    font=("Helvetica", "10", "bold"))
                stats_header.pack(side=tk.TOP, anchor='w')

                progress_frame = tk.Frame(data_frame, bg='lightgray')
                progress_frame.pack(side=tk.TOP, anchor='w')

                column_widths = [80, 40, 40]
                for col, width in enumerate(column_widths):
                    progress_frame.grid_columnconfigure(col, weight=0, minsize=width)

                row_counter = 0

                if not last_result and not first_result:
                    info_label = tk.Label(data_frame, text="No exercises found", fg='gray')
                    info_label.pack(pady=20)
                else:
                    for ex_name in exercises_order:
                        f_data = first_result.get(ex_name, {})

                        if not f_data:
                            ex_stats = tk.Label(progress_frame, bg='lightgray')
                            ex_stats.config(text=f"Not enough data")
                            ex_stats.grid(column=1, row=row_counter, sticky="ew", padx=2, pady=2)

                        l_data = last_result.get(ex_name, {})

                        f_weight = f_data.get('weight', '')
                        l_weight = l_data.get('weight', '')

                        exercise_name = tk.Label(progress_frame)
                        exercise_name.config(text=f"{ex_name}")
                        exercise_name.grid(column=0, row=row_counter, sticky="w", padx=2, pady=2)

                        if f_weight != 'Self' and l_weight != 'Self':
                            if f_weight == '' or l_weight == '':
                                ex_stats = tk.Label(progress_frame, bg='lightgray')
                                ex_stats.config(text=f"Not enough data")
                                ex_stats.grid(column=1, row=row_counter, sticky="ew", padx=2, pady=2)

                                row_counter += 1
                            else:
                                weight_progress = "{:.1f}".format((float(l_weight) - float(f_weight)) / float(f_weight) * 100)

                                ex_stats = tk.Label(progress_frame, bg='lightgray')
                                ex_stats.config(text=f"{f_weight} -> {l_weight} :")
                                ex_stats.grid(column=1, row=row_counter, sticky="ew", padx=2, pady=2)

                                ex_value = tk.Label(progress_frame, bg='lightgray')

                                if float(weight_progress) > 0:
                                    ex_value.config(text=f"{weight_progress}%", font=("Helvetica", "12", "bold"), fg='green')
                                elif float(weight_progress) == 0:
                                    ex_value.config(text=f"{weight_progress}%", font=("Helvetica", "12", "bold"), fg='gray')
                                else:
                                    ex_value.config(text=f"{weight_progress}%", font=("Helvetica", "12", "bold"), fg='red')

                                ex_value.grid(column=2, row=row_counter, sticky="ew", padx=2, pady=2)

                                row_counter += 1

                                print(f"{ex_name} : progress({f_weight} -> {l_weight}): {weight_progress}%")
                        else:
                            f_reps = first_result[ex_name]['repeats']
                            l_reps = last_result[ex_name]['repeats']
                            f_sum = 0
                            l_sum = 0

                            for rep in f_reps:
                                f_sum += int(rep) if rep.isdigit() else 0

                            for rep in l_reps:
                                l_sum += int(rep) if rep.isdigit() else 0

                            if f_sum == 0 or l_sum == 0:
                                ex_stats = tk.Label(progress_frame, bg='lightgray')
                                ex_stats.config(text=f"Not enough data")
                                ex_stats.grid(column=1, row=row_counter, sticky="ew", padx=2, pady=2)

                                row_counter += 1
                            else:
                                rep_progress = "{:.1f}".format((int(l_sum) - int(f_sum)) / int(f_sum) * 100)

                                ex_stats = tk.Label(progress_frame, bg='lightgray')
                                ex_stats.config(text=f"{'[%s]' % ', '.join(f_reps)}->{'[%s]' % ', '.join(l_reps)}")
                                ex_stats.grid(column=1, row=row_counter, sticky="ew", padx=2, pady=2)

                                ex_value = tk.Label(progress_frame, bg='lightgray')

                                if float(rep_progress) > 0:
                                    ex_value.config(text=f"{rep_progress}%", font=("Helvetica", "12", "bold"), fg='green')
                                elif float(rep_progress) == 0:
                                    ex_value.config(text=f"{rep_progress}%", font=("Helvetica", "12", "bold"), fg='gray')
                                else:
                                    ex_value.config(text=f"{rep_progress}%", font=("Helvetica", "12", "bold"), fg='red')

                                ex_value.config(text=f"{rep_progress}%")
                                ex_value.grid(column=2, row=row_counter, sticky="ew", padx=2, pady=2)

                                row_counter += 1

                                print(f"{ex_name} : progress: {rep_progress}%")

            except Exception as e:
                print(f"Error getting last workout data: {e}")
            finally:
                conn.close()

        calculate_progress(28)

        tk.Button(butt_row_one, text="1 M", command=lambda: calculate_progress(28), width=4).pack(side=tk.LEFT, padx=1)
        tk.Button(butt_row_one, text="2 M", command=lambda: calculate_progress(58), width=4).pack(side=tk.LEFT, padx=1)
        tk.Button(butt_row_one, text="4 M", command=lambda: calculate_progress(120), width=4).pack(side=tk.LEFT, padx=1)
        tk.Button(butt_row_one, text="6 M", command=lambda: calculate_progress(180), width=4).pack(side=tk.LEFT, padx=1)
        tk.Button(butt_row_one, text="8 M", command=lambda: calculate_progress(240), width=4).pack(side=tk.LEFT, padx=1)
        tk.Button(butt_row_two, text="1 Y", command=lambda: calculate_progress(360), width=4).pack(side=tk.LEFT, padx=1)
        tk.Button(butt_row_two, text="18 M", command=lambda: calculate_progress(540), width=4).pack(side=tk.LEFT, padx=1)
        tk.Button(butt_row_two, text="2 Y", command=lambda: calculate_progress(730), width=4).pack(side=tk.LEFT, padx=1)
        tk.Button(butt_row_two, text="Cancel", command=dialog.destroy, bg="lightcoral", width=8).pack(side=tk.LEFT, padx=1)