import re
import time
from pathlib import Path

INTERVAL = 60
DURATION = 5


def find_steam_root():
    home = Path.home()

    for p in home.rglob("steamapps"):
        root = p.parent
        if (root / "logs/content_log.txt").exists():
            return root

    raise RuntimeError("Steam не найден")


def load_game_names(root):
    names = {}

    for f in (root / "steamapps").glob("appmanifest_*.acf"):
        text = f.read_text(errors="ignore")

        i = re.search(r'"appid"\s+"(\d+)"', text)
        n = re.search(r'"name"\s+"(.+)"', text)

        if i and n:
            names[i.group(1)] = n.group(1)

    return names


def tail(file):
    file.seek(0, 2)
    while True:
        line = file.readline()
        if not line:
            time.sleep(0.2)
            continue
        yield line


appid_re = re.compile(r"AppID\s*(\d+)", re.I)
pause_re = re.compile(r"pause|suspend|stop", re.I)
resume_re = re.compile(r"start|resume|running", re.I)

speed_re = re.compile(r"Current download rate:\s*(\d+(?:\.\d+)?)\s*Mbps", re.I)


def parse_speed(line):
    m = speed_re.search(line)
    if not m:
        return None

    mbps = float(m.group(1))
    return mbps / 8


def main():
    root = find_steam_root()
    names = load_game_names(root)
    log_path = root / "logs/content_log.txt"

    print(f"Steam: {root}")
    print("Мониторинг запущен...\n")

    current_game = "неизвестно"
    paused = False

    with open(log_path, "r", errors="ignore") as f:
        lines = tail(f)

        for _ in range(DURATION):
            speeds = []
            end = time.time() + INTERVAL

            while time.time() < end:
                line = next(lines)

                a = appid_re.search(line)
                if a:
                    current_game = names.get(a.group(1), f"AppID {a.group(1)}")

                if pause_re.search(line):
                    paused = True

                if resume_re.search(line):
                    paused = False

                s = parse_speed(line)
                if s and not paused:
                    speeds.append(s)

            avg = sum(speeds) / len(speeds) if speeds else 0
            status = "Пауза" if paused else "Загрузка"

            print(f"[{status}] {current_game} | {avg:.2f} MB/s")


if __name__ == "__main__":
    main()
