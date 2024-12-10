import os
import time

from adbutils import AdbClient

from config.bot_settings import logger, BASE_DIR

tess_folder = '/sdcard/tesseract/tessdata'


def get_file_list(directory, adb_device):
    """
    Получение списка файлов из директории с их размерами
    """
    command = f'ls -l {directory}'
    files_output = adb_device.shell(command)
    files = files_output.splitlines()
    file_list = []
    for file in files:
        if file.startswith('total'):
            continue
        items = file.split()
        if len(items) >= 5:
            file_name = items[-1]
            file_size = int(items[4])
            file_list.append((file_name, file_size))
    return file_list


def main():
    # adb_client = AdbClient(host="host.docker.internal", port=5037)
    # adb_client = AdbClient(host="127.0.0.1", port=5037)
    adb_client = AdbClient(host=os.getenv('HOST'), port=5037)
    adb_devices = adb_client.device_list()
    logger.info(f'Подключено: {adb_devices}')
    try:
        for adb_device in adb_devices:
            device_name = adb_device.info.get('serialno')
            data = get_file_list(tess_folder, adb_device)
            logger.debug(f'Количество скринов на {device_name}: {len(data)}')
            logger.debug(str(data))
            print(data)
            files = []
            for file in data:
                files.append(file[0])
            file_eng = BASE_DIR / 'eng.traineddata'
            file_rus = BASE_DIR / 'rus.traineddata'
            if 'eng.traineddata'not in files:
                print('Заливаем eng.traineddata')
                adb_device.sync.push(file_eng, f'{tess_folder}/eng.traineddata')
            if 'rus.traineddata' not in files:
                print('Заливаем rus.traineddata')
                adb_device.sync.push(file_rus, f'{tess_folder}/rus.traineddata')


    except Exception as err:
        logger.debug(err, exc_info=True)
        time.sleep(5)


if __name__ == '__main__':
    main()
