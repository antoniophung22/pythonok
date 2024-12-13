import os
import asyncio
import json
from playwright.async_api import async_playwright
import aiofiles
import random
from datetime import datetime
from PIL import Image
import shutil
import re

async def read_file(file_path):
    try:
        async with aiofiles.open(file_path, mode="r", encoding="utf-8") as f:
            data = await f.read()
        return data.split("\n")
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

def generate_single_title(file_name, phrases):
    file_name_without_extension = os.path.splitext(file_name)[0]
    
    if len(file_name_without_extension) >= 65:
        return file_name_without_extension

    remaining_length = 65 - len(file_name_without_extension)

    selected_phrases = []
    current_length = 0
    while phrases and current_length < remaining_length:
        word = random.choice(phrases)
        phrases.remove(word)  
        selected_phrases.append(word)
        current_length += len(word) + 1

    return f"{file_name_without_extension} - {' '.join(selected_phrases)}"
    
def get_files_from_folder(folder_path):
    supported_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"}
    files = [
        os.path.join(root, file_name)
        for root, _, file_names in os.walk(folder_path)
        for file_name in file_names
        if os.path.splitext(file_name)[1].lower() in supported_extensions
    ]
    return files


# Hàm chính
async def gen_listing(folder_path, profiles, value_to_match=None, phrases=None):
    
    print("\nSố lượng ACC: ",len(profiles))
    # print("Danh sach template: ",value_to_match)

    try:
        file_paths = [
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"))
        ]
        file_names = [os.path.splitext(os.path.basename(file))[0] for file in file_paths]
        print("Số lượng ảnh:", len(file_paths),"\n")
        # print("Tên ảnh:", file_names)

        if not file_paths:
            print(f"Tập tin không hợp lệ : {folder_path}")
            return

        # phrases = [
        #     "Perfect Gift for Her", "Vintage Graphic", "Soft Cotton", "Stylish Gift for Her",
        #     "Trendy Cotton with Graphic Print", "Unique T-Shirt Gift for Her", "Retro Design",
        #     "Soft Cotton Fabric", "Cool Gift for Him", "Streetwear Graphic", "100% Cotton",
        #     "Perfect Gift for Him", "HipHop Style Oversized", "Trendy Gift for Him",
        #     "Retro Graphic Tee", "Relaxed Fit", "Retro 90s Vintage", "Unisex Streetwear Style",
        #     "Vintage 90s Graphic Tee", "Soft Cotton", "Perfect for Retro Vibes", "Classic 90s Retro",
        #     "Unisex", "Comfortable Fit", "Graphic Design Cotton", "Bold Style", "Machine Washable",
        #     "Unique Design for Everyday Wear", "High-Quality Graphic Design", "Trendy Fit",
        #     "Perfect Gift for Fans", "Retro Graphic", "Street Style", "Ultimate Gift for Fans",
        #     "HipHop Graphic", "Comfy Cotton", "Vintage Tee for Fans", "Unisex Graphic Design",
        #     "Cotton Comfort", "Everyday Graphic Tee", "Cotton and Machine Washable",
        #     "Casual, Comfy, and Stylish", "Perfect Everyday Tee", "Weekend Vibes Only",
        #     "Lightweight and Breathable", "Essential", "Minimalist Graphic", "HipHop Style",
        #     "Modern Style", "Edgy Streetwear", "Pair with Anything", "Unique Graphic Print for Standout Styl",
        #     "Premium Comfort", "Cozy & Relaxed", "Comfortable Fit for All-Day Wear", "Sustainable Cotton",
        #     "Recycled Cotton Graphic", "Add Your Unique Twist", "Customizable",
        #     "Perfect for Active Days and Casual Style", "Great for On-the-Go Looks",
        #     "Graphic Tees for Him and Her", "Bold Style for Streetwear Lovers",
        #     "Trendy Graphic T-Shirt with Street Style", "Cool and Casual Urban Look",
        #     "Customizable Graphic", "Unique Graphic Tee You Can Customize", "Trendy, Viral, and On-Point",
        #     "Stylish Tee for Everyday Looks", "Adventure Tee for Outdoor Enthusiasts",
        #     "Comfy T-Shirt for Nature Lovers", "Cozy Graphic T-Shirt for Chilly Days",
        #     "Bold T-Shirt for Night Out Vibes", "Lightweight, Soft, and Stylish"
        # ]

        
        if not value_to_match:
            print("Template không hợp lệ. Sử dụng mặc định template ao 1 mat")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()

            page = await context.new_page()
            await page.goto("https://apps.tiksuccess.com/login")
            await page.fill("input[name='username']", "vuthuc@kbt.global")
            await page.wait_for_timeout(2000)
            await page.fill("input[name='password']", "Nothing1987@")
            await page.wait_for_timeout(2000)
            await page.click("button[type='submit']")
            await page.wait_for_timeout(3000)

            profile_tasks = []
            for profile, match_value in zip(profiles, value_to_match):
                # print(f"Processing profile: {profile} with value: {match_value}")
                profile_tasks.append(
                    handle_profile(context, profile, file_names, file_paths, phrases, match_value)
                )
            await asyncio.gather(*profile_tasks)
            
            now = datetime.now()
            current_today = now.strftime("%d-%m-%Y")
            current_time = now.strftime("%H:%M")
            print("\nĐã List xong!!!!")
            for profile in profiles: 
                print(profile)
            print(f"Thời Gian List : \n Ngày {current_today} \n Giờ: {current_time}")
    except Exception as e:
        print(f"An error occurred: {e}")

async def handle_profile(context, profile, file_names, file_paths, phrases, value_to_match):
    
    
    page = await context.new_page()
    await page.goto("https://apps.tiksuccess.com/quan-ly-listing")
    await page.wait_for_timeout(12000)

    await page.fill("input#shop_id", profile)
    await page.wait_for_timeout(2000)
    await page.keyboard.press("Enter")
    await page.wait_for_timeout(5000)

    spin_container = await page.query_selector(".ant-spin-container")
    if spin_container:
        ul_element = await spin_container.query_selector("ul")

        if ul_element:
            await page.wait_for_selector("table tr th:nth-child(1) span")
            await page.click("table tr th:nth-child(1) span")
            await page.wait_for_timeout(2000)

            await page.wait_for_selector("button.ant-btn.css-1pg9a38.ant-btn-primary.ant-btn-lg.ant-btn-dangerous span:has-text('Xóa')")
            await page.click("button.ant-btn.css-1pg9a38.ant-btn-primary.ant-btn-lg.ant-btn-dangerous span:has-text('Xóa')")
            await page.wait_for_timeout(2000)

            await page.wait_for_selector(".ant-popconfirm-buttons button.ant-btn.css-1pg9a38.ant-btn-primary.ant-btn-sm span:has-text('Yes')")
            await page.click(".ant-popconfirm-buttons button.ant-btn.css-1pg9a38.ant-btn-primary.ant-btn-sm span:has-text('Yes')")

            await page.wait_for_timeout(2000)
            print("XOA LIST NHAP THANH CONG!!!")
        else:
            print("KHONG CO LIST NHAP NAO!!!!")

    await page.click("span:has-text('Tạo mới Listing')")
    await page.wait_for_timeout(2000)

    await page.fill("input#CreateListing_number_sku", str(len(file_names)))
    await page.wait_for_timeout(2000)

    await page.click("input#CreateListing_product_id")
    await page.wait_for_timeout(2000)

    dropdown_locator = page.locator(".ant-select-dropdown.css-1pg9a38.ant-select-dropdown-placement-bottomLeft")
    options = dropdown_locator.locator(".ant-select-item.ant-select-item-option")
    count = await options.count()

    
    matched = False
    for i in range(count):
        option = options.nth(i)
        title = await option.get_attribute("title")
        if title and title.upper() == value_to_match.upper():
            print("Đang tạo listing cho:",title)
            await option.click()
            matched = True
            break

    if not matched:
        print(f"Không tìm thấy tùy chọn nào khớp với giá trị: {value_to_match}. Đóng tab lại.")
        await page.close()
        return

    await page.fill("input#CreateListing_quantity", "10")
    await page.wait_for_timeout(2000)
    await page.click("span:has-text('Tạo Listing')")
    await page.wait_for_timeout(4000)

    for i, (file_name, file_path) in enumerate(zip(file_names, file_paths)):
        if "thumbs" in file_name.lower():
            continue

        try:
            await page.click(f"tbody tr:nth-child({i + 2}) span[title='Edit Listing']")
        except Exception as e:
            print(f"Error editing listing: {e}")    
        await page.wait_for_timeout(3000)
        await page.set_input_files(
            f"tbody tr:nth-child({i + 2}) .ant-upload-list.ant-upload-list-picture-circle input",
            file_path
        )
        await page.wait_for_timeout(3000)

        generated_title = generate_single_title(file_name, phrases)

        await page.fill(f"tbody tr:nth-child({i + 2}) textarea#product_name", generated_title)
        await page.wait_for_timeout(2000)

        await page.click(f"tbody tr:nth-child({i + 2}) span b:has-text('Save')")
        await page.wait_for_timeout(3000)


    await page.click("table tr th:nth-child(1) span")
    await page.wait_for_timeout(2000)

    await page.click("button.ant-btn.css-1pg9a38.ant-btn-primary.ant-btn-lg span:has-text('Đăng SP')")
    await page.wait_for_timeout(2000)

    await page.click(".ant-popconfirm-buttons button.ant-btn.css-1pg9a38.ant-btn-primary.ant-btn-sm span:has-text('Yes')")
    await page.wait_for_timeout(2000)

async def load_config(file_path):
    try:
        async with aiofiles.open(file_path, mode="r", encoding="utf-8") as f:
            data = await f.read()
        return json.loads(data)
    except Exception as e:
        print(f"Error reading config file: {e}")
        return {}
def convert_images_to_jpg_and_delete_original(folder_path):
    filtered_folder = os.path.join(folder_path, "ERROR")
    os.makedirs(filtered_folder, exist_ok=True)

    files = get_files_from_folder(folder_path)
    print(f"Đang chuyển đổi sang JPG và lọc ảnh!")

    # Các mảng từ cấm
    banned_words_to_delete = [
        "free shipping",
        "comfort colors®",
        "comfort colors",
        "comfort color",
         "kids",
    "Kid",
    "kid",
    "youth",
    "toddle"
    ]
    banned_words_to_replace = {
        "tiktok": "",
        "tik tok": "",
        "tiktokshop": "",
        "tik tok shop": "",
        "MLB":"",
        "NFL":"",
        "NBA":"",
        "Rams":"",
        "Dallas":"",
        "Dolphins":"",
        "49ers":"",
        "Falcons":"",
        "Bulls":"",
        "Yankees":"",
        "Suns":"",
        "Ravens":"",
        "Dodgers":"",
        "Bucks":"",
        "Pistons":"",
        "76ers":"",
        "Los Angeles Rams":"Los Angeles",
        "Dallas Cowboys":"Cowboys",
        "Miami Dolphins":"Miami",
        "San Francisco 49ers":"San Francisco",
        "Atlanta Falcons":"Atlanta",
        "Chicago Bulls":"Chicago",
        "New York Yankees":"New York",
        "Phoenix Suns":"Phonenix",
        "Baltimore Ravens":"Baltimore",
        "Los Angeles Dodgers":"Los Angeles",
        "Milwaukee Bucks":"Milwaukee",
        "Detroit Pistons":"Detroit",
        "Tom & Jerry":"Tom and Jerry",
        "Philadelphia 76ers":"Philadelphia",
    



        
    }
    banned_words_to_move = [
        "disney",
        "embroidered"
    ]
    
    # Biểu thức regex
    delete_pattern = re.compile(r'\b(' + '|'.join(re.escape(word) for word in banned_words_to_delete) + r')\b', flags=re.IGNORECASE)
    replace_pattern = re.compile("|".join(re.escape(key) for key in banned_words_to_replace.keys()), re.IGNORECASE)
    for file_path in files:
        try:
            file_name = os.path.basename(file_path)

            # Xóa các từ trong mảng "delete"
            if delete_pattern.search(file_name):
                new_file_name = delete_pattern.sub("", file_name).strip()
                new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)
                os.rename(file_path, new_file_path)
                print(f"Đã xóa từ bị cấm: {file_name}")
                file_path = new_file_path
            
            # Thay thế các từ trong mảng "replace"
            if replace_pattern.search(file_name):
                new_file_name = replace_pattern.sub(lambda m: banned_words_to_replace[m.group(0).lower()], file_name).strip()
                new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)
                os.rename(file_path, new_file_path)
                print(f"Đã thay thế từ bị cấm: {file_name} -> {new_file_name}")
                file_path = new_file_path
            
            # Di chuyển file nếu chứa từ trong mảng "move"
            if any(word in file_name.lower() for word in banned_words_to_move):
                shutil.move(file_path, os.path.join(filtered_folder, file_name))
                print(f"Từ bị cấm. Đã di chuyển ảnh vào thư mục ERROR: {file_name}")
                continue

            # Xử lý ảnh
            with Image.open(file_path) as img:
                img = img.convert("RGB")  
                width, height = img.size
                
                # Kiểm tra kích thước
                if width < 530 or height < 530:
                    print(f"Di chuyển ảnh kích thước nhỏ: {file_path}")
                    shutil.move(file_path, os.path.join(filtered_folder, file_name))
                    continue
                
                # Nén ảnh nếu chiều cao >= 1200px
                if height >= 1300:
                    random_size = random.randint(1000, 1200)
                    print(f"Đã nén xuống: {random_size}px")
                    target_size = (random_size, random_size)
                else:
                    target_size = (width, height)
                
                # Lưu ảnh JPG
                temp_path = os.path.splitext(file_path)[0] + "_temp.jpg"
                img_resized = img.resize(target_size)
                img_resized.save(temp_path, "JPEG")
                os.replace(temp_path, file_path)

        except Exception as e:
            print(f"Lỗi xử lý ảnh {file_path}: {e}")
    print(f"Xử lý ảnh hoàn tất!")  
# Hàm chính
async def main():
   
    folder_path = r"C:\Users\ADMIN\Pictures\MOCKUP\SPORT\T SHIRT 1 MAT\NHÓM 7\13.12\1"
    convert_images_to_jpg_and_delete_original(folder_path)
    if not os.path.isdir(folder_path):
        print(f"Đường dẫn không hợp lệ hoặc không có ảnh: {folder_path}")
        return

    config = await load_config("config.json")
    if not config:
        print("Không thể tải cấu hình. Đang thoát.")
        return

    phrases = config[2].get("Phrases", [])
    if not phrases:
        print("Lỗi không tìm thay phrases .")
        return

    groups = config[0].get("Groups", [])
    if not groups:
        print("Không có nhóm nào trong cấu hình.")
        return
    
    

    print("\nChọn nhóm:")
    for i, group in enumerate(groups):
        print(f"{i + 1}. {group['name']}")
    
    name_choice = -1
    while name_choice < 0 or name_choice >= len(groups):
        try:
            name_choice = int(input(f"Nhập số (1 - {len(groups)}): ")) - 1
            if name_choice < -1 or name_choice >= len(groups):
                print("Lựa chọn không hợp lệ. Vui lòng chọn lại.")
        except ValueError:
            print("Lựa chọn không hợp lệ. Vui lòng nhập số hợp lệ.")

    selected_group = groups[name_choice]
    selected_name = selected_group["name"]

    print(f"\nChọn nhom list cho - {selected_name}:")
    data = selected_group.get("data", [])
    titles = [
        f"{group['title']} - {group['niche']}" for group in data
    ]
    columns = [title.split(" - ") for title in titles]
    header = "+----------+----------+"
    rows = [header]
    rows.append(f"| {'Nhóm':<8} | {'Niche':<8} |")
    rows.append(header)
    for nhom, niche in columns:
        rows.append(f"| {nhom:<8} | {niche:<8} |")
        rows.append(header)
    print("\n".join(rows))
    
    title_choice = -1
    while title_choice < 0 or title_choice >= len(titles):
        try:
            title_choice = int(input(f"\nNhập số (1 - {len(titles)}): ")) - 1
            if title_choice < -1 or title_choice >= len(titles):
                print("Lựa chọn không hợp lệ. Vui lòng chọn lại.")
        except ValueError:
            print("Lựa chọn không hợp lệ. Vui lòng nhập số hợp lệ.")

    selected_title_niche = titles[title_choice]
    selected_title, selected_niche = selected_title_niche.split(" - ")

    profiles = [
        group["profiles"]
        for group in data
        if group["title"] == selected_title and group["niche"] == selected_niche
    ]
    profiles = profiles[0] if profiles else []

    print("Danh sach profiles se list!!!")
    for i, profile in enumerate(profiles):
        print(f"{i + 1}. {profile}")

    print(f"\nChọn template cho {selected_title} - {selected_niche}:")
    templates = [
        template
        for group in data
        if group["title"] == selected_title and group["niche"] == selected_niche
        for template in group.get("templates", [])
    ]
    if not templates:
        print("Không tìm thấy template phù hợp. Exiting.")
        return
    
    for i, template in enumerate(templates):
        print(f"{i + 1}. {template}")

    template_choice = -1
    while template_choice < 0 or template_choice >= len(templates):
        try:
            template_choice = int(input(f"Nhập số (1 - {len(templates)}): ")) - 1
            if template_choice < -1 or template_choice >= len(templates):
                print("Lựa chọn không hợp lệ. Vui lòng chọn lại.")
        except ValueError:
            print("Lựa chọn không hợp lệ. Vui lòng nhập số hợp lệ.")

    selected_template = templates[template_choice]
    if selected_template == "" or selected_template == "default":
        value_to_match = [f"{profile}".strip().upper() for profile in profiles]
    else: 
        value_to_match = [f"{profile} {selected_template}".strip().upper() for profile in profiles]


    await gen_listing(folder_path, profiles, value_to_match,phrases)

if __name__ == "__main__":
    asyncio.run(main())