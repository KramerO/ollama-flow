#!/usr/bin/env python3
import sqlite3

def create_calculation_table():
    conn = sqlite3.connect('calculations.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS calculations
                 (id INTEGER PRIMARY KEY, operation TEXT, result REAL)''')
    conn.commit()
    conn.close()

def insert_calculation(operation, result):
    conn = sqlite3.connect('calculations.db')
    c = conn.cursor()
    c.execute("INSERT INTO calculations VALUES (NULL, ?, ?)", (operation, result))
    conn.commit()
    conn.close()

def main():
    create_calculation_table()
    # Add your main logic here
    
if __name__ == "__main__":
    main()
