import curses
import time
import threading

# Global variable to store the current line number
# current_line = 0
REFRESH_FREQ = 0.2
READ_FILE_FREQ = 1
# Function to read from file and update the screen
def file_reader(stdscr):
    # global current_line
    while True:
        with open('your_file.txt', 'r') as file:
            content = file.readlines()
        for _ in range(int(READ_FILE_FREQ/REFRESH_FREQ)):
            stdscr.clear()
            # for line in content[current_line:]:
            for line in content:
                stdscr.addstr(line)
            stdscr.refresh()
            time.sleep(REFRESH_FREQ)

# Function to update the ETA text bar
def update_eta(stdscr):
    while True:
        eta_text = "ETA: 5 seconds"  # Replace with your actual ETA calculation
        stdscr.addstr(curses.LINES-1, 0, eta_text.ljust(curses.COLS))
        stdscr.refresh()
        time.sleep(REFRESH_FREQ)

def main(stdscr):
    global current_line
    curses.curs_set(0)  # Hide the cursor
    stdscr.scrollok(True)  # Enable scrolling

    # Create and start the file reading thread
    file_thread = threading.Thread(target=file_reader, args=(stdscr,))
    file_thread.daemon = True
    file_thread.start()

    # Create and start the ETA update thread
    eta_thread = threading.Thread(target=update_eta, args=(stdscr,))
    eta_thread.daemon = True
    eta_thread.start()

    while True:
        c = stdscr.getch()
        if c == ord('q'):
            break
        # elif c == curses.KEY_DOWN:
        #     current_line += 1  # Move to the next line
        # elif c == curses.KEY_UP:
        #     current_line -= 1  # Move to the previous line
        #     if current_line < 0:
        #         current_line = 0  # Ensure not to scroll above the first line

curses.wrapper(main)
