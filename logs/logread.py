import json

with open('script.log', encoding='utf-8') as file:
    lines = (file.readlines())
    for line in lines:
        line_dict = json.loads(line)
        # print(line_dict)
        event = line_dict['event']
        timestamp = line_dict['timestamp']
        payment_id = '6c1dfc20-c733-4092-afd8-d5d950236eff'
        if timestamp >= '2024-12-09 00:50' and timestamp <= '2024-12-09 00:55':
            # if payment_id in event:
            print(f'{timestamp} {event}')


