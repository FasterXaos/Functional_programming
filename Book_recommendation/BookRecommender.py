import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    with open("books.json", "r", encoding="utf-8") as file:
        books = json.load(file)
except FileNotFoundError:
    books = []
    messagebox.showerror("Ошибка", "Файл books.json не найден.")

def calculateScore(book, genres, authors, keywords):
    score = 0

    if book["genre"].lower() in genres:
        score += 3

    for author in book["author"]:
        if author.lower() in authors:
            score += 2

    for keyword in keywords:
        if keyword.lower() in book["description"].lower():
            score += 1

    return score

def recommendBooks(genres, authors, keywords, yearFilter, sortBy):
    genres = [genre.strip().lower() for genre in genres.split(",") if genre.strip()]
    authors = [author.strip().lower() for author in authors.split(",") if author.strip()]
    keywords = [keyword.strip().lower() for keyword in keywords.split(",") if keyword.strip()]

    recommendations = []

    for book in books:
        if yearFilter and book["first_publish_year"] < yearFilter:
            continue

        score = calculateScore(book, genres, authors, keywords)

        if score > 0:
            recommendations.append({
                "title": book["title"],
                "author": ", ".join(book["author"]),
                "genre": book["genre"],
                "year": book["first_publish_year"],
                "score": score
            })

    if sortBy == "Рейтинг":
        recommendations.sort(key=lambda x: x["score"], reverse=True)
    elif sortBy == "Алфавит":
        recommendations.sort(key=lambda x: x["title"])
    elif sortBy == "Год":
        recommendations.sort(key=lambda x: x["year"])

    return recommendations

def showRecommendations():
    genres = genresEntry.get()
    authors = authorsEntry.get()
    keywords = keywordsEntry.get()

    try:
        yearFilter = int(yearFilterEntry.get()) if yearFilterEntry.get() else None
    except ValueError:
        messagebox.showerror("Ошибка", "Год должен быть числом.")
        return

    sortBy = sortByCombobox.get()

    recommendations = recommendBooks(genres, authors, keywords, yearFilter, sortBy)

    for row in tree.get_children():
        tree.delete(row)

    for book in recommendations:
        tree.insert("", tk.END, values=(book["title"], book["author"], book["genre"], book["year"], book["score"]))

def saveRecommendations():
    recommendations = []
    for item in tree.get_children():
        recommendations.append(tree.item(item, "values"))

    if not recommendations:
        messagebox.showinfo("Сохранение", "Список рекомендаций пуст.")
        return

    filePath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])

    if filePath:
        with open(filePath, "w", encoding="utf-8") as file:
            json.dump(recommendations, file, ensure_ascii=False, indent=4)
        messagebox.showinfo("Сохранение", "Рекомендации сохранены в файл.")


root = tk.Tk()
root.title("Рекомендательная система книг")

frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="Любимые жанры (через запятую):").grid(row=0, column=0, sticky="w")
genresEntry = tk.Entry(frame, width=50)
genresEntry.grid(row=0, column=1)

tk.Label(frame, text="Любимые авторы (через запятую):").grid(row=1, column=0, sticky="w")
authorsEntry = tk.Entry(frame, width=50)
authorsEntry.grid(row=1, column=1)

tk.Label(frame, text="Ключевые слова (через запятую):").grid(row=2, column=0, sticky="w")
keywordsEntry = tk.Entry(frame, width=50)
keywordsEntry.grid(row=2, column=1)

tk.Label(frame, text="Год публикации (с фильтром):").grid(row=3, column=0, sticky="w")
yearFilterEntry = tk.Entry(frame, width=50)
yearFilterEntry.grid(row=3, column=1)

tk.Label(frame, text="Сортировка:").grid(row=4, column=0, sticky="w")
sortByCombobox = ttk.Combobox(frame, values=["Рейтинг", "Алфавит", "Год"], state="readonly")
sortByCombobox.grid(row=4, column=1)
sortByCombobox.set("Рейтинг")

buttonFrame = tk.Frame(root)
buttonFrame.pack(pady=10)

tk.Button(buttonFrame, text="Показать рекомендации", command=showRecommendations).pack(side="left", padx=5)
tk.Button(buttonFrame, text="Сохранить рекомендации", command=saveRecommendations).pack(side="left", padx=5)

tree = ttk.Treeview(root, columns=("Название", "Автор", "Жанр", "Год", "Рейтинг"), show="headings")

for col in ("Название", "Автор", "Жанр", "Год", "Рейтинг"):
    tree.heading(col, text=col)
    tree.column(col, width=200 if col == "Название" else 100, anchor="w")

tree.pack(fill=tk.BOTH, expand=True)

root.rowconfigure(1, weight=1)
root.columnconfigure(0, weight=1)

root.mainloop()
