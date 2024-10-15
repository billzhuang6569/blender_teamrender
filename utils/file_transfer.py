import aiohttp
import asyncio
import os
from tqdm import tqdm
import zipfile
import io
import requests

async def upload_batch(url, file_paths):
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        total_size = sum(os.path.getsize(fp) for fp in file_paths)
        
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Uploading") as pbar:
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                data.add_field('files', open(file_path, 'rb'), filename=file_name)
                pbar.update(os.path.getsize(file_path))
        
        async with session.post(url, data=data, ssl=False) as response:  # 生产环境中应验证SSL证书
            result = await response.json()
            return result

async def download_batch(url, file_names, output_dir):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={'files': file_names}, ssl=False) as response:  # 生产环境中应验证SSL证书
            if response.status == 200:
                content = await response.read()
                zip_file = io.BytesIO(content)
                
                with zipfile.ZipFile(zip_file) as zf:
                    total_size = sum(zf.getinfo(name).file_size for name in zf.namelist())
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc="Extracting") as pbar:
                        for file in zf.infolist():
                            zf.extract(file, output_dir)
                            pbar.update(file.file_size)
            else:
                print(f"Download failed with status code: {response.status}")

async def main():
    server_url = 'https://your-server.com'
    
    # 上传示例
    upload_files = ['path/to/file1.png', 'path/to/file2.png', 'path/to/file3.png']
    upload_result = await upload_batch(f'{server_url}/upload_batch', upload_files)
    print("Upload result:", upload_result)
    
    # 下载示例
    download_files = ['file1.png', 'file2.png', 'file3.png']
    await download_batch(f'{server_url}/download_batch', download_files, 'path/to/output/directory')

if __name__ == "__main__":
    asyncio.run(main())

def upload_file(file_path, url, data=None):
    try:
        with open(file_path, 'rb') as file:
            files = {'file': file}
            response = requests.post(url, files=files, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return False

def download_file(url, local_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(local_path, 'wb') as file:
                file.write(response.content)
            return True
        else:
            print(f"Failed to download file. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return False