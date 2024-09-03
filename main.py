import time
from pathlib import Path

import mouse
import pyautogui as pg
import keyboard
import pyperclip

from services.func import Target, find_target_in_image, make_screenshot
# 5462 6312 1882 6164 07\26 cvv285
insert_card_data_key = 'ctrl+q'
data = "10;5462631218826164;08/25;299;3434"
card_field = Target(img=Path('media/target_card.png'), x=30, y=115)
exp_from_card = (10, 60)
cvv_from_card = (110, 60)
box_field = Target(img=Path('media/checkbox_target.png'), x=20, y=60)
card_confirm_button = Target(img=Path('media/card_confirm_button.png'), x=75, y=55)
amount, card, exp, cvv, sms = data.split(';')
with open('settings.ini') as file:
    data = file.read().split('\n')
    thresh1 = float(data[0])
    thresh2 = float(data[1])
    after_click_delay = float(data[2])
    after_input_delay = float(data[3])
print(thresh1, thresh2, after_click_delay, after_input_delay)


def insert_card_data():
    try:
        data = pyperclip.paste()
        amount, card, exp, cvv, sms = data.split(';')
        print(amount, card, exp, cvv, sms)
        target_point = find_target_in_image(make_screenshot(), box_field, thresh1)
        if target_point:
            print('Нашел чекбокс')
            pg.click(target_point[0], target_point[1])
        else:
            print('Не нашел чекбокс')

        target_point = find_target_in_image(make_screenshot(), card_field,  thresh2)
        if target_point:
            pyperclip.copy(card)
            print('Нашел поле карты')
            pg.click(target_point[0], target_point[1])
            time.sleep(after_click_delay)
            keyboard.release(insert_card_data_key)
            keyboard.send('ctrl+v')
            time.sleep(after_input_delay)

            pyperclip.copy(exp)
            pg.click(target_point[0] + exp_from_card[0], target_point[1] + exp_from_card[1])
            time.sleep(after_click_delay)
            keyboard.send('ctrl+v')
            time.sleep(after_input_delay)

            pyperclip.copy(cvv)
            pg.click(target_point[0] + cvv_from_card[0], target_point[1] + cvv_from_card[1])
            time.sleep(after_click_delay)
            keyboard.send('ctrl+v')
            time.sleep(after_input_delay)
        else:
            print('Не нашел поле карты')
        # target_point = find_target_in_image(make_screenshot(), card_confirm_button, thresh2)
        # if target_point:
            pg.click(target_point[0], target_point[1])
    except Exception as err:
        print(err)


def main():
    keyboard.add_hotkey(insert_card_data_key, insert_card_data)
    keyboard.wait()


if __name__ == '__main__':
    main()


