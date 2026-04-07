import tkinter as tk
from tkinter import ttk


from exercises import ExerciseManager
from debugs import open_debug_window
from workouts import WorkoutManager
from presets import PresetManager
from users import UserManager

#######################################################################################################################
                                            #GLOBALS
#######################################################################################################################

max_rep_entries = 5
workout_frames = {}
workout_names = {}
workout_managers = {}

import exercises
exercises.max_rep_entries = max_rep_entries

#######################################################################################################################
                                            #COMMON
#######################################################################################################################

def hide_frame():
    toggle_frame.pack_forget()
    top_frame.config(height=1)
    change_butt.config(state=tk.NORMAL)

def show_frame():
    toggle_frame.pack(side=tk.TOP, padx=10, pady=10)
    change_butt.config(state=tk.DISABLED)

def read_insert():
    return ''

def limit_input_length(input_text, input_length=0):
    if len(input_text) > input_length:
        return False
    return True

def validate_int_input(value):
    if value == '':
        return True
    if value.isdigit() and int(value) <= 999:
        return True
    return False

def validate_float_input(value):
    if value == '':
        return True

    try:
        num = float(value)

        if '.' in value:
            decimals = len(value.split('.')[1])
            if decimals > 2:
                return False
        if num < 0 or num > 999:
            return False

        return True
    except ValueError:
        return False

def create_placeholder(parent, text, width=4):
    entry = tk.Entry(parent, width=width, fg='gray')
    entry.insert(0, text)

    def on_focus_in(event):
        if entry.get() == text:
            entry.delete(0, tk.END)
            entry.config(fg='black')

    def on_focus_out(event):
        if entry.get() == '':
            entry.insert(0, text)
            entry.config(fg='gray')

    entry.bind('<FocusIn>', on_focus_in)
    entry.bind('<FocusOut>', on_focus_out)

    return entry

def update_header_label(user):
    header_label.config(text=f"Current user: {user}")

#######################################################################################################################
                                            #WINDOW
#######################################################################################################################

window = tk.Tk()
window.title('Gymer')
window.minsize(520, 500)
window.resizable(False, True)


# header
header_frame = tk.Frame(window, bg="gray")
header_frame.pack(side=tk.TOP, fill="x")

header_label = tk.Label(header_frame, text=f"Current User: ", anchor="w")
header_label.pack(side=tk.LEFT)

change_butt = tk.Button(header_frame, text="Change User", anchor="e", height=1, command=show_frame)
change_butt.pack(side=tk.RIGHT)
change_butt.config(state=tk.DISABLED)


# login frame
top_frame = tk.Frame(window)
top_frame.pack(side=tk.TOP)

toggle_frame = tk.Frame(top_frame)
toggle_frame.pack(side=tk.TOP, padx=10, pady=10)

    # chose user row
chose_row = tk.Frame(toggle_frame)
chose_row.pack(side=tk.TOP)

user_chose_label = tk.Label(chose_row, text="Chose User:")
user_chose_label.pack(side=tk.LEFT)

user_chose_box = ttk.Combobox(chose_row, state="readonly", width=10)
user_chose_box.pack(side=tk.LEFT, padx=5)

chose_butt = tk.Button(chose_row, text="Chose", width=10, height=1)
chose_butt.pack(side=tk.LEFT)

delete_butt = tk.Button(chose_row, text='Delete', width=10, height=1)
delete_butt.pack(side=tk.LEFT)

    # create user row
create_row = tk.Frame(toggle_frame)
create_row.pack(side=tk.TOP, pady=10)

new_user_entry = tk.Entry(create_row, width=15)
new_user_entry.insert(0, read_insert())
new_user_entry.pack(side=tk.LEFT, padx=5)

create_butt = tk.Button(create_row, text="Create New", width=10, height=1)
create_butt.pack(side=tk.LEFT)


# body frame
body_frame = tk.Frame(window, width=200, height=150, bg="lightgray")
body_frame.pack(side=tk.TOP, fill="x")

body_upper_frame = tk.Frame(body_frame)
body_upper_frame.pack(side=tk.TOP, padx=5, pady=10)

body_mid_frame = tk.Frame(body_frame, bg="lightgray")
body_mid_frame.pack(side=tk.TOP, padx=5, fill="x")

body_lower_frame = tk.Frame(body_frame)
body_lower_frame.pack(side=tk.TOP, padx=5, pady=10)


# workouts
workout_tab = ttk.Notebook(body_mid_frame)
style = ttk.Style()
style.configure('TNotebook', background="lightgray")
workout_tab.pack(side=tk.TOP, pady=5)

# tab lower butts
vcmd = body_lower_frame.register(lambda text: limit_input_length(text, 21))

new_ex_entry = tk.Entry(body_lower_frame, validate='key', validatecommand=(vcmd, "%P"), width=28)
new_ex_entry.insert(0, read_insert())
new_ex_entry.pack(side=tk.LEFT, padx=5)

add_ex_butt = tk.Button(body_lower_frame, text="Add Exercise", width=10, height=1,
                        command=lambda: workout_manager.add_exercise_to_current_tab(new_ex_entry))
add_ex_butt.pack(side=tk.LEFT)


# footer butts
footer_frame = tk.Frame(window)
footer_frame.pack(side=tk.BOTTOM, pady=5)

status_label = tk.Label(footer_frame, text="", fg="green")
status_label.pack(side=tk.TOP, pady=5)

f_row_one = tk.Frame(footer_frame)
f_row_one.pack(side=tk.TOP)

f_row_two = tk.Frame(footer_frame)
f_row_two.pack(side=tk.TOP)


#managers
user_manager = UserManager(
    header_label=header_label,
    status_label=status_label,
    window=window,
    hide_frame_func=hide_frame,
    show_frame_func=show_frame,
    read_insert_func=read_insert,
    change_butt=change_butt,
    top_frame=top_frame,
    toggle_frame=toggle_frame,
    user_chose_box=user_chose_box,
    new_user_entry=new_user_entry,
    chose_butt=chose_butt,
    create_butt=create_butt
)

chose_butt.config(command=user_manager.chose_user)
delete_butt.config(command=lambda: user_manager.delete_user())
create_butt.config(command=user_manager.create_new_user)

user_manager.init_database()
user_manager.user_chose_box.config(values=user_manager.extract_users())

workout_manager = WorkoutManager(
    workout_tab=workout_tab,
    workout_managers=workout_managers,
    workout_names=workout_names,
    ExerciseManager=ExerciseManager,
    validate_float_func=validate_float_input,
    validate_int_func=validate_int_input,
    read_insert_func=read_insert,
    get_current_user_func=user_manager.get_current_user,
    status_label=status_label,
    window=window
)

preset_manager = PresetManager(
    workout_managers=workout_managers,
    workout_names=workout_names,
    workout_tab=workout_tab,
    add_workout_tab_func=workout_manager.add_workout_tab,
    ExerciseManager=ExerciseManager,
    validate_float_func=validate_float_input,
    validate_int_func=validate_int_input,
    read_insert_func=read_insert,
    get_current_user_func=user_manager.get_current_user,
    get_last_workout_data_func=workout_manager.get_last_workout_data,
    save_last_user_func=user_manager.save_last_user,
    hide_frame_func=hide_frame,
    update_header_label_func=update_header_label,
    set_current_user_func=user_manager.set_current_user,
    set_last_preset_func=user_manager.set_last_preset,
    status_label=status_label,
    window=window
)


#workout_butts
add_workout_butt = tk.Button(body_upper_frame, text="Add Workout Tab",
                             width=14, height=1, command=workout_manager.add_new_workout_tab)
add_workout_butt.pack(side=tk.LEFT)

remove_workout_butt = tk.Button(body_upper_frame, text="Remove Workout Tab",
                                width=17, height=1, command=workout_manager.remove_workout_tab)
remove_workout_butt.pack(side=tk.LEFT)

workout_tab.bind("<Double-Button-1>", workout_manager.rename_workout_tab)

workout_manager.add_workout_tab(1)
workout_manager.add_workout_tab(2)


show_stats_butt = tk.Button(f_row_one, text="Show Stats", height=1,
                            command=workout_manager.get_workout_progress)
show_stats_butt.pack(side=tk.LEFT)

save_workout_butt = tk.Button(f_row_one, text="Save Workout", height=1,
                              command=workout_manager.save_current_workout_data)
save_workout_butt.pack(side=tk.LEFT)

delete_workout_butt = tk.Button(f_row_one, text="Delete Workout", height=1,
                                command=workout_manager.delete_specific_workout)
delete_workout_butt.pack(side=tk.LEFT)


#preset_butts
save_preset_butt = tk.Button(f_row_two, text="Save Preset", height=1, command=preset_manager.save_preset)
save_preset_butt.pack(side=tk.LEFT)

load_preset_butt = tk.Button(f_row_two, text="Load Preset", height=1, command=preset_manager.load_preset)
load_preset_butt.pack(side=tk.LEFT)

delete_preset_butt = tk.Button(f_row_two, text="Delete Preset", height=1, command=preset_manager.delete_preset)
delete_preset_butt.pack(side=tk.LEFT)

debug_butt = tk.Button(f_row_two, text="Debug", height=1,
                       command=lambda: open_debug_window(window, workout_tab, user_manager.get_current_user))
debug_butt.pack(side=tk.LEFT)


preset_manager.auto_load_last_preset()

window.mainloop()
