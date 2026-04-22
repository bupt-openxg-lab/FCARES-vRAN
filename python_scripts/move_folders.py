import os
import json
import shutil
import argparse

# 解析命令行参数
parser = argparse.ArgumentParser(description='根据 summary.json 的 status 移动文件夹')
parser.add_argument('--runs_dir', type=str, default='/home/bupt/wlh/ran/automation/automation/batches/20260409_093004_night_30runs/runs', help='runs 文件夹的路径')
args = parser.parse_args()

runs_dir = args.runs_dir
success_dir = os.path.join(runs_dir, 'success')
fail_dir = os.path.join(runs_dir, 'fail')

# 创建 success 和 fail 目录（如果不存在）
os.makedirs(success_dir, exist_ok=True)
os.makedirs(fail_dir, exist_ok=True)

# 遍历 runs 目录下的子文件夹
for folder in os.listdir(runs_dir):
    folder_path = os.path.join(runs_dir, folder)
    if os.path.isdir(folder_path) and folder not in ['success', 'fail']:
        summary_path = os.path.join(folder_path, 'summary.json')
        if os.path.exists(summary_path):
            try:
                with open(summary_path, 'r') as f:
                    data = json.load(f)
                status = data.get('status')
                if status == 'ok':
                    shutil.move(folder_path, os.path.join(success_dir, folder))
                    print(f"移动 {folder} 到 success")
                elif status == 'failed':
                    shutil.move(folder_path, os.path.join(fail_dir, folder))
                    print(f"移动 {folder} 到 fail")
                else:
                    print(f"跳过 {folder}：status 为 {status}")
            except Exception as e:
                print(f"处理 {folder} 时出错：{e}")
        else:
            print(f"跳过 {folder}：summary.json 不存在")

print("处理完成")