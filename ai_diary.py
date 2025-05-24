import os
import time
import schedule
import pyautogui
import requests
import base64
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api
from notion_client import Client

# 加载环境变量
load_dotenv()

class AIDiary:
    def __init__(self):
        self.screenshots_dir = "screenshots"
        self.diary_dir = "diaries"
        self.api_key = os.getenv('DOUBAO_API_KEY')
        if not self.api_key:
            raise ValueError("请在.env文件中配置DOUBAO_API_KEY")
        self.api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        self.model = "doubao-1-5-thinking-vision-pro-250428"
        
        # Cloudinary配置
        cloudinary.config(
            cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key = os.getenv('CLOUDINARY_API_KEY'),
            api_secret = os.getenv('CLOUDINARY_API_SECRET')
        )
        
        # Notion配置
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.notion_db_id = os.getenv('NOTION_DATABASE_ID')
        self.device_name = os.getenv('DEVICE_NAME', 'device1')
        self.notion = None
        if self.notion_token:
            self.notion = Client(auth=self.notion_token)
        
        self.create_directories()

    def create_directories(self):
        """创建必要的目录"""
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.diary_dir, exist_ok=True)

    def take_screenshot(self):
        """截取屏幕并保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot = pyautogui.screenshot()
        filename = f"{self.screenshots_dir}/screenshot_{timestamp}.png"
        screenshot.save(filename)
        print(f"Screenshot saved: {filename}")
        return filename

    def upload_to_cloudinary(self, image_path, max_retries=3):
        """上传图片到Cloudinary图床，带重试机制"""
        for attempt in range(max_retries):
            try:
                result = cloudinary.uploader.upload(
                    image_path,
                    folder="ai_diary",
                    resource_type="image"
                )
                return result['secure_url']
            except Exception as e:
                print(f"Upload attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # 等待2秒后重试
                else:
                    print("All upload attempts failed")
                    return None

    def analyze_image(self, image_path):
        """使用豆包大模型API分析图片内容"""
        try:
            # 上传图片到图床
            image_url = self.upload_to_cloudinary(image_path)
            if not image_url:
                print("Failed to upload image to Cloudinary")
                return None

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "这是一张我的屏幕截图，请用100字以内简明扼要地概述图片内容，并推测我当时可能在做什么。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error analyzing image: {e}")
            return None

    def generate_diary(self, image_analysis):
        """生成日记内容"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的日记写作助手。请根据提供的图片分析内容，生成一篇优美的日记。"
                    },
                    {
                        "role": "user",
                        "content": f"请根据以下内容生成一篇日记：\n{image_analysis}"
                    }
                ]
            }
            
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error generating diary: {e}")
            return None

    def save_to_notion(self, content, image_url):
        if not self.notion or not self.notion_db_id:
            print("Notion配置缺失，无法同步到Notion")
            return
        try:
            self.notion.pages.create(
                parent={"database_id": self.notion_db_id},
                properties={
                    "名称": {"title": [{"text": {"content": f"{self.device_name} 日记"}}]},
                    "今天": {"date": {"start": datetime.now().isoformat()}},
                    "内容": {"rich_text": [{"text": {"content": content}}]},
                    "图片URL": {"url": image_url}
                }
            )
            print("已同步到Notion")
        except Exception as e:
            print(f"同步到Notion失败: {e}")

    def save_diary(self, content, image_url=None):
        if content:
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"{self.diary_dir}/diary_{timestamp}.txt"
            with open(filename, "a", encoding="utf-8") as f:
                f.write(f"\n=== {datetime.now().strftime('%H:%M:%S')} ===\n")
                f.write(content)
                f.write("\n")
            print(f"Diary saved: {filename}")
            # 同步到Notion
            if image_url:
                self.save_to_notion(content, image_url)

    def process_hourly(self):
        """每小时执行一次的处理流程"""
        print(f"Processing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        screenshot_path = self.take_screenshot()
        image_url = self.upload_to_cloudinary(screenshot_path)
        if not image_url:
            print("Failed to upload image to Cloudinary")
            return
        image_analysis = self.analyze_image(screenshot_path)
        if image_analysis:
            self.save_diary(image_analysis, image_url)

def main():
    diary = AIDiary()
    
    # 设置每小时执行一次
    schedule.every().hour.at(":00").do(diary.process_hourly)
    
    print("AI Diary started. Press Ctrl+C to exit.")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main() 