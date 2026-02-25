"""
WhatsApp Web Automation using PyAutoGUI
Controls WhatsApp Web to send messages automatically.
"""

import os
import sys
import time
import webbrowser
from pathlib import Path

try:
    import pyautogui
    import pyperclip
except ImportError:
    print("Installing required packages...")
    os.system("pip install pyautogui pyperclip")
    import pyautogui
    import pyperclip


def send_whatsapp_message(phone_number, message, wait_time=15):
    """
    Send a WhatsApp message using WhatsApp Web automation.
    
    Args:
        phone_number: Recipient's phone number with country code (e.g., +923222208301)
        message: Message to send
        wait_time: Time to wait for WhatsApp Web to load (seconds)
    
    Returns:
        bool: True if message sent successfully, False otherwise
    """
    try:
        # Format the WhatsApp Web URL
        # Using wa.me which is more reliable than web.whatsapp.com direct links
        whatsapp_url = f"https://wa.me/{phone_number.replace('+', '')}"
        
        print(f"   Opening WhatsApp Web for: {phone_number}")
        
        # Open WhatsApp Web in default browser
        webbrowser.open(whatsapp_url)
        
        # Wait for browser to open and WhatsApp to load
        print(f"   Waiting {wait_time} seconds for WhatsApp to load...")
        time.sleep(wait_time)
        
        # Copy message to clipboard
        pyperclip.copy(message)
        
        # Small delay to ensure clipboard is ready
        time.sleep(1)
        
        # Click in the message input area (relative to center of screen)
        # This is a heuristic - may need adjustment based on screen resolution
        screen_width, screen_height = pyautogui.size()
        
        # Click in the approximate message input area
        # WhatsApp Web message box is typically at bottom center
        input_x = screen_width // 2
        input_y = int(screen_height * 0.85)  # 85% down the screen
        
        print(f"   Clicking message input area at ({input_x}, {input_y})...")
        pyautogui.click(input_x, input_y)
        time.sleep(1)
        
        # Paste the message using Ctrl+V
        print("   Pasting message...")
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1)
        
        # Press Enter to send
        print("   Sending message (Enter)...")
        pyautogui.press('enter')
        
        # Wait for message to be sent
        time.sleep(2)
        
        print("   Message sent!")
        return True
        
    except Exception as e:
        print(f"   Error sending WhatsApp message: {e}")
        return False


def send_whatsapp_to_contact(contact_name, message, wait_time=10):
    """
    Send a WhatsApp message to a contact by name.
    
    Args:
        contact_name: Name of the contact as saved in WhatsApp
        message: Message to send
        wait_time: Time to wait for WhatsApp Web to load
    
    Returns:
        bool: True if message sent successfully
    """
    try:
        # Open WhatsApp Web
        webbrowser.open("https://web.whatsapp.com")
        time.sleep(wait_time)
        
        # Click on search box
        screen_width, screen_height = pyautogui.size()
        search_x = int(screen_width * 0.2)  # Left side where search is
        search_y = int(screen_height * 0.15)
        
        pyautogui.click(search_x, search_y)
        time.sleep(1)
        
        # Type contact name
        pyperclip.copy(contact_name)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(2)
        
        # Press Enter to select contact
        pyautogui.press('enter')
        time.sleep(2)
        
        # Click message input
        input_x = screen_width // 2
        input_y = int(screen_height * 0.85)
        pyautogui.click(input_x, input_y)
        time.sleep(1)
        
        # Paste and send message
        pyperclip.copy(message)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1)
        pyautogui.press('enter')
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    # Test the function
    print("WhatsApp Automation Test")
    print("="*50)
    
    test_number = input("Enter phone number (with country code): ")
    test_message = input("Enter message: ")
    
    success = send_whatsapp_message(test_number, test_message)
    
    if success:
        print("\n✅ Test successful!")
    else:
        print("\n❌ Test failed!")
