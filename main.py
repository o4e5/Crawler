import os
import requests
import shutil
from multiprocessing import Pool
import argparse
from collect_links import CollectLinks
import imghdr
import base64
from pathlib import Path
import random


class Sites:
    GOOGLE = 1
    NAVER = 2
    GOOGLE_FULL = 3
    NAVER_FULL = 4

    @staticmethod
    def get_text(code):
        if code == Sites.GOOGLE:
            return 'Google'
        elif code == Sites.NAVER:
            return 'Naver'
        elif code == Sites.GOOGLE_FULL:
            return 'Google'
        elif code == Sites.NAVER_FULL:
            return 'Naver'

    @staticmethod
    def get_face_url(code):
        if code == Sites.GOOGLE or Sites.GOOGLE_FULL:
            return "&tbs=itp:face"
        if code == Sites.NAVER or Sites.NAVER_FULL:
            return "&face=1"


class AutoCrawler:
    def __init__(self, skip_already_exist=True, n_threads=4, do_google=True, do_naver=True, download_path='download',
                 full_resolution=False, face=False, no_gui=False, limit=0, proxy_list=None):

        self.skip = skip_already_exist
        self.n_threads = n_threads
        self.do_google = do_google
        self.do_naver = do_naver
        self.download_path = download_path
        self.full_resolution = full_resolution
        self.face = face
        self.no_gui = no_gui
        self.limit = limit
        self.proxy_list = proxy_list if proxy_list and len(proxy_list) > 0 else None

        os.makedirs('./{}'.format(self.download_path), exist_ok=True)

    @staticmethod
    def all_dirs(path):
        paths = []
        for dir in os.listdir(path):
            if os.path.isdir(path + '/' + dir):
                paths.append(path + '/' + dir)

        return paths

    @staticmethod
    def all_files(path):
        paths = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if os.path.isfile(path + '/' + file):
                    paths.append(path + '/' + file)

        return paths

    @staticmethod
    def get_extension_from_link(link, default='jpg'):
        splits = str(link).split('.')
        if len(splits) == 0:
            return default
        ext = splits[-1].lower()
        if ext == 'jpg' or ext == 'jpeg':
            return 'jpg'
        elif ext == 'gif':
            return 'gif'
        elif ext == 'png':
            return 'png'
        else:
            return default

    @staticmethod
    def validate_image(path):
        ext = imghdr.what(path)
        if ext == 'jpeg':
            ext = 'jpg'
        return ext

    @staticmethod
    def make_dir(dirname):
        current_path = os.getcwd()
        path = os.path.join(current_path, dirname)
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def get_keywords(keywords_file='keywords.txt'):
        with open(keywords_file, 'r', encoding='utf-8-sig') as f:
            text = f.read()
            lines = text.split('\n')
            lines = filter(lambda x: x != '' and x is not None, lines)
            keywords = sorted(set(lines))

        print('{} 키워드 확인 완료 : {}'.format(len(keywords), keywords))
        with open(keywords_file, 'w+', encoding='utf-8') as f:
            for keyword in keywords:
                f.write('{}\n'.format(keyword))

        return keywords

    @staticmethod
    def save_object_to_file(object, file_path, is_base64=False):
        try:
            with open('{}'.format(file_path), 'wb') as file:
                if is_base64:
                    file.write(object)
                else:
                    shutil.copyfileobj(object.raw, file)
        except Exception as e:
            print('저장 실패 - {}'.format(e))

    @staticmethod
    def base64_to_object(src):
        header, encoded = str(src).split(',', 1)
        data = base64.decodebytes(bytes(encoded, encoding='utf-8'))
        return data

    def download_images(self, keyword, links, site_name, max_count=0):
        self.make_dir('{}/{}'.format(self.download_path, keyword.replace('"', '')))
        total = len(links)
        success_count = 0

        if max_count == 0:
            max_count = total

        for index, link in enumerate(links):
            if success_count >= max_count:
                break

            try:
                print('키워드 {}을(를) {}로 다운로드 중 | {} / {} '.format(keyword, site_name, success_count + 1, max_count))

                if str(link).startswith('data:image/jpeg;base64'):
                    response = self.base64_to_object(link)
                    ext = 'jpg'
                    is_base64 = True
                elif str(link).startswith('data:image/png;base64'):
                    response = self.base64_to_object(link)
                    ext = 'png'
                    is_base64 = True
                else:
                    response = requests.get(link, stream=True)
                    ext = self.get_extension_from_link(link)
                    is_base64 = False

                no_ext_path = '{}/{}/{}_{}'.format(self.download_path.replace('"', ''), keyword, site_name,
                                                   str(index).zfill(4))
                path = no_ext_path + '.' + ext
                self.save_object_to_file(response, path, is_base64=is_base64)

                success_count += 1
                del response

                ext2 = self.validate_image(path)
                if ext2 is None:
                    print('읽을 수 없는 파일 - {}'.format(link))
                    os.remove(path)
                    success_count -= 1
                else:
                    if ext != ext2:
                        path2 = no_ext_path + '.' + ext2
                        os.rename(path, path2)
                        print('확장자 변경됨 : {} -> {}'.format(ext, ext2))

            except Exception as e:
                print('다운로드 실패 - ', e)
                continue

    def download_from_site(self, keyword, site_code):
        site_name = Sites.get_text(site_code)
        add_url = Sites.get_face_url(site_code) if self.face else ""

        try:
            proxy = None
            if self.proxy_list:
                proxy = random.choice(self.proxy_list)
            collect = CollectLinks(no_gui=self.no_gui, proxy=proxy)
        except Exception as e:
            print('크롬 드라이버를 불러오는 중 오류가 발생했습니다 - {}'.format(e))
            return

        try:
            print('링크 가져오는 중 : {} {} '.format(keyword, site_name))

            if site_code == Sites.GOOGLE:
                links = collect.google(keyword, add_url)

            elif site_code == Sites.NAVER:
                links = collect.naver(keyword, add_url)

            elif site_code == Sites.GOOGLE_FULL:
                links = collect.google_full(keyword, add_url)

            elif site_code == Sites.NAVER_FULL:
                links = collect.naver_full(keyword, add_url)

            else:
                print('올바르지 않은 DNS 코드')
                links = []

            print('수집된 링크에서 이미지 다운로드 중 :{} {}'.format(keyword, site_name))
            self.download_images(keyword, links, site_name, max_count=self.limit)
            Path('{}/{}/{}_done'.format(self.download_path, keyword.replace('"', ''), site_name)).touch()

            print('완료 {} : {}'.format(site_name, keyword))

        except Exception as e:
            print('예외 {}:{} - {}'.format(site_name, keyword, e))

    def download(self, args):
        self.download_from_site(keyword=args[0], site_code=args[1])

    def do_crawling(self):
        keywords = self.get_keywords()

        tasks = []

        for keyword in keywords:
            dir_name = '{}/{}'.format(self.download_path, keyword)
            google_done = os.path.exists(os.path.join(os.getcwd(), dir_name, 'google_done'))
            naver_done = os.path.exists(os.path.join(os.getcwd(), dir_name, 'naver_done'))
            if google_done and naver_done and self.skip:
                print('완료된 작업 건너뛰기 : {}'.format(dir_name))
                continue

            if self.do_google and not google_done:
                if self.full_resolution:
                    tasks.append([keyword, Sites.GOOGLE_FULL])
                else:
                    tasks.append([keyword, Sites.GOOGLE])

            if self.do_naver and not naver_done:
                if self.full_resolution:
                    tasks.append([keyword, Sites.NAVER_FULL])
                else:
                    tasks.append([keyword, Sites.NAVER])

        pool = Pool(self.n_threads)
        pool.map_async(self.download, tasks)
        pool.close()
        pool.join()
        print('작업이 끝났습니다.')

        self.imbalance_check()

        print('프로그램을 종료합니다')

    def imbalance_check(self):
        print('데이터 패키징 중 . . .')

        dict_num_files = {}

        for dir in self.all_dirs(self.download_path):
            n_files = len(self.all_files(dir))
            dict_num_files[dir] = n_files

        avg = 0
        for dir, n_files in dict_num_files.items():
            avg += n_files / len(dict_num_files)
            print('파일 위치 : {}, 파일 개수 : {}'.format(dir, n_files))

        dict_too_small = {}

        for dir, n_files in dict_num_files.items():
            if n_files < avg * 0.5:
                dict_too_small[dir] = n_files

        if len(dict_too_small) >= 1:
            print('데이터 밸런스가 맞지 않습니다.')
            print('아래 키워드는 평균 파일 수의 50% 미만입니다.')
            print('이 디렉토리를 제거하고 해당 키워드에 대해 다시 다운로드하는 것이 좋습니다.')
            print('_________________________________')
            print('너무 작은 파일 수 디렉토리 :')
            for dir, n_files in dict_too_small.items():
                print('위치 : {}, 파일 개수 : {}'.format(dir, n_files))

            print("위의 디렉토리 제거? (y/n)")
            answer = input()

            if answer == 'y':
                print("너무 작은 파일 수 디렉토리 제거 중...")
                for dir, n_files in dict_too_small.items():
                    shutil.rmtree(dir)
                    print('삭제함 : {}'.format(dir))

                print('이제 이 프로그램을 다시 실행하여 제거된 파일을 다시 다운로드하십시오. (with skip_already_exist=True)')
        else:
            print('데이터 불균형이 감지되었습니다.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip', type=str, default='true',
                        help='이전에 이미 다운로드한 키워드를 건너뜁니다. 다시 다운로드 시 필요합니다.')
    parser.add_argument('--threads', type=int, default=4, help='다운로드할 스레드 수입니다.')
    parser.add_argument('--google', type=str, default='true', help='Google.com에서 다운로드합니다.')
    parser.add_argument('--naver', type=str, default='true', help='Naver.com에서 다운로드합니다.')
    parser.add_argument('--full', type=str, default='false',
                        help='썸네일 대신 전체 해상도 이미지 다운로드 (느림) ')
    parser.add_argument('--face', type=str, default='false', help='페이스 검색 모드')
    parser.add_argument('--no_gui', type=str, default='auto',
                        help='GUI 모드가 없습니다. 전체 해상도 모드보다 느리지만 품질이 더 낫습니다.'
                             '그러나 썸네일 모드에서는 불안정합니다.'
                             'Default: "auto" - false if full=false, true if full=true')
    parser.add_argument('--limit', type=int, default=0,
                        help='사이트당 다운로드할 수 있는 최대 이미지 수입니다. (0: 무한)')
    parser.add_argument('--proxy-list', type=str, default='',
                        help='"socks://127.0.0.1:1080,http://127.0.0.1:1081"과 같이 쉼표로 구분된 프록시 목록 ". '
                             '모든 스레드는 목록에서 무작위로 하나를 선택합니다.')
    args = parser.parse_args()

    _skip = False if str(args.skip).lower() == 'false' else True
    _threads = args.threads
    _google = False if str(args.google).lower() == 'false' else True
    _naver = False if str(args.naver).lower() == 'false' else True
    _full = False if str(args.full).lower() == 'false' else True
    _face = False if str(args.face).lower() == 'false' else True
    _limit = int(args.limit)
    _proxy_list = args.proxy_list.split(',')

    no_gui_input = str(args.no_gui).lower()
    if no_gui_input == 'auto':
        _no_gui = _full
    elif no_gui_input == 'true':
        _no_gui = True
    else:
        _no_gui = False

    print(
        '옵션 - 스킵 :{}, 스레드 :{}, Google :{}, Naver :{}, 모든 파일 :{}, 페이스 :{}, 리미트 :{}, 서버 :{}, 프록시 :{}'
            .format(_skip, _threads, _google, _naver, _full, _face, _no_gui, _limit, _proxy_list))

    crawler = AutoCrawler(skip_already_exist=_skip, n_threads=_threads,
                          do_google=_google, do_naver=_naver, full_resolution=_full,
                          face=_face, no_gui=_no_gui, limit=_limit, proxy_list=_proxy_list)
    crawler.do_crawling()
