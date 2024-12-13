import os
import asyncio
import json
from playwright.async_api import async_playwright
import aiofiles
from datetime import datetime

# Hàm tải cấu hình từ tệp JSON
async def load_config(file_path):
    try:
        async with aiofiles.open(file_path, mode="r", encoding="utf-8") as f:
            data = await f.read()
        return json.loads(data)
    except Exception as e:
        print(f"Error reading config file: {e}")
        return {}

def display_and_select_config(config):
    names = [item['name'] for item in config[0]['Groups']]

    print("\n=== Danh sách Name ===")
    for i, name in enumerate(names):
        print(f"{i + 1}. {name}")
    
    name_choice = int(input("\nChọn Name (Nhập số): ")) - 1
    selected_name = names[name_choice] if 0 <= name_choice < len(names) else names[0]

    selected_group = None
    for group_data in config[0]['Groups']:
        if group_data['name'] == selected_name:
            selected_group = group_data
            break

    if not selected_group:
        print("Không tìm thấy nhóm cho Name đã chọn.")
        return None, None, None, None

    groups = selected_group.get("data", [])
    if not groups:
        print("Không có nhóm nào trong Name đã chọn.")
        return None, None, None, None

    print("\n=== Danh sách Nhóm ===")
    for i, group in enumerate(groups):
        print(f"{i + 1}. {group['title']}")
    
    group_choice = int(input("\nChọn Nhóm (Nhập số): ")) - 1
    selected_group = groups[group_choice] if 0 <= group_choice < len(groups) else groups[0]

    profiles = selected_group.get("profiles", [])
    if not profiles:
        print("Không có profiles nào trong nhóm.")
        return None, None, None, None

    print("\n=== Danh sách Profiles ===")
    for i, profile in enumerate(profiles):
        print(f"{i + 1}. {profile}")
    
    selected_profiles = input("\nNhập số thứ tự của Profiles cần chọn (phân cách bằng dấu phẩy, để trống để chọn tất cả): ").strip()

    if selected_profiles:
        selected_profiles = [
            profiles[int(i) - 1] for i in selected_profiles.split(",") if 0 < int(i) <= len(profiles)
        ]
    else:
        selected_profiles = profiles

    # Hiển thị danh sách templates
    templates = config[1].get("Templates", [])
    print("\n=== Danh sách Templates ===")
    for i, template in enumerate(templates):
        print(f"{i + 1}. {template}")
    
    template_choice = int(input("\nChọn Template (Nhập số): ")) - 1
    selected_template = templates[template_choice] if 0 <= template_choice < len(templates) else templates[0]

    # Hiển thị lựa chọn mô tả
    descriptions = ["mô tả", "sweatshirt and hoodie"]
    print("\n=== Lựa chọn Description ===")
    for i, desc in enumerate(descriptions):
        print(f"{i + 1}. {desc}")
    desc_choice = int(input("\nChọn Description (Nhập số): ")) - 1
    selected_description = descriptions[desc_choice] if 0 <= desc_choice < len(descriptions) else descriptions[0]

    price = selected_template

    return selected_group, selected_profiles, selected_description, price

# Hàm lấy tất cả các tệp hình ảnh và lọc các tệp theo yêu cầu
def get_image_files(folder_path):
    image_files = []
    other_files = []

    for root, _, file_names in os.walk(folder_path):
        for file_name in file_names:
            base_name, ext = os.path.splitext(file_name)
            if ext.lower() in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"]:
                if base_name in ["1", "2", "3", "4", "5", "Size Chart"]:
                    image_files.append(os.path.join(root, file_name))
                else:
                    other_files.append(os.path.join(root, file_name))
    return image_files, other_files

# Hàm tải ảnh và thông tin lên
async def upload_images_to_profile(context, profile, image_files, other_files, size_chart_file, template_names, description, price):
    page = await context.new_page()
    await page.goto("https://apps.tiksuccess.com/quan-ly-template")
    await page.wait_for_timeout(8000)

    await page.fill("input#CreateProductTemplate_template_name", template_names)
    await page.wait_for_timeout(2000)
    await page.keyboard.press("Enter")
    await page.click("input#CreateProductTemplate_shop_ids")
    await page.keyboard.insert_text(profile)
    await page.wait_for_timeout(5000)
    await page.keyboard.press("Enter")
    await page.click("body")
    await page.wait_for_timeout(4000)

    for file_path in image_files:
        try:
            await page.set_input_files("#CreateProductTemplate_images", file_path)
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Error uploading image {file_path}: {e}")
            continue

    try:
        if other_files:
            await page.fill("#CreateProductTemplate_title", os.path.splitext(os.path.basename(other_files[0]))[0])
            await page.wait_for_timeout(2000)

        await page.set_input_files("#CreateProductTemplate_size_chart", size_chart_file)
        await page.wait_for_timeout(2000)

        await page.fill("#CreateProductTemplate_description_template_id", description)
        await page.wait_for_timeout(2000)
        await page.keyboard.press("Enter")
        await page.fill("#CreateProductTemplate_price_template_id", price)
        await page.wait_for_timeout(2000)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(5000)

        await page.locator("button.ant-btn.css-1pg9a38.ant-btn-primary.ant-btn-lg").nth(1).click()
        await page.wait_for_timeout(5000)



    except Exception as e:
        print(f"Error uploading data: {e}")
    finally:
        await page.close()

async def gen_listing(folder_path, profiles, template_names, description, price):
    image_files, other_files = get_image_files(folder_path)
    if len(image_files) < 5:
        print("Không đủ các tệp hợp lệ cho ảnh! (1-5, size chart)")
        return

    size_chart_file = image_files[-1]
    image_files = image_files[:-1]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        page = await context.new_page()
        await page.goto("https://apps.tiksuccess.com/login")
        await page.wait_for_timeout(2000)
        await page.fill("input[name='username']", "vuthuc@kbt.global")
        await page.wait_for_timeout(2000)
        await page.fill("input[name='password']", "Nothing1987@")
        await page.wait_for_timeout(2000)
        await page.click("button[type='submit']")
        await page.wait_for_timeout(3000)

        tasks = [
            upload_images_to_profile(
                context, profile, image_files, other_files, size_chart_file, template_name, description, price
            )
            for profile, template_name in zip(profiles, template_names)
        ]
        await asyncio.gather(*tasks)
        await browser.close()

    now = datetime.now()

    print(f"\nUpload completed at: {now.strftime('%d-%m-%Y %H:%M:%S')}")

# Hàm chính
async def main():
    folder_path = r"C:\Users\ADMIN\Pictures\TEMPLATE\T-Shirt"
    config_path = "config.json"

    if not os.path.isdir(folder_path):
        print(f"Thư mục không hợp lệ hoặc không tồn tại: {folder_path}")
        return

    config = await load_config(config_path)
    if not config:
        print("Không thể tải cấu hình. Đang thoát.")
        return

    selected_group, profiles, description, price = display_and_select_config(config)
    if not profiles:
        return

    template_names = [f"{profile} {price}".strip().upper() for profile in profiles]
    print("Template names for selected profiles:", template_names)

    await gen_listing(folder_path, profiles, template_names, description, price)

if __name__ == "__main__":
    asyncio.run(main())
