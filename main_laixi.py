import json
import time
from pathlib import Path
import pyautogui as pg
import keyboard
import pyperclip

from services.func import Target, find_target_in_image, make_screenshot

insert_card_data_key = 'ctrl+q'
data = "1000;5462631218826164;08/25;299;3434"

amount_field = Target(img=Path('media/amount_field.png'), x=40, y=70)
amount_ok = (50, 500)
card_field = Target(img=Path('media/target_card.jpg'), x=30, y=115)


exp_from_card = (10, 60)
cvv_from_card = (110, 60)
box_field = Target(img=Path('media/checkboxtarget.jpg'), x=10, y=75)
card_confirm_button = Target(img=Path('media/card_confirm_button.png'), x=75, y=55)
amount, card, exp, cvv, sms = data.split(';')


def get_coord():
    pg.mouseInfo()


def get_settings():
    with open('settings.txt') as file:
        settings = json.load(file)
        print(settings)
        return settings


def insert_card_data():
    try:
        settings = get_settings()
        thresh1 = settings['thresh1']
        thresh2 = settings['thresh2']
        after_click_delay = settings['after_click_delay']
        after_input_delay = settings['after_input_delay']
        after_amount_limit = settings['after_amount_limit']
        data = pyperclip.paste()
        amount, card, exp, cvv, sms = data.split(';')
        print(amount, card, exp, cvv, sms)
        # Ввод суммы
        target_point = find_target_in_image(make_screenshot(), amount_field, thresh1)
        if target_point:
            pyperclip.copy(amount)
            print('Нашел поле amount')
            pg.moveTo(target_point[0], target_point[1])
            pg.click()
            time.sleep(after_click_delay)
            keyboard.send('ctrl+v')
            time.sleep(after_input_delay)
            pg.moveTo(target_point[0] + amount_ok[0], target_point[1] + amount_ok[1])
            pg.click(target_point[0] + amount_ok[0], target_point[1] + amount_ok[1])
            time.sleep(settings['after_amount_delay'])
        else:
            raise TimeoutError('Не нашел amount')

        count = 0
        while True:
            if count >= after_amount_limit:
                raise TimeoutError('Время ожидания экрана карты вышло.')

            # Чекбокс и данные карты
            target_point = find_target_in_image(make_screenshot(), box_field, thresh1)
            if target_point:
                print('Нашел чекбокс')
                # pg.click(target_point[0], target_point[1])
                break
            else:
                print(f'Не нашел чекбокс. Жду еще {after_amount_limit - count} сек.')

            time.sleep(1)
            count += 1
        count = 0
        while True:
            time.sleep(1)
            if count >= after_amount_limit:
                raise TimeoutError('Время ожидания экрана карты вышло.')

            target_point = find_target_in_image(make_screenshot(), card_field,  thresh2)
            if target_point:
                pyperclip.copy(card)
                print('Нашел поле карты')
                pg.moveTo(target_point[0], target_point[1])
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
                break
            else:
                print('Не нашел поле карты')
                count += 1
        # target_point = find_target_in_image(make_screenshot(), card_confirm_button, thresh2)
        # if target_point:
        #     pg.click(target_point[0], target_point[1])
        print('Скрипт завершен')
    except Exception as err:
        print(err)
        print('Скрипт завершен')


def main():
    try:
        keyboard.add_hotkey(insert_card_data_key, insert_card_data)
        # keyboard.add_hotkey('ctrl+shift+q', get_coord())
        keyboard.wait()
    except Exception as err:
        print(err)
        input('Нажмите Enter')


if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        print(err)
        input('Нажмите Enter')


