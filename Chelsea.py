import json
import requests
import os
import youtube_dl
from token_vk import token



def download_pic(url, post_id, pic_id, group_name):
    """Скачивает картинки из постов. Создаёт папки file и post_id если они еще не существуют.
    Имя картинки релевантно id картинки из json файла"""
    resp = requests.get(url)
    if not os.path.exists(f'{group_name}/files'):
        os.mkdir(f'{group_name}/files')
    if not os.path.exists(f'{group_name}/files/{post_id}'):
        os.mkdir(f'{group_name}/files/{post_id}')
    with open(f'{group_name}/files/{post_id}/{pic_id}.jpg', "wb") as f:
        f.write(resp.content)


def download_vid(url, post_id, vid_id, group_name):
    """Скачивает видео из постов, если их длительность меньше 300 секунд. Создаёт папки file и
     post_id если они еще не существуют. Имя видео релевантно id видео из json файла"""
    if not os.path.exists(f'{group_name}/files'):
        os.mkdir(f'{group_name}/files')
    if not os.path.exists(f'{group_name}/files/{post_id}'):
        os.mkdir(f'{group_name}/files/{post_id}')
    try:
        ydl_opts = {"outtmpl": f'{group_name}/files/{post_id}/{vid_id}.mpeg'}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            video_info = ydl.extract_info(url, download=False)
            duration = video_info["duration"]
            if duration > 300:
                print("Video is longer than 90sec")
            else:
                ydl.download([url])
    except Exception:
        print("Видео закрыто")

def extracting_post(post, post_id, group_name):
    """Если в посте есть вложения, скачивает из него видео длительностью меньше 300 секунд
     и картинки высшего из доступных разрешения"""
    try:
        if "attachments" in post:
            post = post["attachments"]
            for att_num in post:
                if att_num["type"] == "photo":
                    photo_url = \
                        att_num["photo"]["sizes"][len(att_num["photo"]["sizes"]) - 1]["url"]
                    photo_id = att_num["photo"]["id"]
                    print(photo_url)
                    download_pic(url=photo_url, post_id=post_id, pic_id=photo_id,
                                 group_name=group_name)

                elif att_num["type"] == "video":
                    print("video post")
                    video_owner_id = att_num["video"]["owner_id"]
                    video_id = att_num["video"]["id"]
                    video_access_key = att_num["video"]["access_key"]
                    video_json_url = f"https://api.vk.com/method/video.get?videos=" \
                                     f"{video_owner_id}_{video_id}_{video_access_key}" \
                                     f"&access_token={token}&v=5.130"
                    req = requests.get(video_json_url)
                    res = req.json()
                    video_url = res["response"]["items"][0]["player"]
                    download_vid(url=video_url, post_id=post_id, vid_id=video_id,
                                 group_name=group_name)

                else:
                    print("Линка либо аудио либо ещё что. Упс)")
        else:
            print("Тут нет вкладки attachments. Упс)")
    except Exception as err:
        print(err)
        print(f"Something goes wrong with {post_id}. Oooops;)")

def get_wall_posts(group_name):
    """Делает запрос с методом wall.get, сохраняет файл json с id  двадцати последних постов
     выбранной группы вконтакте. Если файл уже существует, то дополняет id постов,
      которые ещё не были спарсены."""
    url = f'https://api.vk.com/method/wall.get?domain={group_name}' \
          f'&count=20&access_token={token}&v=5.130'
    req = requests.get(url)
    rez = req.json()

    # check if directory already exists:
    if os.path.exists(f'{group_name}'):
        print(f'The directory {group_name} already exists')
    else:
        os.mkdir(group_name)

    # Lets save json file
    with open(f'{group_name}/{group_name}.json', "w", encoding="utf-8") as f:
        json.dump(rez, f, indent=4, ensure_ascii=False)

    # Looking for new posts
    new_posts_id = []
    posts = rez['response']['items']
    for new_post in posts:
        new_posts_id.append(new_post["id"])

    # Проверим существует ли уже файл с id постов. Если не - отправляем все
    # посты. Если да - отправляем only new_posts
    if not os.path.exists(f'{group_name}/existed_posts_id.txt'):
        print("File with posts_id doesn't exist.Creating new...")
        with open(f'{group_name}/existed_posts_id.txt', "w") as f:
            for id in new_posts_id:
                f.write(str(id) + "\n")
        # Извлекаем данные из постов
        for post in posts:
            post_id = post["id"]
            print(f'Отправляем пост с id={post_id}')
            extracting_post(post=post, post_id=post_id, group_name=group_name)
    else:
        print("File with posts_id already exists. Adding new")
        existed_ids = []
        with open(f'{group_name}/existed_posts_id.txt', "r") as f:
            ids = str(f.read())
            ids_list = ids.split("\n")
            for num in ids_list[0:-1]:
                a = int(num)
                existed_ids.append(a)
        print(f'existed {existed_ids}')
        print(f'new {new_posts_id}')
        # Добавляем только те посты, которые ещё не были спарсены
        not_exist_ids = list(set(new_posts_id) - set(existed_ids))
        print(f'Вот id которых ещё не было: {not_exist_ids}')
        with open(f'{group_name}/existed_posts_id.txt', "a") as f:
            for _ in not_exist_ids:
                f.write(str(_)+"\n")
        # Извлекаем данные из постов
        for post in posts:
            post_id = post["id"]
            if post_id in not_exist_ids:
                print(f'Sending post with id={post_id}')
                extracting_post(post=post, post_id=post_id, group_name=group_name)
            else:
                print(f"Пост {post_id} уже был извлечён")


def main():
    group_name = input("Enter vk group name: ")
    get_wall_posts(group_name)


if __name__ == '__main__':
    main()
