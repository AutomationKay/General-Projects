import pyautogui
import time
import random
import logging

# Configuring logging for possible debugging 
logging.basicConfig(filename='chrome_script.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def random_delay(min_ms, max_ms):
    """
     Function to generate a random delay

    Args:
        min_ms (int): Minimum seconds
        max_ms (int): Maximum seconds
    """
    delay = random.uniform(min_ms / 1000, max_ms / 1000)
    logging.info(f'Random delay for {delay:.2f} seconds')
    time.sleep(delay)
    
def refresh_page():
    """
    Function to refresh the page using pyautogui
    
    """
    pyautogui.hotkey('ctrl', 'r')
    logging.info('Refreshed page with Ctrl + R')

def switch_tab():
    """
    Function to switch to the next tab using pyautogui with simultaneous key presses
    
    """
    logging.info("Switching tab with Ctrl + Tab using pyautogui")
    pyautogui.hotkey('ctrl', 'tab')

def random_mouse_movement():
    """
    Function to perform random mouse movements
    
    """
    screen_width, screen_height = pyautogui.size()
    random_x = random.randint(0, screen_width)
    random_y = random.randint(0, screen_height)
    logging.info(f'Moving mouse to random coordinates: ({random_x}, {random_y})')
    pyautogui.moveTo(random_x, random_y, duration=random.uniform(0.5, 1.5))  # Random human like mouse movement

def click_at(x, y):
    """
    Function to click at specific coordinates

    Args:
        x (int): Mouse x coordinates
        y (int): Mouse y coordinates
    """
    pyautogui.click(x, y)
    logging.info(f'Clicked at: ({x}, {y})')

def type_text(text):
    """
    Function to type a string with random delays between keystrokes

    Args:
        text (str): String for script to enter into chat
    """
    for char in text:
        pyautogui.typewrite(char)
        delay = random.uniform(0.01, 0.05)  # Random delay between keystrokes to simulate human like motions (10-50 ms)
        time.sleep(delay)
        logging.info(f'Typed: {char}')
    pyautogui.press('enter')
    logging.info('Pressed Enter')


def select_three_random_emotes(emotes):
    """
    Function to select 3 unique random emotes from the list

    Args:
        emotes (list): list of emotions for use

    Returns:
        list: Returns a list to be joined for text writing
    """
    num_emotes = random.randint(2, 6)
    selected_emotes = random.sample(emotes, num_emotes)
    logging.info(f'Selected emotes: {" ".join(selected_emotes)}')
    return " ".join(selected_emotes)

# List of emote names
emotes = [
    "Dancingdragon",
    "Eazy",
    "Pourupandtoast",
    "Lurking",
    "Numberone",
    "Cookingupinthelab",
    "HighIQplays",
    "Hello",
    "TheBow",
    "HoodieK",
    "Everythingisfine",
    "Carrying"
]

# Coordinates for the chat box in Google Chrome
chat_box_x = 2322
chat_box_y = 1322 

while True:
    random_delay(2000, 4000)

    # Refresh the page
    refresh_page()

    # Shorter delay for page load (change based on PC performance and simulation goals)
    random_delay(9000, 30000)
    
    # Perform random mouse movement after switching tabs
    random_mouse_movement()

    # Click at specific coordinates for the chat box
    click_at(chat_box_x, chat_box_y)
    random_delay(200, 500)

    # Click into the chat box again to ensure focus
    click_at(chat_box_x, chat_box_y)
    random_delay(200, 500)

    # Choose three random emotes and type them
    text = select_three_random_emotes(emotes)
    type_text(text)

    random_delay(3000, 6000)

    # Switch to the next tab
    switch_tab()

    # Shorter delay for page load (change based onlab PC performance and simulation goals)
    random_delay(9000, 20000)
    
    # Perform random mouse movement after switching tabs
    random_mouse_movement()
