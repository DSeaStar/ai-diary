import os
import time
import schedule
import pyautogui
from datetime import datetime
from PIL import Image
import openai
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

class AIDiary:
    def __init__(self):
        self.screenshots_dir = "screenshots"
        self.diary_dir = "diaries"
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

    def analyze_image(self, image_path):
        """使用OpenAI API分析图片内容"""
        try:
            with open(image_path, "rb") as image_file:
                response = openai.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "请详细描述这张图片中的内容，包括你看到的所有重要信息。"},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_file.read().hex()}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=500
                )
                return response.choices[0].message.content
        except Exception as e:
            print(f"Error analyzing image: {e}")
            return None

    def generate_diary(self, image_analysis):
        """生成日记内容"""
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的日记写作助手。请根据提供的图片分析内容，生成一篇优美的日记。"
                    },
                    {
                        "role": "user",
                        "content": f"请根据以下内容生成一篇日记：\n{image_analysis}"
                    }
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating diary: {e}")
            return None

    def save_diary(self, content):
        """保存日记内容"""
        if content:
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"{self.diary_dir}/diary_{timestamp}.txt"
            with open(filename, "a", encoding="utf-8") as f:
                f.write(f"\n=== {datetime.now().strftime('%H:%M:%S')} ===\n")
                f.write(content)
                f.write("\n")
            print(f"Diary saved: {filename}")

    def process_hourly(self):
        """每小时执行一次的处理流程"""
        print(f"Processing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        screenshot_path = self.take_screenshot()
        image_analysis = self.analyze_image(screenshot_path)
        if image_analysis:
            diary_content = self.generate_diary(image_analysis)
            self.save_diary(diary_content)

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