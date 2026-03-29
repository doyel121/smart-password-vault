# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import hashlib
import re
from cryptography.fernet import Fernet

# ---------------- DATABASE ---------------- #
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS vault (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    website TEXT,
    username TEXT,
    password TEXT
)
""")

conn.commit()

# ---------------- ENCRYPTION ---------------- #
def load_key():
    try:
        with open("key.key", "rb") as f:
            return f.read()
    except:
        key = Fernet.generate_key()
        with open("key.key", "wb") as f:
            f.write(key)
        return key

key = load_key()
cipher = Fernet(key)

# ---------------- BREACH ---------------- #
common_passwords = [
    "123456", "password", "123456789", "admin", "qwerty",
    "abc123", "111111", "123123", "password123"
]

def check_breach(password):
    return password.strip().lower() in common_passwords

# ---------------- PASSWORD STRENGTH ---------------- #
def check_strength(password):
    score = 0
    if len(password) >= 6: score += 1
    if re.search(r"[A-Za-z]", password): score += 1
    if re.search(r"[0-9]", password): score += 1
    if re.search(r"[^\w\s]", password): score += 1
    return score

def is_strong_password(password):
    return check_strength(password) >= 3

# ---------------- SECURITY ---------------- #
def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# ---------------- REGISTER ---------------- #
def register():
    username = entry_username.get()
    password = entry_password.get().strip()

    if not username or not password:
        messagebox.showerror("Error", "All fields required")
        return

    if check_breach(password):
        messagebox.showerror("Weak Password", "❌ Common password not allowed")
        return

    if not is_strong_password(password):
        messagebox.showerror("Weak Password", "❌ Password too weak")
        return

    hashed = hash_password(password)

    cursor.execute("INSERT INTO users VALUES (NULL, ?, ?)", (username, hashed))
    conn.commit()

    messagebox.showinfo("Success", "User registered!")

# ---------------- LOGIN ---------------- #
def login():
    username = entry_username.get()
    password = entry_password.get()

    hashed = hash_password(password)

    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed))
    result = cursor.fetchone()

    if result:
        messagebox.showinfo("Success", "Login successful!")
        open_vault()
    else:
        messagebox.showerror("Error", "Invalid credentials")

# ---------------- VAULT ---------------- #
def open_vault():
    vault_window = tk.Toplevel(root)
    vault_window.title("🔐 Password Vault")
    vault_window.geometry("500x450")
    vault_window.configure(bg="#1e1e2f")

    tk.Label(vault_window, text="Website", bg="#1e1e2f", fg="white").pack(pady=5)
    entry_site = tk.Entry(vault_window, font=("Arial", 12))
    entry_site.pack(pady=5)

    tk.Label(vault_window, text="Username", bg="#1e1e2f", fg="white").pack(pady=5)
    entry_user = tk.Entry(vault_window, font=("Arial", 12))
    entry_user.pack(pady=5)

    tk.Label(vault_window, text="Password", bg="#1e1e2f", fg="white").pack(pady=5)
    entry_pass = tk.Entry(vault_window, show="*", font=("Arial", 12))
    entry_pass.pack(pady=5)

    strength_label = tk.Label(vault_window, text="", bg="#1e1e2f", fg="white")
    strength_label.pack()

    def update_strength(event):
        pwd = entry_pass.get()
        score = check_strength(pwd)

        if score <= 1:
            strength_label.config(text="Weak ❌", fg="red")
        elif score <= 3:
            strength_label.config(text="Medium ⚠️", fg="orange")
        else:
            strength_label.config(text="Strong ✅", fg="green")

    entry_pass.bind("<KeyRelease>", update_strength)

    def add_password():
        site = entry_site.get()
        user = entry_user.get()
        pwd = entry_pass.get().strip()

        if not site or not user or not pwd:
            messagebox.showerror("Error", "All fields required")
            return

        if check_breach(pwd):
            messagebox.showerror("Weak Password", "❌ Common password not allowed")
            return

        if not is_strong_password(pwd):
            messagebox.showerror("Weak Password", "❌ Password too weak")
            return

        encrypted_pwd = cipher.encrypt(pwd.encode()).decode()
        print("🔐 Encrypted:", encrypted_pwd)

        cursor.execute("INSERT INTO vault VALUES (NULL, ?, ?, ?)", (site, user, encrypted_pwd))
        conn.commit()

        messagebox.showinfo("Success", "Password saved!")

    def view_passwords():
        view_win = tk.Toplevel(vault_window)
        view_win.title("🔐 Stored Passwords")
        view_win.geometry("600x350")

        tree = ttk.Treeview(view_win, columns=("Website", "Username", "Password"), show="headings")

        tree.heading("Website", text="Website")
        tree.heading("Username", text="Username")
        tree.heading("Password", text="Password")

        tree.column("Website", width=180)
        tree.column("Username", width=150)
        tree.column("Password", width=220)

        scrollbar = tk.Scrollbar(view_win)
        scrollbar.pack(side="right", fill="y")

        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.config(command=tree.yview)

        tree.pack(fill="both", expand=True)

        cursor.execute("SELECT * FROM vault")
        records = cursor.fetchall()

        for r in records:
            try:
                decrypted = cipher.decrypt(r[3].encode()).decode()
            except:
                decrypted = "Error"

            tree.insert("", "end", values=(r[1], r[2], decrypted))

    tk.Button(vault_window, text="Add Password", command=add_password,
              bg="#4CAF50", fg="white").pack(pady=10)

    tk.Button(vault_window, text="View Passwords", command=view_passwords,
              bg="#2196F3", fg="white").pack()

# ---------------- MAIN UI ---------------- #
root = tk.Tk()
root.title("🔐 Smart Password Vault")
root.geometry("350x300")
root.configure(bg="#1e1e2f")

tk.Label(root, text="Username", bg="#1e1e2f", fg="white").pack(pady=5)
entry_username = tk.Entry(root, font=("Arial", 12))
entry_username.pack(pady=5)

tk.Label(root, text="Password", bg="#1e1e2f", fg="white").pack(pady=5)
entry_password = tk.Entry(root, show="*", font=("Arial", 12))
entry_password.pack(pady=5)

strength_label_main = tk.Label(root, text="", bg="#1e1e2f", fg="white")
strength_label_main.pack()

def update_strength_main(event):
    pwd = entry_password.get()
    score = check_strength(pwd)

    if score <= 1:
        strength_label_main.config(text="Weak ❌", fg="red")
    elif score <= 3:
        strength_label_main.config(text="Medium ⚠️", fg="orange")
    else:
        strength_label_main.config(text="Strong ✅", fg="green")

entry_password.bind("<KeyRelease>", update_strength_main)

tk.Button(root, text="Register", command=register,
          bg="#4CAF50", fg="white").pack(pady=10)

tk.Button(root, text="Login", command=login,
          bg="#2196F3", fg="white").pack()

root.mainloop()