import tkinter as tk
from tkinter import ttk
import window_vanish as wv
import threading


AlgorithmComboBox = None
FavouritesSpinbox = None
UserModelDumpTextArea = None
WindowList = None
StepComboBox = None
window_vanish_thread = None


def setupLeftFrame(left_frame):
    global WindowList

    left_frame.grid_rowconfigure(0, weight=3)
    left_frame.grid_rowconfigure(2, weight=1)
    left_frame.grid_columnconfigure(0, weight=1)

    list_frame = tk.Frame(left_frame)
    list_frame.grid(row=0, column=0, sticky="nsew", padx=5)

    window_list = tk.Listbox(list_frame, height=16)
    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=window_list.yview)
    window_list.configure(yscrollcommand=scrollbar.set)

    window_list.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    WindowList = window_list

    button_frame = tk.Frame(left_frame)
    button_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

    excludeBtn = ttk.Button(button_frame, text="Exclude", 
                          command=lambda: excludeWindow(WindowList.get(WindowList.curselection()[0]) if WindowList.curselection() else None))
    unexcludeBtn = ttk.Button(button_frame, text="Unexclude", 
                            command=lambda: unexcludeWindow(WindowList.get(WindowList.curselection()[0]) if WindowList.curselection() else None))
    clearBtn = ttk.Button(button_frame, text="Clear")

    def on_select(event):
        if WindowList.curselection():
            excludeBtn.config(state="normal")
            unexcludeBtn.config(state="normal")
        else:
            excludeBtn.config(state="disabled")
            unexcludeBtn.config(state="disabled")

    WindowList.bind('<<ListboxSelect>>', on_select)
    excludeBtn.config(state="disabled")
    unexcludeBtn.config(state="disabled")

    excludeBtn.pack(side="left", expand=True, padx=2)
    unexcludeBtn.pack(side="left", expand=True, padx=2)
    clearBtn.pack(side="left", expand=True, padx=2)


def setupRightFrame(right_frame):
    global UserModelDumpTextArea, FavouritesSpinbox, AlgorithmComboBox, StepComboBox

    right_frame.grid_rowconfigure(0, weight=3)
    right_frame.grid_rowconfigure(1, weight=2)
    right_frame.grid_rowconfigure(2, weight=1)
    right_frame.grid_columnconfigure(0, weight=1)

    # ====== TOP FRAME ======

    top_frame = tk.Frame(right_frame)
    top_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    text_area = tk.Text(top_frame, wrap=tk.WORD, state="disabled", height=8)
    scrollbar = ttk.Scrollbar(top_frame, orient="vertical", command=text_area.yview)
    text_area.configure(yscrollcommand=scrollbar.set)

    text_area.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    separator1 = ttk.Separator(right_frame, orient="horizontal")
    separator1.grid(row=1, column=0, sticky="ew", padx=5)

    UserModelDumpTextArea = text_area

    # ====== MIDDLE FRAME ======

    middle_frame = tk.Frame(right_frame)
    middle_frame.grid(row=2, column=0, sticky="nsew", padx=5)

    tk.Label(middle_frame, text="Favourites:").grid(row=0, column=0, padx=5)
    favourite_sb = ttk.Spinbox(middle_frame, from_=1, to=10, width=7)
    favourite_sb.set(3)
    favourite_sb.grid(row=0, column=1, padx=5)

    tk.Label(middle_frame, text="Algorithm:").grid(row=0, column=2, padx=5)
    algo_cb = ttk.Combobox(
        middle_frame, values=["MFU", "MRU"], width=5, state="readonly"
    )
    algo_cb.set("MFU")
    algo_cb.grid(row=0, column=3, padx=5)

    tk.Label(middle_frame, text="Step").grid(row=0, column=4, padx=5)
    step_sb = ttk.Spinbox(middle_frame, from_=1, to=10, width=7)
    step_sb.set(1)
    step_sb.grid(row=0, column=5, padx=5)

    separator2 = ttk.Separator(right_frame, orient="horizontal")
    separator2.grid(row=3, column=0, sticky="ew", padx=5)

    FavouritesSpinbox = favourite_sb
    AlgorithmComboBox = algo_cb
    StepComboBox = step_sb

    # ====== BOTTOM FRAME ======

    bottom_frame = tk.Frame(right_frame)
    bottom_frame.grid(row=4, column=0, sticky="nsew", padx=5, pady=5)

    startStopBtn = ttk.Button(bottom_frame, text="Start")
    resetBtn = ttk.Button(bottom_frame, text="Reset")
    exitBtn = ttk.Button(bottom_frame, text="Exit")

    exitBtn.bind("<Button-1>", lambda _: exit())
    resetBtn.bind("<Button-1>", lambda _: resetToDefault())
    startStopBtn.bind("<Button-1>", lambda _: handleStartStop(startStopBtn))

    startStopBtn.pack(side="left", expand=True, padx=2)
    resetBtn.pack(side="left", expand=True, padx=2)
    exitBtn.pack(side="left", expand=True, padx=2)


def setupWindow(rootWindow):
    rootWindow.title("WindowVanish")
    rootWindow.geometry("850x320")
    rootWindow.resizable(False, False)

    left_frame = tk.Frame(rootWindow)
    right_frame = tk.Frame(rootWindow)
    separator = ttk.Separator(rootWindow, orient="vertical")

    rootWindow.grid_columnconfigure(0, weight=1)
    rootWindow.grid_columnconfigure(1, weight=0)
    rootWindow.grid_columnconfigure(2, weight=1)
    rootWindow.grid_rowconfigure(0, weight=1)

    left_frame.grid(row=0, column=0, sticky="nsew", padx=(5, 0))
    separator.grid(row=0, column=1, sticky="ns", padx=5)
    right_frame.grid(row=0, column=2, sticky="nsew", padx=(0, 5))

    left_frame.grid_propagate(False)
    right_frame.grid_propagate(False)

    setupLeftFrame(left_frame)
    setupRightFrame(right_frame)


def stop_window_vanish_thread():
    global window_vanish_thread
    if window_vanish_thread and window_vanish_thread.is_alive():
        wv.stop_window_vanish()
        stop_thread = threading.Thread(
            target=lambda: window_vanish_thread.join(), daemon=True
        )
        stop_thread.start()
        window_vanish_thread = None


def handleStartStop(btn):
    global window_vanish_thread

    if btn["text"] == "Start":
        btn["text"] = "Stop"
        window_vanish_thread = threading.Thread(
            target=wv.start_window_vanish, daemon=True
        )
        window_vanish_thread.start()
    else:
        btn["text"] = "Start"
        stop_window_vanish_thread()


def updateTextArea(text: str):
    UserModelDumpTextArea.config(state="normal")
    UserModelDumpTextArea.delete("1.0", tk.END)
    UserModelDumpTextArea.insert(tk.END, text)
    UserModelDumpTextArea.config(state="disabled")


def excludeWindow(entry: str):
    if not entry:
        return
    hwnd = int(entry.split('(')[1].split(')')[0])
    wv.global_user_model.window_exlusions.append(wv.window_utils.get_title_from_hwnd(hwnd))
    updateUMComponents()


def unexcludeWindow(entry: str):
    if not entry:
        return
    hwnd = int(entry.split('(')[1].split(')')[0])
    wv.global_user_model.window_exlusions.remove(wv.window_utils.get_title_from_hwnd(hwnd))
    updateUMComponents()


def updateUMComponents():
    AlgorithmComboBox.set(wv.global_user_model.algorithm)
    FavouritesSpinbox.set(wv.global_user_model.favourites_size)
    StepComboBox.set(wv.global_user_model.step)
    updateTextArea(wv.global_user_model.dump(stdout=False))
    wv.global_user_model.save_user_model()


def resetToDefault(algo="MFU"):
    wv.reset_opacities()
    wv.global_user_model = wv.UserModel(algorithm=algo)
    updateUMComponents()


def um_setup():
    if wv.user_model_exists():
        wv.global_user_model = wv.load_user_model()
        updateUMComponents()


def updateFavouritesSize():
    wv.global_user_model.favourites_size = int(FavouritesSpinbox.get())
    updateUMComponents()


def updateStepSize():
    wv.global_user_model.step = int(StepComboBox.get())
    updateUMComponents()


def updateAlgorithm():
    resetToDefault(AlgorithmComboBox.get())


def setupEventHandlers():
    FavouritesSpinbox.bind("<FocusOut>", lambda _: updateFavouritesSize())
    AlgorithmComboBox.bind("<<ComboboxSelected>>", lambda _: updateAlgorithm())
    StepComboBox.bind("<FocusOut>", lambda _: updateStepSize())


def readableWindowList() -> list:
    windows = []
    for hwnd in wv.global_user_model.windows:
        title = wv.window_utils.get_title_from_hwnd(hwnd)
        score = wv.global_user_model.window_scores.get(hwnd, 0)
        windows.append(f"{title} ({hwnd}) - [{score}]")

    return windows


def updateWindowList(windows: list):
    WindowList.delete(0, tk.END)

    for window in windows:
        WindowList.insert(tk.END, window)


def windowListUpdater(root):
    windows = readableWindowList()
    updateWindowList(windows)
    root.after(3000, lambda: windowListUpdater(root))


def textAreaUpdater(root):
    updateTextArea(wv.global_user_model.dump(stdout=False))
    root.after(3000, lambda: textAreaUpdater(root))


def main():
    rootWindow = tk.Tk()
    setupWindow(rootWindow)
    wv.start_auto_setup()
    um_setup()
    setupEventHandlers()
    windowListUpdater(rootWindow)
    textAreaUpdater(rootWindow)

    def on_closing():
        stop_window_vanish_thread()
        rootWindow.destroy()

    rootWindow.protocol("WM_DELETE_WINDOW", on_closing)
    rootWindow.mainloop()


if __name__ == "__main__":
    main()
