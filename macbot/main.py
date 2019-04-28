import base64
import vk_api
import requests
from vk_api.longpoll import VkLongPoll, VkEventType
import random
import time
import imgkit
import qrcode
from jinja2 import Template
import multiprocessing as mp
import threading
import io
import os

token = os.environ['token']
vk_session = vk_api.VkApi(token=token)
longpoll = VkLongPoll(vk_session)

vk = vk_session.get_api()


def create_photo(tasks, results):
    """Процесс создания картинки"""
    print(f'Starting process {mp.current_process().name}')
    while True:

        event = tasks.get()
        code_list = [random.randint(10000, 80000) for _ in range(10)]
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
            binary_stream = io.BytesIO()
            img.save(binary_stream)
            img_str = base64.b64encode(binary_stream.getvalue()).decode("utf-8")
            with open('qr.html') as fout:
                template = Template(fout.read())
                template = template.render(qr_code=img_str)
                img_bytes = imgkit.from_string(template, False)
                binary_stream.seek(0)
                binary_stream.write(img_bytes)
                binary_stream.seek(0)
                results.put({'f': binary_stream, 'e': event})

        print(f'Finish render coupons at process {mp.current_process().name} in {time.time()-start}sec')


def build_request(results):
    """Функция потока ,в которой из очереди готовых фоток берется имя файла и отправляется в Vk"""
    print(f'start thread {threading.currentThread().name}')
    while True:
        res = results.get()
        print(f'Get photo from result at {threading.currentThread().name};'
              f' {results.qsize()} photo left')

        start = time.time()
        f = res['f']; event = res['e']
        upload_url = vk.photos.getMessagesUploadServer(peer_id=event.peer_id)['upload_url']  # -> dict

        files = {'photo': ('photo.png', f, 'image/png')}

        res = requests.post(url=upload_url, files=files).json()

        photo = vk.photos.saveMessagesPhoto(server=res['server'], photo=res['photo'], hash=res['hash'])[0]
        photo_id, owner_id = photo['id'], photo['owner_id']
        attch = f"photo{owner_id}_{photo_id}"

        vk.messages.send(user_id=event.user_id, attachment=attch, random_id=random.randint(0, 999999))
        print(f'Upload photo at {threading.currentThread().name} in {time.time()-start}')


def upload_photo(results):
    """Процесс для отправки фотографий, используя несколько потоков"""
    print(f'Starting process {mp.current_process().name}')
    t_count = 5
    threads = []
    for i in range(t_count):
        t = threading.Thread(target=build_request, name=f'thread#{i+1}', args=(results,))
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
    n_procs = mp.cpu_count()
    for i in range(n_procs - 1):
        mp.Process(target=create_photo, args=(tasks, results), name=f'render_worker {i+1}').start()

    mp.Process(target=upload_photo, args=(results,), name=f'upload_worker {n_procs}').start()

    polling(tasks)
