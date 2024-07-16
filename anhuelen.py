# Anhuelen - Take In
# Anhuelen is an input managment module. Use it to prompt users 
# neatly for input and handle returned results

class clr:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    GREYOUT = '\033[37m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    CURSUP = "\033[A"
    CURSDOWN = '\033[B'
    CURSNEXT = '\033[C'
    CURSBACK = '\033[D'

# Prints a title or header. change first value to prefered styling to indicate
def title(text):
    print(f"{clr.UNDERLINE}{text}{clr.END}")

# Takes a question and predetermined answer and displays them
def inform(question, answer=''):
    print(f"{clr.END}{question}: {clr.OKBLUE}{answer}{clr.END}")

# Takes a question and default answer, allows user to accept default with [Enter]
# or to type a new answer. Returns that answer either way
def prompt(question, answer=''):
    print(f"{clr.END}{question}: {clr.GREYOUT}{answer}{clr.END}", end='\b'*len(str(answer)))
    new_answer = input(f"{clr.OKGREEN}")

    if new_answer == '':
        print(f"{clr.CURSUP}", end='')
        print(f"{clr.CURSNEXT}"*(len(question) + 2), end='')
        print(f"{answer}{clr.END}")
        return answer

    erase_extra = len(answer) - len(new_answer)
    if erase_extra > 0:
        print(f"{clr.CURSUP}", end='')
        print(f"{clr.CURSNEXT}"*(len(question) + 2 + len(new_answer)), end='')
        print(" "*erase_extra)

    print(f"{clr.END}", end='')
    return new_answer
