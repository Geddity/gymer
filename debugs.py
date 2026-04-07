import tkinter as tk
import sqlite3


def open_debug_window(window, workout_tab, current_user_func):
    dialog = tk.Toplevel(window)
    dialog.title("Debug window")
    dialog.geometry("300x50")
    dialog.transient(window)
    dialog.grab_set()

    dialog.update_idletasks()
    x = window.winfo_x() + (window.winfo_width() // 2) - (dialog.winfo_width() // 2)
    y = window.winfo_y() + (window.winfo_height() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")

    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text='Tables', command=lambda: debug_all_tables()).pack(side=tk.LEFT, padx=1)
    tk.Button(btn_frame, text='Users', command=lambda: debug_saved_users()).pack(side=tk.LEFT, padx=1)
    tk.Button(btn_frame, text='Workouts',
              command=lambda: debug_saved_workouts(workout_tab, current_user_func)).pack(side=tk.LEFT, padx=1)
    tk.Button(btn_frame, text='Presets',
              command=lambda: debug_saved_presets(current_user_func)).pack(side=tk.LEFT, padx=1)
    tk.Button(btn_frame, text='Cancel', command=dialog.destroy).pack(side=tk.LEFT, padx=1)

def debug_saved_workouts(workout_tab, current_user_func):
    current_user = current_user_func()
    workout_num = workout_tab.index(workout_tab.select()) + 1

    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()

    print("=" * 60)
    print(f"DEBUG: saved_workouts for workout #{workout_num}, user: {current_user}")
    print("=" * 60)

    cursor.execute("PRAGMA table_info(saved_workouts)")
    columns = cursor.fetchall()
    print("Table structure:")
    for col in columns:
        print(f"  {col[1]} - {col[2]}")

    cursor.execute("""
        SELECT * FROM saved_workouts 
        WHERE user = ? AND workout_number = ?
        ORDER BY date DESC
        LIMIT 10
    """, (current_user, workout_num))

    records = cursor.fetchall()
    print(f"\nLast {len(records)} records:")

    for i, record in enumerate(records):
        print(f"\nRecord {i + 1}:")
        for j, col in enumerate(columns):
            print(f"  {col[1]}: {record[j]}")

    conn.close()

def debug_saved_presets(current_user_func):
    current_user = current_user_func()

    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()

    print("=" * 60)
    print(f"DEBUG: saved_presets for user: {current_user}")
    print("=" * 60)

    cursor.execute("PRAGMA table_info(presets)")
    columns = cursor.fetchall()
    print("Table structure:")
    for col in columns:
        print(f"  {col[1]} - {col[2]}")

    cursor.execute("""
        SELECT * FROM presets 
        WHERE user = ?
        ORDER BY updated_date DESC
        LIMIT 10
    """, (current_user,))

    records = cursor.fetchall()
    print(f"\nLast {len(records)} records:")

    for i, record in enumerate(records):
        preset_id = record[0]
        preset_name = record[1]
        user = record[2]
        updated_date = record[3]

        print(f"\n{'=' * 50}")
        print(f"PRESET #{i + 1}:")
        print(f"  ID: {preset_id}")
        print(f"  Name: {preset_name}")
        print(f"  User: {user}")
        print(f"  Updated: {updated_date}")

        cursor.execute("""
            SELECT workout_number, workout_name, exercise_name, weight_mode
            FROM workout_data
            WHERE preset_id = ?
            ORDER BY workout_number
        """, (preset_id,))

        workout_data = cursor.fetchall()

        if workout_data:
            print(f"  Workouts in preset: {len(set(w[0] for w in workout_data))}")

            workouts_summary = {}
            for w_num, w_name, ex_name, w_mode in workout_data:
                if w_num not in workouts_summary:
                    workouts_summary[w_num] = {
                        'name': w_name,
                        'exercises': []
                    }
                workouts_summary[w_num]['exercises'].append([ex_name, w_mode])

            for w_num in sorted(workouts_summary.keys()):
                workout_info = workouts_summary[w_num]
                print(f"\n  Workout #{w_num}: '{workout_info['name']}'")
                print(f"    Exercises ({len(workout_info['exercises'])}):")
                for ex in workout_info['exercises']:
                    print(f"      - {ex[0]}: {ex[1]}")
        else:
            print("  No workout data found for this preset")

    conn.close()

def debug_saved_users():
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()

    print("=" * 60)
    print("DEBUG: saved_users")
    print("=" * 60)

    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print("Table structure:")
    for col in columns:
        print(f"  {col[1]} - {col[2]}")

    cursor.execute("""
        SELECT * FROM users 
        ORDER BY id DESC
        LIMIT 10
    """)

    records = cursor.fetchall()
    print(f"\nLast {len(records)} records:")

    for i, record in enumerate(records):
        print(f"\nRecord {i + 1}:")
        for j, col in enumerate(columns):
            print(f"  {col[1]}: {record[j]}")

    conn.close()


def debug_all_tables():
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print("=" * 60)
    print("DEBUG: ALL TABLES IN DATABASE")
    print("=" * 60)

    for table in tables:
        table_name = table[0]
        print(f"\n--- TABLE: {table_name} ---")

        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        print("Columns:")
        for col in columns:
            print(f"  {col[1]} - {col[2]}")

        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"Row count: {count}")

    conn.close()