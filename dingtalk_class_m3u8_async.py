from Crypto.Cipher import AES
import requests_async as requests
import aiofiles
import m3u8
import os, sys
import asyncio

# class_video_name = sys.argv[1]
class_video_name = "Teasync"
# m3u8_file_uri = sys.argv[2]
m3u8_file_uri = 'https://dtliving-sz.dingtalk.com/live_hp/50c76578-f922-48cd-a3e8-0c789a14248d_merge.m3u8?app_type=mac&auth_key=1627431132-0-0-3ffe8c22fb3aa0c7883db7a53a05de5d&cid=3f50c462bbd1b19733455dff4addb7e3&token=3fec44afc70cc00a65b4d378dc52a520OlunyFPNJ6IUJwA2HDEU8To5wezU_-DqtAB5r2rNRHqFi4Fc-ebSUSe8g0RPgMygY9wbEShiXmx728T0ikwfT7IT1yEoAqVGnBNJx12_ehg=&token2=ed619b628a7e774c93bdabef7bc053cerTCNQru0YJ49PlMzblg202aMXn1urxkDApmB_Xg2-1j_1k5PWJ2XEHnHg2mL-KVCoFkvCQ9GA8N3yzd5OhFePzop4g76YfaBe-kvKJqgkYU&version=5.1.40'
prefix_request_url = f'{m3u8_file_uri.rsplit("/", 1)[0]}/'

headers={'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_16_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36 DingTalk(5.1.40-macOS-macOS-MAS-14354546) nw Channel/201200'}

async def download_m3u8_video(index: int, suffix_url: str):
    if not os.path.exists(f'{class_video_name}/downloads/{index}.ts'):
        i = 0
        while i < 10:
            try:
                await asyncio.sleep(i)
                download_video_ts = await requests.get(url=prefix_request_url + suffix_url,headers=headers, timeout=60)
                assert download_video_ts
                with open(f'{class_video_name}/downloads/{index}.ts', "wb") as ts:
                    ts.write(download_video_ts.content)
                print(f'[{class_video_name}]——已下载第 {index} 个片段/ 共 {len(playlist.files)} 个片段')
                return
            except requests.exceptions.RequestException:
                print(f'[{class_video_name}]——下载超时，正在重新下载第 {index} 个片段/ 共 {len(playlist.files)} 个片段')
            except AssertionError:
                pass
            finally:
                i += 1


async def download_m3u8_all():
    print(f'[{class_video_name}]——已开始下载，请稍后……')
    if not os.path.exists(class_video_name + '/downloads'):
        os.makedirs(class_video_name + '/downloads')
    download_async_list = [asyncio.create_task(download_m3u8_video(i, video_suffix_url))
                           for i, video_suffix_url in enumerate(playlist.files, 1)]
    await asyncio.wait(download_async_list)

    download_encrypt_list = [uri for uri in os.listdir(f'{class_video_name}/downloads') if uri[0] != '.']
    if len(download_encrypt_list) == len(playlist.files):  # 判断是否有漏下的分段视频没有下载
        print(f'[{class_video_name}]——视频全部下载完成')
        return download_encrypt_list
    else:  # 有部分视频在三次重试后依旧没有下载成功
        print(f'[{class_video_name}]——下载过程中出现问题，正在重试...')
        return await download_m3u8_all()


def merge_m3u8_all():
    with open(f'{class_video_name}/{class_video_name}.mp4', 'ab') as final_file:
        print(f'[{class_video_name}]——开始拼接下载的分段视频')
        temp_file_uri_list = [uri for uri in os.listdir(f'{class_video_name}/downloads') if uri[0] != '.']
        temp_file_uri_list.sort(key=lambda x: int(x[:-3]))
        for uri in temp_file_uri_list:
            # if uri[0] == '.': continue  # 忽略隐藏文件
            with open(f'{class_video_name}/downloads/{uri}', 'rb') as temp_file:
                final_file.write(temp_file.read())  # 将ts格式分段视频追加到完整视频文件中
        print(f'[{class_video_name}]——合成视频成功')
        print(f'[{class_video_name}]——视频文件:{os.getcwd()}/{class_video_name}/{class_video_name}.mp4')

def merge_m3u8_ffmpeg():
    with open(f'{class_video_name}/list.txt', 'w+') as list_file:
        print(f'[{class_video_name}]——开始生成合并列表清单',end="...")
        temp_file_uri_list = [uri for uri in os.listdir(f'{class_video_name}/downloads') if uri[0] != '.']
        temp_file_uri_list.sort(key=lambda x: int(x[:-3]))
        for uri in temp_file_uri_list:
            list_file.writelines(f"file downloads/{uri}\n")
        print('已生成')
        print('使用ffmpeg合成视频文件')
        os.chdir(f'{class_video_name}')
        os.popen('ffmpeg -y -loglevel info -f concat -i list.txt -acodec copy -vcodec copy output.mp4')
        print(f'[{class_video_name}]——视频文件:{os.getcwd()}/output.mp4')


if __name__ == '__main__':
    playlist = m3u8.load(m3u8_file_uri, verify_ssl=False)
    asyncio.run(download_m3u8_all())
    merge_m3u8_all()

    # merge_m3u8_ffmpeg()
