import os
import csv
import django

# 1. 初始化 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anilib_project.settings') # 記得改成你的專案名稱
django.setup()

from ani.models import Ani, Studio, Creator, Tag

def run_import():
    file_path = 'notion_data.csv'
    
    if not os.path.exists(file_path):
        print(f"❌ 找不到檔案: {file_path}，請確認檔案已放在根目錄。")
        return

    with open(file_path, mode='r', encoding='utf-8-sig') as f: # 使用 utf-8-sig 處理 Excel 可能產生的 BOM
        reader = csv.DictReader(f)
        for row in reader:
            # 2. 處理基礎欄位
            # get_or_create 會根據 title 判斷，若重複則回傳既有物件，不重複則新建
            ani_obj, created = Ani.objects.get_or_create(
                title=row['title'],
                defaults={
                    'IMDb_ID': row.get('IMDb_ID', ''),
                    'title_ch': row.get('title_ch', ''),
                    'title_zh': row.get('title_zh', ''),
                    'year': int(row['year']) if row.get('year') and row['year'].isdigit() else None,
                    'imdb_stars': float(row['imdb_stars']) if row.get('imdb_stars') and row['imdb_stars'] != '' else None,
                    'rating': row.get('rating', ''),
                }
            )

            # 3. 處理「Studio」關聯 (自動建立並連結)
            if row.get('Studio'):
                studio_names = [s.strip() for s in row['Studio'].split(',')]
                for s_name in studio_names:
                    if s_name: # 確保名稱不是空的
                        s_obj, _ = Studio.objects.get_or_create(name=s_name)
                        ani_obj.studio.add(s_obj)

            # 4. 處理「creator」關聯
            if row.get('creator'):
                creator_names = [c.strip() for c in row['creator'].split(',')]
                for c_name in creator_names:
                    if c_name:
                        c_obj, _ = Creator.objects.get_or_create(name=c_name)
                        ani_obj.creators.add(c_obj)

            if created:
                print(f"✅ 新增: {ani_obj.title}")
            else:
                print(f"ℹ️ 更新: {ani_obj.title}")

if __name__ == "__main__":
    run_import()
    print("✨ 任務完成！你的 ANiLib 資料庫已更新。")