from pathlib import Path
import re


def strip_g04_comments_line(line: str) -> str:
    """
    Rimuove tutti i segmenti commento G04 su una singola riga.
    - Se c'è un '*', elimina 'G04 ... *' incluso l'asterisco.
    - Se non c'è '*', elimina 'G04 ...' fino a fine riga.
    """
    i = 0
    out = []
    n = len(line)
    while i < n:
        idx = line.find("G04", i)
        if idx == -1:
            # nessun altro G04: conserva il resto
            out.append(line[i:])
            break
        # conserva la parte prima del commento
        out.append(line[i:idx])
        # cerca il terminatore '*'
        star = line.find('*', idx + 3)
        if star == -1:
            # niente '*': commento fino a fine riga
            # scarta il resto della riga
            break
        # salta il segmento commento includendo '*'
        i = star + 1

    # ricompone e normalizza spazi extra
    cleaned = ''.join(out).strip()
    return cleaned


def remove_g04_comments(text: str) -> str:
    cleaned_lines = []
    for raw_line in text.splitlines():
        line = strip_g04_comments_line(raw_line)
        if line:  # tieni solo righe non vuote
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

if __name__ == "__main__":
    gerber_file = Path("C:\\TheAntFarmRepo\\GerberWizard\\data\\g04_comment_check.txt")
    with open(gerber_file, "r", encoding="utf-8") as f:
        content = f.read()

    clean_text = remove_g04_comments(content)
    print(clean_text)
