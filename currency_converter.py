import json
import os
import urllib.request
import urllib.error
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

DATA_FILE = "history.json"
API_KEY = "7869888e6d99bfd3c187500c"
API_URL = f"https://v6.exchangerate-api.com/v6/7869888de6d99bfd3c187500c/latest/USD"

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Конвертер валют")
        self.root.geometry("900x650")

        self.history = []
        self.load_history()
        self.currencies = []
        self.exchange_rates = {}

        # Загрузка списка валют и курсов
        self.load_currencies()

        # Рамка для конвертации
        converter_frame = tk.LabelFrame(root, text="Конвертация валют", padx=10, pady=10, font=("Arial", 10, "bold"))
        converter_frame.pack(fill="x", padx=10, pady=5)

        # Сумма
        tk.Label(converter_frame, text="Сумма:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.amount_entry = tk.Entry(converter_frame, width=15, font=("Arial", 12))
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)

        # Из какой валюты
        tk.Label(converter_frame, text="Из валюты:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.from_currency_var = tk.StringVar()
        self.from_currency_combo = ttk.Combobox(converter_frame, textvariable=self.from_currency_var, values=self.currencies, width=10)
        self.from_currency_combo.grid(row=0, column=3, padx=5, pady=5)
        if self.currencies:
            self.from_currency_combo.current(0)

        # В какую валюту
        tk.Label(converter_frame, text="В валюту:").grid(row=0, column=4, sticky="w", padx=5, pady=5)
        self.to_currency_var = tk.StringVar()
        self.to_currency_combo = ttk.Combobox(converter_frame, textvariable=self.to_currency_var, values=self.currencies, width=10)
        self.to_currency_combo.grid(row=0, column=5, padx=5, pady=5)
        if len(self.currencies) > 1:
            self.to_currency_combo.current(1)

        # Результат
        self.result_label = tk.Label(converter_frame, text="Результат: 0.00", font=("Arial", 12, "bold"), fg="blue")
        self.result_label.grid(row=0, column=6, padx=10, pady=5)

        # Кнопка конвертации
        self.convert_btn = tk.Button(converter_frame, text="Конвертировать", command=self.convert, bg="green", fg="white", font=("Arial", 10, "bold"))
        self.convert_btn.grid(row=0, column=7, padx=10, pady=5)

        # Рамка для обновления курсов
        update_frame = tk.Frame(root)
        update_frame.pack(fill="x", padx=10, pady=5)
        self.update_btn = tk.Button(update_frame, text="Обновить курсы валют", command=self.load_currencies, bg="orange", fg="white")
        self.update_btn.pack(side="left", padx=5)

        self.last_update_label = tk.Label(update_frame, text="", font=("Arial", 9))
        self.last_update_label.pack(side="left", padx=10)

        # Рамка истории
        history_frame = tk.LabelFrame(root, text="История конвертаций", padx=10, pady=10, font=("Arial", 10, "bold"))
        history_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Таблица истории
        columns = ("ID", "Date", "Amount", "From", "To", "Result", "Rate")
        self.tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=12)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Date", text="Дата и время")
        self.tree.heading("Amount", text="Сумма")
        self.tree.heading("From", text="Из")
        self.tree.heading("To", text="В")
        self.tree.heading("Result", text="Результат")
        self.tree.heading("Rate", text="Курс")

        self.tree.column("ID", width=40)
        self.tree.column("Date", width=140)
        self.tree.column("Amount", width=80)
        self.tree.column("From", width=60)
        self.tree.column("To", width=60)
        self.tree.column("Result", width=100)
        self.tree.column("Rate", width=80)

        self.tree.pack(fill="both", expand=True)

        # Скроллбар
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Кнопки управления историей
        buttons_frame = tk.Frame(root)
        buttons_frame.pack(fill="x", padx=10, pady=5)

        self.clear_history_btn = tk.Button(buttons_frame, text="Очистить историю", command=self.clear_history, bg="red", fg="white")
        self.clear_history_btn.pack(side="left", padx=5)

        self.export_btn = tk.Button(buttons_frame, text="Экспорт истории", command=self.export_history, bg="purple", fg="white")
        self.export_btn.pack(side="left", padx=5)

        self.refresh_history()

    def load_currencies(self):
        """Загрузка списка валют и курсов из API"""
        if API_KEY == "YOUR_API_KEY_HERE":
            messagebox.showwarning("Нет API-ключа",
                                 "Пожалуйста, получите API-ключ на https://app.exchangerate-api.com/sign-up\n"
                                 "и вставьте его в код в переменную API_KEY")
            # Демо-режим с базовыми валютами
            self.currencies = ["USD", "EUR", "RUB", "GBP", "JPY", "CNY", "UAH", "KZT"]
            self.exchange_rates = {"USD": 1.0, "EUR": 0.92, "RUB": 92.5, "GBP": 0.79,
                                   "JPY": 151.2, "CNY": 7.24, "UAH": 39.5, "KZT": 446.0}
            self.last_update_label.config(text="Последнее обновление: демо-режим (без API)", fg="red")
            self.update_currency_lists()
            return

        try:
            # Получаем курсы относительно USD
            url = API_URL + "USD"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())

                if data.get("result") == "success":
                    self.exchange_rates = data["conversion_rates"]
                    self.currencies = sorted(self.exchange_rates.keys())
                    self.update_currency_lists()
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.last_update_label.config(text=f"Последнее обновление: {now}", fg="green")
                    messagebox.showinfo("Успех", f"Загружено {len(self.currencies)} валют")
                else:
                    messagebox.showerror("Ошибка API", f"API вернул ошибку: {data.get('error-type', 'Неизвестная ошибка')}")
                    self.use_demo_data()
        except urllib.error.URLError as e:
            messagebox.showerror("Ошибка сети", f"Не удалось подключиться к API.\n{e.reason}\nИспользуются демо-данные.")
            self.use_demo_data()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}\nИспользуются демо-данные.")
            self.use_demo_data()

    def use_demo_data(self):
        """Использование демо-данных при недоступности API"""
        self.currencies = ["USD", "EUR", "RUB", "GBP", "JPY", "CNY", "UAH", "KZT"]
        self.exchange_rates = {"USD": 1.0, "EUR": 0.92, "RUB": 92.5, "GBP": 0.79,
                               "JPY": 151.2, "CNY": 7.24, "UAH": 39.5, "KZT": 446.0}
        self.last_update_label.config(text="Демо-режим (API недоступен)", fg="red")
        self.update_currency_lists()

    def update_currency_lists(self):
        """Обновление выпадающих списков валют"""
        self.from_currency_combo['values'] = self.currencies
        self.to_currency_combo['values'] = self.currencies
        if self.from_currency_var.get() not in self.currencies:
            self.from_currency_var.set("USD" if "USD" in self.currencies else self.currencies[0])
        if self.to_currency_var.get() not in self.currencies:
            self.to_currency_var.set("EUR" if "EUR" in self.currencies else self.currencies[1] if len(self.currencies) > 1 else self.currencies[0])

    def convert(self):
        """Конвертация валюты"""
        # Проверка суммы
        try:
            amount = float(self.amount_entry.get().strip())
            if amount <= 0:
                raise ValueError("Сумма должна быть положительной")
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Сумма должна быть положительным числом.\nПример: 100, 50.75")
            return

        # Проверка валют
        from_currency = self.from_currency_var.get()
        to_currency = self.to_currency_var.get()

        if not from_currency or not to_currency:
            messagebox.showerror("Ошибка", "Выберите валюты для конвертации.")
            return

        if from_currency == to_currency:
            result = amount
            rate = 1.0
            result_text = f"{result:.2f}"
        else:
            try:
                # Получаем курс: сначала переводим в USD, затем в целевую валюту
                if from_currency == "USD":
                    rate = self.exchange_rates.get(to_currency, 1)
                    result = amount * rate
                elif to_currency == "USD":
                    rate = 1 / self.exchange_rates.get(from_currency, 1)
                    result = amount * rate
                else:
                    # Конвертация через USD
                    rate_in_usd = self.exchange_rates.get(from_currency, 1)
                    rate_out_usd = self.exchange_rates.get(to_currency, 1)
                    rate = rate_out_usd / rate_in_usd
                    result = amount * rate

                result_text = f"{result:.2f}"
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при конвертации: {str(e)}")
                return

        # Отображение результата
        self.result_label.config(text=f"Результат: {result_text} {to_currency}")

        # Сохранение в историю
        history_entry = {
            "id": max([h["id"] for h in self.history], default=0) + 1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "result": float(result),
            "rate": round(rate, 6)
        }
        self.history.append(history_entry)
        self.save_history()
        self.refresh_history()

        # Очистка поля ввода
        self.amount_entry.delete(0, tk.END)

    def refresh_history(self):
        """Обновление таблицы истории"""
        for row in self.tree.get_children():
            self.tree.delete(row)

        for entry in reversed(self.history[-50:]):  # Показываем последние 50 записей
            self.tree.insert("", tk.END, values=(
                entry["id"],
                entry["timestamp"],
                f"{entry['amount']:.2f}",
                entry["from_currency"],
                entry["to_currency"],
                f"{entry['result']:.2f}",
                entry["rate"]
            ))

    def clear_history(self):
        """Очистка всей истории"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить всю историю?"):
            self.history = []
            self.save_history()
            self.refresh_history()
            messagebox.showinfo("Успех", "История очищена.")

    def export_history(self):
        """Экспорт истории в отдельный JSON-файл"""
        if not self.history:
            messagebox.showwarning("Нет данных", "История пуста. Нечего экспортировать.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"history_export_{timestamp}.json"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Успех", f"История экспортирована в файл:\n{filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать историю:\n{str(e)}")

    def save_history(self):
        """Сохранение истории в JSON"""
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def load_history(self):
        """Загрузка истории из JSON"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.history = []

if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()
