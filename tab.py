import pyautogui
import time
from datetime import datetime

# Advertisement messages
messages = [
    "All view ah new item",
    "ALLL View ah pale oak off",
    "All ./ah view ItsReZNuM",
    "All view my ah",
    "All creaking heart ah",
    "ah off khorde hamechi moft moft"
]

# Time settings
startup_delay = 10      # Wait before starting (seconds)
advert_interval = 180   # 5 minutes between advertisements
dot_delay = 3           # Delay after sending dot

message_index = 0


def log(message):
    """Print timestamped logs."""
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"[{current_time}] {message}")


def send_chat_message(message):
    """Open Minecraft chat and send a message."""
    log("Opening Minecraft chat...")
    pyautogui.press("t")
    time.sleep(0.5)

    log(f"Typing message: {message}")
    pyautogui.write(message)

    pyautogui.press("enter")
    log("Message sent successfully.")


def main():
    global message_index

    log("Minecraft Auto Advertiser started.")
    log(f"Waiting {startup_delay} seconds before first action...")
    
    time.sleep(startup_delay)

    log("Starting advertisement loop.")

    while True:
        try:
            # Send dot to prevent duplicate message detection
            send_chat_message(".")
            log(f"Waiting {dot_delay} seconds before advertisement...")
            time.sleep(dot_delay)

            # Send advertisement message
            current_message = messages[message_index]
            send_chat_message(current_message)

            # Move to next message
            message_index += 1

            if message_index >= len(messages):
                message_index = 0

            log(f"Next advertisement index: {message_index}")

            log(f"Waiting {advert_interval} seconds until next advertisement...")
            time.sleep(advert_interval)

        except Exception as e:
            log(f"ERROR: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()