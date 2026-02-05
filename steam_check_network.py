import time
import psutil
from pathlib import Path
import re

INTERVAL = 60
DURATION = 5


def find_steam_root():
    for p in Path.home().rglob("steamapps"):
        if (p.parent / "logs").exists():
            return p.parent
    raise RuntimeError("Steam не найден")


def load_game_names(root):
    names = {}
    for f in (root / "steamapps").glob("appmanifest_*.acf"):
        t = f.read_text(errors="ignore")
        i = re.search(r'"appid"\s+"(\d+)"', t)
        n = re.search(r'"name"\s+"(.+)"', t)
        if i and n:
            names[i.group(1)] = n.group(1)
    return names


def current_game(root, names):
    manifests = list((root / "steamapps").glob("appmanifest_*.acf"))
    if not manifests:
        return "неизвестно"
    latest = max(manifests, key=lambda x: x.stat().st_mtime)
    t = latest.read_text(errors="ignore")
    i = re.search(r'"appid"\s+"(\d+)"', t)
    if not i:
        return "неизвестно"
    return names.get(i.group(1), latest.stem)


def main():
    root = find_steam_root()
    names = load_game_names(root)

    print(f"Steam: {root}")
    print("Мониторинг запущен...\n")

    prev = psutil.net_io_counters().bytes_recv

    for _ in range(DURATION):
        samples = []

        for _ in range(INTERVAL):
            time.sleep(1)
            cur = psutil.net_io_counters().bytes_recv
            diff = cur - prev
            prev = cur
            samples.append(diff)

        avg = sum(samples) / len(samples) / 1024 / 1024

        game = current_game(root, names)

        status = "Пауза" if avg < 0.05 else "Загрузка"

        print(f"[{status}] {game} | {avg:.2f} MB/s")


if __name__ == "__main__":
    main()
