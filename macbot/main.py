import vk_api
import requests
from vk_api.longpoll import VkLongPoll, VkEventType
import random
import time
import imgkit
import qrcode
from jinja2 import Environment, FileSystemLoader
import multiprocessing as mp
from multiprocessing import Process
import os
import threading
from config import token

print(mp.current_process().name, 'print')
vk_session = vk_api.VkApi(token=token)
longpoll = VkLongPoll(vk_session)

vk = vk_session.get_api()

def create_photo(tasks, results):
    """Процесс создания картинки"""
    print(f'Starting process {mp.current_process().name}')
    while True:

        event = tasks.get()
        code_list= [random.randint(10000, 80000) for _ in range(5)]
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
            # file_name = qr_code
            imgkit.from_file(f'{code}.html', file_name)
            print(f'Create {file_name} at process {mp.current_process().name}')
            results.put({'f_name': file_name, 'e': event})

            #delete tmp files
            os.remove(f'{code}.png'); os.remove(f'{code}.html')

        print(f'Finish render coupons at process {mp.current_process().name} in {time.time()-start}sec')


def build_request(results):
    """Функция потока ,в которой из очереди готовых фоток берется имя файла и отправляется в Vk"""
    print(f'start thread {threading.currentThread().name}')
    while True:
        res = results.get()
        print(f'Get photo from result at {threading.currentThread().name};'
              f' {results.qsize()} photo left')

        start = time.time()
        file_name = res['f_name']; event = res['e']
        upload_url = vk.photos.getMessagesUploadServer(peer_id=event.peer_id)['upload_url']  # -> dict
        with open(file_name, 'rb') as f:
            files = {"photo": f}
            res = requests.post(url=upload_url, files=files).json()

            photo = vk.photos.saveMessagesPhoto(server=res['server'], photo=res['photo'], hash=res['hash'])[0]
            photo_id, owner_id = photo['id'], photo['owner_id']
            attch = f"photo{owner_id}_{photo_id}"

            vk.messages.send(user_id=event.user_id, attachment=attch, random_id=random.randint(0, 999999))
            print(f'Upload {file_name} at {threading.currentThread().name} in {time.time()-start}')

        os.remove(file_name)



def upload_photo(results):
    """Процесс для отправки фотографий, используя несколько потоков"""
    print(f'Starting process {mp.current_process().name}')
    t_count = 5
    threads = []
    for i in range(t_count):
        t = threading.Thread(target=build_request, name=f'thread#{i+1}',args=(results, ))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


def polling(tasks):
    for event in longpoll.listen():

        if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:

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

































