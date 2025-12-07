

def clean_gerber_text(text: str, in_line_comment_char: str = ';') -> str:
    # Rimuovi newline, tab e spazi superflui
    no_spaces = text.replace(" ", "")
    no_comments = "\n".join([x.split(in_line_comment_char)[0].upper() for x in no_spaces.split("\n")])
    # rimuovo i commenti G04, dato che sono complessi, li elimino utilizzando \n come
    # terminatore del commento.
    lines = no_comments.splitlines()
    no_g04 = ""
    for l in lines:
        i = l.find("G04")
        if i != -1:
            nl = l[:i]
        else:
            nl = l
        if nl:
            no_g04 += nl + "\n"
    cleaned = no_g04.replace("\n", "").replace("\r", "").replace("\t", "").strip()
    return cleaned


def tokenize_gerber(raw_text: str, in_line_comment_char: str = '#'):

    text = clean_gerber_text(raw_text, in_line_comment_char=in_line_comment_char)

    # print("text:")
    # print(text)

    i = 0
    length = len(text)
    macro_start = False
    macro_body = ""
    while i < length:
        ch = text[i]
        if ch == '%':
            # cerco un * per trovare la fine del token
            j = text.find('*', i + 1)
            if j == -1:
                raise ValueError("Parametro Gerber non chiuso correttamente")
            # ho trovato un asterisco i casi ora sono 2:
            # - il carattere successivo e' un % allora e' un parametro
            # - il carattere successivo non e' un % allora e' l'intestazione di una macro.
            if text[j+1] == '%':
                # parametro
                block = text[i + 1:j + 1]
                if block != "*":
                    yield ('param', block)
                    i = j + 2
                else:
                    i = j + 1
            else:
                # macro init
                block = text[i + 1:j + 1]
                yield ('macro_start', block)
                macro_start = True
                i = j + 1
            print("% ->", block)
            continue

        j = text.find('*', i)
        if j == -1:
            break
        stmt = text[i:j + 1].strip()
        if stmt.startswith('G04'):
            yield ('comment', stmt)
            i = j + 1
            continue
        if stmt:
            if macro_start:
                macro_body += stmt
                if j + 1 < length:
                    if text[j + 1] == '%':
                        yield ('macro_body', macro_body)
                        print("MA ->", macro_body)
                        macro_start = False
                        macro_body = ""
                        i = j + 2
                        continue
                else:
                    raise ValueError("File incompleto")
            else:
                yield ('stmt', stmt)
                print("stmt ->", stmt)
        i = j + 1
