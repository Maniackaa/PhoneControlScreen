import json

with open('script.log', encoding='utf-8') as file:
    lines = (file.readlines())
    for line in lines:
        line_dict = json.loads(line)
        # print(line_dict)
        event = line_dict['event']
        timestamp = line_dict['timestamp']
        payment_id = 'af10b8ab-8bd0-45a7-a88b-be5deecb3c14'
        if timestamp >= '2024-12-14 00:34' and timestamp <= '2024-12-14 00:35':
            # if payment_id in event:
            print(f'{timestamp} {event}')


