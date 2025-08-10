#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk

class UserInterfaceDesign:
    def __init__(self, root):
        self.root = root
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        numerical_input_label = ttk.Label(main_frame, text="Numerical Input:")
        numerical_input_label.pack()
        numerical_input_entry = tk.Entry(main_frame)
        numerical_input_entry.pack()

        operator_selection_label = ttk.Label(main_frame, text="Operator Selection:")
        operator_selection_label.pack()
        operator_selection_var = tk.StringVar()
        operator_selection_var.set("Choose an Operator")  # default value
        operator_selection_menu = tk.OptionMenu(main_frame, operator_selection_var, "Add", "Subtract", "Multiply", "Divide")
        operator_selection_menu.pack()

        submit_button = ttk.Button(main_frame, text="Submit", command=lambda: self.process_input())
        submit_button.pack()

    def process_input(self):
        numerical_input = int(numerical_input_entry.get())
        operator = operator_selection_var.get()
        if operator == "Add":
            result = numerical_input + 5
        elif operator == "Subtract":
            result = numerical_input - 3
        elif operator == "Multiply":
            result = numerical_input * 2
        elif operator == "Divide":
            result = numerical_input / 4

        result_label = ttk.Label(self.root, text=f"Result: {result}")
        result_label.pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = UserInterfaceDesign(root)
    root.mainloop()
