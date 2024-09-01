import time
from pathlib import Path
import pyautogui as pg
import keyboard
import pyperclip

from services.func import Target, find_target_in_image, make_screenshot
# 5462 6312 1882 6164 07\26 cvv285
insert_card_data_key = 'ctrl+q'
data = "10;5462631218826164;08/25;299;3434"
card_field = Target(img=Path('media/target_card.png'), x=30, y=115)
exp_from_card = (0, 38)
cvv_from_card = (95, 38)
box_field = Target(img=Path('media/checkbox_target.png'), x=20, y=60)
card_confirm_button = Target(img=Path('media/card_confirm_button.png'), x=75, y=55)
amount, card, exp, cvv, sms = data.split(';')


def insert_card_data():
    try:
        data = pyperclip.paste()
        amount, card, exp, cvv, sms = data.split(';')
        print(amount, card, exp, cvv, sms)
        target_point = find_target_in_image(make_screenshot(), box_field, 0.8)
        if target_point:
            pg.click(target_point[0], target_point[1])

        target_point = find_target_in_image(make_screenshot(), card_field, 0.8)
        if target_point:
            pg.click(target_point[0], target_point[1])
            pyperclip.copy(card)
            keyboard.release(insert_card_data_key)
            keyboard.send('ctrl+v')
            time.sleep(1)

            pyperclip.copy(exp)
            pg.click(target_point[0] + exp_from_card[0], target_point[1] + exp_from_card[1])
            keyboard.send('ctrl+v')
            time.sleep(0.5)

            pyperclip.copy(cvv)
            pg.click(target_point[0] + cvv_from_card[0], target_point[1] + cvv_from_card[1])
            keyboard.send('ctrl+v')

        target_point = find_target_in_image(make_screenshot(), card_confirm_button, 0.8)
        if target_point:
            pg.moveTo(target_point[0], target_point[1])
            # pg.click(target_point[0], target_point[1])
    except Exception as err:
        print(err)


def main():
    keyboard.add_hotkey(insert_card_data_key, insert_card_data)
    keyboard.wait()


if __name__ == '__main__':
    main()


