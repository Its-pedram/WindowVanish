import time, os, json, threading
import window_utils


class UserModel:
    algorithm: str = ""  # MRU, MFU
    favourites_size: int = 0
    step: int = 0
    windows: list = []
    window_opacities: dict = {}
    window_scores: dict = {}
    window_exlusions: list = []

    def __init__(self, algorithm="MFU", favourites_size=3, step=1):
        self.algorithm = algorithm
        self.favourites_size = favourites_size
        self.step = step
        self.windows = []
        self.window_opacities = {}
        self.window_scores = {}
        self.window_exlusions = []

    def save_user_model(self):
        print("[!] Saving user model...")
        try:
            with open(USER_MODEL_FILE, "w") as f:
                f.write(
                    json.dumps(
                        self, default=lambda o: o.__dict__, sort_keys=True, indent=4
                    )
                )
        except Exception as e:
            print(f"[!] Error saving user model: {e}")

    def dump(self, stdout=True):
        if stdout:
            print("[!] Dumping user model...\n")
            print(json.dumps(self, default=lambda o: o.__dict__, indent=4))
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)

    def filter_zombies(self):
        self.windows = [
            window
            for window in self.windows
            if window != 0 and window_utils.get_title_from_hwnd(window)
        ]


global_user_model: UserModel = None
USER_MODEL_FILE = "user_model.json"
stop_thread = False
lock = threading.Lock()


def load_user_model() -> UserModel:
    print("[!] Loading user model...")
    with open(USER_MODEL_FILE, "r") as f:
        data = json.load(f)
        user_model = UserModel(data["algorithm"], data["favourites_size"])
        user_model.windows = data["windows"]
        user_model.window_opacities = data["window_opacities"]
        user_model.window_scores = data["window_scores"]
        user_model.window_exlusions = data["window_exlusions"]
        return user_model


def user_model_exists() -> bool:
    if os.path.exists(USER_MODEL_FILE):
        with open(USER_MODEL_FILE, "r") as f:
            return len(f.read()) > 0
    return False


def print_separator():
    """
    Borrowed from: https://github.com/Its-pedram/CoolCheckSums/blob/dev/src/ccs.py
    """
    try:
        columns, _ = os.get_terminal_size(0)
    except OSError:
        columns = 67

    columns = min(columns, 67)

    print("-" * columns)


def print_ascii_art():
    print(
        """
 _       ___           __             _    __            _      __  
| |     / (_)___  ____/ /___ _      _| |  / /___ _____  (_)____/ /_ 
| | /| / / / __ \/ __  / __ \ | /| / / | / / __ `/ __ \/ / ___/ __ \\
| |/ |/ / / / / / /_/ / /_/ / |/ |/ /| |/ / /_/ / / / / (__  ) / / /
|__/|__/_/_/ /_/\__,_/\____/|__/|__/ |___/\__,_/_/ /_/_/____/_/ /_/                                                                     
    """
    )
    print_separator()


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")


def handle_mfu(window):
    global global_user_model

    if window in global_user_model.window_scores:
        global_user_model.window_scores[window] += 1
    else:
        global_user_model.window_scores[window] = 1

    global_user_model.window_scores = dict(
        sorted(
            global_user_model.window_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )


def handle_mru(window):
    global global_user_model

    length = len(global_user_model.windows)
    if window in global_user_model.window_scores:
        for w in global_user_model.windows:
            if w == window:
                global_user_model.window_scores[w] = length
            else:
                global_user_model.window_scores[w] = max(
                    1, global_user_model.window_scores[w] - 1
                )
    else:
        global_user_model.window_scores[window] = length

    global_user_model.window_scores = dict(
        sorted(
            global_user_model.window_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )


def handle_opacity():
    global global_user_model
    for window in global_user_model.windows:
        opacity = global_user_model.window_opacities[window]
        window_utils.set_window_opacity(window, opacity)
        if opacity == 0:
            window_utils.minimize_window(window)
            window_utils.set_window_opacity(window, 255)


def window_tracker():
    print("[!] Starting window tracker...")
    global global_user_model
    previous_window = None
    while not stop_thread:
        with lock:
            current_window = window_utils.get_focused_window()
            if any(
                [
                    exclusion in window_utils.get_title_from_hwnd(current_window)
                    for exclusion in global_user_model.window_exlusions
                ]
            ):
                continue
            global_user_model.window_opacities[current_window] = 255
            handle_opacity()
            if current_window not in global_user_model.windows:
                global_user_model.windows.append(current_window)
            if (
                global_user_model.algorithm == "MFU"
                and current_window != previous_window
            ):
                handle_mfu(current_window)
            elif (
                global_user_model.algorithm == "MRU"
                and current_window != previous_window
            ):
                handle_mru(current_window)
            global_user_model.filter_zombies()
            previous_window = current_window
        time.sleep(0.1)


def vanish():
    global global_user_model
    for i, window in enumerate(global_user_model.window_scores):
        if i < global_user_model.favourites_size:
            continue
        if global_user_model.window_opacities[window] - global_user_model.step >= 0:
            global_user_model.window_opacities[window] -= global_user_model.step
        else:
            global_user_model.window_opacities[window] = 0


def start_window_vanish():
    global global_user_model
    tracker_thread = threading.Thread(target=window_tracker)
    tracker_thread.start()
    while True:
        with lock:
            vanish()
            clear_terminal()
            global_user_model.dump(stdout=True)
            for window in global_user_model.windows:
                print(
                    f"Window: {window}, Name: {window_utils.get_title_from_hwnd(window)}"
                )
            print(f"Last Update: {time.ctime()}")
        print_separator()
        time.sleep(1)


def open_menu():
    print(
        """
[1] Start WindowVanish
[2] Dump (Print) User Model
[3] Save User Model
[4] Exit
          """
    )
    choice = input("Enter your choice $> ")
    match choice:
        case "1":
            return start_window_vanish()
        case "2":
            return global_user_model.dump()
        case "3":
            return global_user_model.save_user_model()
        case "4":
            print("\n[!] Exiting...")
            exit()
        case _:
            clear_terminal()
            print("[!] Invalid choice. Please try again.")
    print_separator()


def start_setup():
    global global_user_model
    if user_model_exists():
        global_user_model = load_user_model()
    else:
        print("[!] No user model found. Creating a new one...")
        algorithm = input("Enter the algorithm to use [MRU, MFU] (MFU) $>  ") or "MFU"
        favourites_size = int(
            input("Enter the number of favourites to keep (3) $>  ") or 3
        )
        global_user_model = UserModel(algorithm, favourites_size)
        global_user_model.save_user_model()


def start_auto_setup():
    global global_user_model
    if user_model_exists():
        global_user_model = load_user_model()
    else:
        print("[!] No user model found. Creating a new one...")
        global_user_model = UserModel()
        global_user_model.save_user_model()


def reset_opacities():
    global global_user_model
    for window in global_user_model.windows:
        window_utils.set_window_opacity(window, 255)


def stop_window_vanish():
    global stop_thread
    stop_thread = True
    reset_opacities()
    global_user_model.save_user_model()


def main():
    try:
        print_ascii_art()
        start_setup()
        while True:
            open_menu()
    except KeyboardInterrupt:
        print("\n[!] Exiting...")
        stop_window_vanish()
        exit()
    except Exception as e:
        print(f"[!] Error: {e}")
        exit()


if __name__ == "__main__":
    main()
