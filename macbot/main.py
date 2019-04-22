import vk_api
import requests
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api import VkUpload
import random
import time
import json
import imgkit
import qrcode
from jinja2 import Environment, FileSystemLoader
import multiprocessing as mp
from multiprocessing import Process
import os

token = ""

vk_session = vk_api.VkApi(token=token)
longpoll = VkLongPoll(vk_session)

vk = vk_session.get_api()


def create_photo(tasks, results):
    print(f'Starting process {mp.current_process().name}')
    while True:

        event = tasks.get()
        code_list= [random.randint(10000, 80000) for _ in range(5)]
        # code_list = [111]
        start = time.time()
        for code in code_list:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(code)
            qr.make(fit=True)

            img = qr.make_image()
            qr_code = f'{code}.png'
            img.save(qr_code)

            file_loader = FileSystemLoader('templates')
            env = Environment(loader=file_loader)

            template = env.get_template('qr.html')
            output = template.render(qr_code=qr_code)
            with open(f'{code}.html', 'w') as fin:
                print(output, file=fin)

            file_name = f'coupon#{code}.jpg'
            imgkit.from_file(f'{code}.html', file_name)
            results.put({'f_name': file_name, 'e': event})

            #delete tmp files
            os.remove(f'{code}.png'); os.remove(f'{code}.html')

        print(f'Finish render coupons at process {mp.current_process().name} in {time.time()-start}sec')


def upload_photo(results):
    print(f'Starting process {mp.current_process().name}')
    while True:

        res = results.get()
        print('Get photo from result')
        start = time.time()
        file_name = res['f_name']; event = res['e']
        upload_url = vk.photos.getMessagesUploadServer(peer_id=event.peer_id)['upload_url']  # -> dict
        files = {"photo": open(file_name, 'rb')}
        res = requests.post(url=upload_url, files=files).json()

        photo = vk.photos.saveMessagesPhoto(server=res['server'], photo=res['photo'], hash=res['hash'])[0]
        photo_id, owner_id = photo['id'], photo['owner_id']
        attch = f"photo{owner_id}_{photo_id}"

        vk.messages.send(user_id=event.user_id, attachment=attch, random_id=random.randint(0, 999999))
        os.remove(file_name)
        print(f'Upload {file_name} at process {mp.current_process().name} in {time.time()-start}')




def polling(tasks):
    for event in longpoll.listen():

        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
            if event.text:
                if event.from_user:
                    print('recieve event')
                    tasks.put(event)


if __name__ == '__main__':
    tasks = mp.Queue()
    results = mp.Queue()
    n_procs = mp.cpu_count()  # 4
    for i in range(n_procs - 1):
        mp.Process(target=create_photo, args=(tasks, results), name=f'render_worker {i+1}').start()

    mp.Process(target=upload_photo, args=(results, ), name=f'upload_worker {n_procs}').start()

    polling(tasks)
