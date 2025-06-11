from typing import Final
import os
import time
from dotenv import load_dotenv
from discord import Intents, Client, Message
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables
load_dotenv()

# Configuration
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")
INSTAGRAM_USERNAME: Final[str] = os.getenv("INSTA_USERNAME")
INSTAGRAM_PASSWORD: Final[str] = os.getenv("INSTA_PASSWORD")
TARGET_USERNAME: Final[str] = os.getenv("TARGET_USERNAME")

# Discord Setup
intents: Intents = Intents.default()
intents.message_content = True
client = Client(intents=intents)


class InstagramBot:
    def __init__(self, username: str, password: str):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Initialize WebDriver using webdriver-manager to auto-manage the ChromeDriver version
        service = Service(ChromeDriverManager().install())
        self.browser = webdriver.Chrome(service=service, options=options)
        self.username = username
        self.password = password

    def log_in(self) -> None:
        """Handle Instagram login with improved reliability"""
        try:
            self.browser.get("https://www.instagram.com/accounts/login/")

            # Wait for login fields
            username_field = WebDriverWait(self.browser, 20).until(
                EC.element_to_be_clickable((By.NAME, "username"))
            )
            password_field = WebDriverWait(self.browser, 20).until(
                EC.element_to_be_clickable((By.NAME, "password"))
            )

            # Enter credentials
            username_field.send_keys(self.username)
            password_field.send_keys(self.password)

            # Click login button
            WebDriverWait(self.browser, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            ).click()

            time.sleep(5)  # Wait for login completion

        except TimeoutException as e:
            raise Exception(f"Login failed: {str(e)}")

    def bypass_popups(self) -> None:
        """Handle all post-login popups"""
        try:
            # "Save Info" popup
            WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Save Info')]"))
            ).click()
            time.sleep(1)
        except TimeoutException:
            pass

        try:
            # Notification popup
            WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Not Now')]"))
            ).click()
            time.sleep(1)
        except TimeoutException:
            pass

    def send_direct_message(self, username: str, message: str) -> bool:
        """Send DM with better element handling"""
        try:
            # Open direct messages
            self.browser.get("https://www.instagram.com/direct/inbox/")
            WebDriverWait(self.browser, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//div[text()='Send message']"))
            ).click()

            # Search for user
            search = WebDriverWait(self.browser, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Search...']"))
            )
            search.send_keys(username)
            time.sleep(2)

            # Select user from results
            WebDriverWait(self.browser, 20).until(
                EC.element_to_be_clickable((By.XPATH, f"/html/body/div[6]/div[1]/div/div[2]/div/div/div/div/div/div/div[1]/div/div[3]/div/div/div[1]"))
            ).click()

            # Click Next button
            WebDriverWait(self.browser, 20).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[6]/div[1]/div/div[2]/div/div/div/div/div/div/div[1]/div/div[4]"))
            ).click()

            # Send message
            input_box = WebDriverWait(self.browser, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//textarea[@placeholder='Message...']"))
            )
            input_box.send_keys(message)
            input_box.send_keys(Keys.RETURN)

            # Verify message sent
            WebDriverWait(self.browser, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'message-sent')]"))
            )
            return True

        except Exception as e:
            print(f"Failed to send message to {username}: {str(e)}")
            return False

    def close(self) -> None:
        """Clean up browser instance"""
        self.browser.quit()


@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return

    if message.content.startswith("/send_dm_insta"):
        bot = None  # Initialize bot to None
        try:
            # Extract the message to be sent from the Discord command
            parts = message.content.split(" ", 1)
            if len(parts) < 2:
                await message.channel.send("Please provide the message to send.")
                return

            dm_message = parts[1]

            if not TARGET_USERNAME:
                await message.channel.send("❌ Target username is not set in the .env file.")
                return

            await message.channel.send(f"🚀 Sending message to {TARGET_USERNAME}: {dm_message}")

            # Initialize the Instagram bot
            bot = InstagramBot(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
            bot.log_in()
            bot.bypass_popups()

            # Send the direct message
            if bot.send_direct_message(TARGET_USERNAME, dm_message):
                await message.channel.send(f"✅ Successfully sent message to {TARGET_USERNAME}.")
            else:
                await message.channel.send(f"❌ Failed to send message to {TARGET_USERNAME}.")

        except Exception as e:
            await message.channel.send(f"❌ Critical error: {str(e)}")
        finally:
            if bot is not None:
                bot.close()


@client.event
async def on_ready() -> None:
    print(f"{client.user} is operational!")


def main() -> None:
    client.run(TOKEN)


if __name__ == "__main__":
    main()
