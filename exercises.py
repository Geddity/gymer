import tkinter as tk


max_rep_entries = 5

class ExerciseRow:
    def __init__(self, parent, row_num, manager, name="New Ex", skip_initial_reps=False,
                 validate_float_func=None, validate_int_func=None, read_insert_func=None,
                 get_current_user_func=None):
        self.parent = parent
        self.row_num = row_num
        self.manager = manager
        self.name = name
        self.widgets = []
        self.rep_entries = []
        self.rep_entry_count = 0
        self.weight_is_label = False

        self.validate_float_func = validate_float_func or (lambda x: True)
        self.validate_int_func = validate_int_func or (lambda x: True)
        self.read_insert_func = read_insert_func or (lambda: '')
        self.get_current_user_func = get_current_user_func or (lambda: '')

        self.create_widgets()

        if not skip_initial_reps:
            self.add_initial_reps()

    def create_widgets(self):
        # name
        self.exercise_name = tk.Label(self.parent, text=self.name, width=22)
        self.exercise_name.grid(row=self.row_num, column=0)
        self.widgets.append(self.exercise_name)

        # weight
        self.weight_frame = tk.Frame(self.parent)
        self.weight_frame.grid(row=self.row_num, column=1)
        self.widgets.append(self.weight_frame)

        self.weight_entry = PlaceholderEntry(self.weight_frame, width=6)
        validate = (self.parent.register(self.validate_float_func), '%P')
        self.weight_entry.config(validate='key', validatecommand=validate)
        self.weight_entry.insert(0, self.read_insert_func())
        self.weight_entry.pack(side=tk.LEFT)

        self.weight_label = tk.Label(self.weight_frame, text="Self", width=5)

        self.weight_toggle = tk.Button(self.weight_frame, text="Change", height=1, command=self.toggle_weight)
        self.weight_toggle.pack(side=tk.RIGHT)

        # rep frame
        self.repeats_frame = tk.Frame(self.parent)
        self.repeats_frame.grid(row=self.row_num, column=2)
        self.widgets.append(self.repeats_frame)

        # butts frame
        self.rep_butts_frame = tk.Frame(self.parent)
        self.rep_butts_frame.grid(row=self.row_num, column=3)
        self.widgets.append(self.rep_butts_frame)

        self.add_rep_butt = tk.Button(self.rep_butts_frame, text="+", width=2, height=1, command=self.add_rep_entry)
        self.add_rep_butt.pack(side=tk.LEFT)

        self.remove_rep_butt = tk.Button(self.rep_butts_frame, text="-", width=2, height=1, command=self.remove_rep_entry)
        self.remove_rep_butt.pack(side=tk.LEFT)

        # ex remove
        self.remove_ex_butt = tk.Button(self.parent, text="X", height=1, width=4, command=self.delete_row)
        self.remove_ex_butt.grid(row=self.row_num, column=4)
        self.widgets.append(self.remove_ex_butt)

    def toggle_weight(self):
        if self.weight_is_label:
            self.weight_label.pack_forget()
            self.weight_entry.pack(side=tk.LEFT)
            self.weight_is_label = False
        else:
            self.weight_entry.pack_forget()
            self.weight_label.pack(side=tk.LEFT)
            self.weight_is_label = True

    def add_initial_reps(self):
        for _ in range(3):
            self.add_rep_entry()

    def add_rep_entry(self):
        if self.rep_entry_count < max_rep_entries:
            new_entry = tk.Entry(self.repeats_frame, width=3)
            validate = (self.parent.register(self.validate_int_func), '%P')
            new_entry.config(validate='key', validatecommand=validate)
            new_entry.insert(0, '')
            new_entry.pack(side=tk.LEFT, padx=1)

            self.rep_entries.append(new_entry)
            self.rep_entry_count += 1
            self.update_butt_state()

    def remove_rep_entry(self):
        if self.rep_entry_count > 1:
            last_entry = self.rep_entries.pop()
            last_entry.destroy()
            self.rep_entry_count -= 1
            self.update_butt_state()

    def update_butt_state(self):
        if self.rep_entry_count >= max_rep_entries:
            self.add_rep_butt.config(state=tk.DISABLED)
        else:
            self.add_rep_butt.config(state=tk.NORMAL)

        if self.rep_entry_count <= 1:
            self.remove_rep_butt.config(state=tk.DISABLED)
        else:
            self.remove_rep_butt.config(state=tk.NORMAL)

    def delete_row(self):
        for widget in self.widgets:
            widget.destroy()
        for entry in self.rep_entries:
            entry.destroy()

        self.manager.remove_row(self)

    def get_data(self):
        if self.weight_is_label:
            weight_value = self.weight_label.cget("text")
        else:
            weight_value = self.weight_entry.get()

        return {
            'user': self.get_current_user_func(),
            'name': self.exercise_name.cget("text"),
            'weight': weight_value,
            'repeats': [entry.get() for entry in self.rep_entries]
        }

class ExerciseManager:
    def __init__(self, parent, validate_float_func=None, validate_int_func=None,
                 read_insert_func=None, get_current_user_func=None):
        self.parent = parent
        self.rows = []
        self.next_row = 1

        self.validate_float_func = validate_float_func or (lambda x: True)
        self.validate_int_func = validate_int_func or (lambda x: True)
        self.read_insert_func = read_insert_func or (lambda: '')
        self.get_current_user_func = get_current_user_func or (lambda: '')

        self.create_headers()

    def create_headers(self):
        headers = ["Exercise", "Weight", "Repeats", "Controls", "Del"]
        column_widths = [170, 100, 130, 60, 40]

        for col, text in enumerate(headers):
            cell_frame = tk.Frame(self.parent, width=column_widths[col], height=30, relief='groove', bd=2)
            cell_frame.grid(row=0, column=col)
            cell_frame.grid_propagate(False)

            label = tk.Label(cell_frame, text=text, bg="lightblue")
            label.place(relwidth=1, relheight=1)

    def add_row(self, name=None, skip_initial_reps=False):
        if name is None:
            name = f"Exercise {len(self.rows) + 1}"

        row = ExerciseRow(self.parent, self.next_row, self, name, skip_initial_reps,
                          self.validate_float_func, self.validate_int_func,
                          self.read_insert_func, self.get_current_user_func)
        self.rows.append(row)
        self.next_row += 1
        self.reorganize_rows()
        return row

    def remove_row(self, row):
        if row in self.rows:
            self.rows.remove(row)
            self.reorganize_rows()

    def reorganize_rows(self):
        for i, row in enumerate(self.rows):
            new_row = i + 1
            row.row_num = new_row

            row.exercise_name.grid(row=new_row, column=0)
            row.weight_frame.grid(row=new_row, column=1)
            row.repeats_frame.grid(row=new_row, column=2)
            row.rep_butts_frame.grid(row=new_row, column=3)
            row.remove_ex_butt.grid(row=new_row, column=4)

        self.next_row = len(self.rows) + 1

    def delete_all_rows(self):
        for row in self.rows:
            for widget in row.widgets:
                widget.destroy()
            for entry in row.rep_entries:
                entry.destroy()
        self.rows.clear()
        self.next_row = 1

    def get_all_data(self):
        return [row.get_data() for row in self.rows]

class PlaceholderEntry(tk.Entry):
    def __init__(self, master=None, placeholder='', placeholder_color='gray', text_color='black', **kwargs):
        super().__init__(master, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.text_color = text_color
        self.has_placeholder = True

        self.insert(0, self.placeholder)
        self.config(fg=self.placeholder_color)

        self.bind('<FocusIn>', self.on_focus_in)
        self.bind('<FocusOut>', self.on_focus_out)

    def on_focus_in(self, event):
        if self.has_placeholder:
            self.delete(0, tk.END)
            self.config(fg=self.text_color)
            self.has_placeholder = False

    def on_focus_out(self, event):
        if self.get() == '':
            self.insert(0, self.placeholder)
            self.config(fg=self.placeholder_color)
            self.has_placeholder = True

    def get(self):
        if self.has_placeholder:
            return ''
        return super().get()

    def set_placeholder(self, text):
        self.placeholder = text
        if self.has_placeholder:
            self.delete(0, tk.END)
            self.insert(0, text)