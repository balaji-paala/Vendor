import pandas as pd
import dataframe_image as dfi
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# ==============================
# CONFIG
# ==============================
EXCEL_FILE = r"C:\Balaji Paala\vendor\F&V_BLR_Indent_051025.xlsx"
SHEET_NAME = "Sheet2"
WAIT_TIME = 5          # seconds before interacting
DELAY_BETWEEN = 5      # seconds between sending messages
USER_PROFILE = r"./WhatsApp_Profile"  # Chrome user profile folder (fresh on first run)

# ==============================
# READ EXCEL
# ==============================
if not os.path.exists(EXCEL_FILE):
    raise FileNotFoundError(f"Excel file not found: {EXCEL_FILE}")

# Read Excel starting from row 4 as headers
df = pd.read_excel(EXCEL_FILE, sheet_name=SHEET_NAME, header=3)

# Ensure required columns exist
required_cols = {"Vendor Name", "Vendor Group Name"}
if not required_cols.issubset(df.columns):
    raise ValueError(f"Excel file must have columns: {required_cols}, found {df.columns.tolist()}")

# Filter valid rows
df = df[df["Vendor Name"].notna() & df["Vendor Group Name"].notna()]
unique_vendors = df[["Vendor Name", "Vendor Group Name"]].drop_duplicates()

# ==============================
# START SELENIUM CHROME
# ==============================
# Use webdriver-manager to auto-install compatible chromedriver
service = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()

# Stable Chrome options for Windows
options.add_argument(f"--user-data-dir={USER_PROFILE}")  # keeps WhatsApp login session
options.add_argument("--disable-extensions")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--start-maximized")
# options.add_argument("--headless")  # Do NOT use headless for WhatsApp

# Start Chrome driver
driver = webdriver.Chrome(service=service, options=options)
driver.maximize_window()
driver.get("https://web.whatsapp.com")
print("Please scan QR code if not logged in...")
time.sleep(15)  # wait for user to scan QR

# ==============================
# LOOP THROUGH VENDORS
# ==============================
for _, row in unique_vendors.iterrows():
    vendor = str(row["Vendor Name"]).strip()
    group_name = str(row["Vendor Group Name"]).strip()

    # Filter data for this vendor
    vendor_df = df[df["Vendor Name"].str.lower() == vendor.lower()]
    if vendor_df.empty:
        continue

    # ==============================
    # STYLE AND SAVE IMAGE
    # ==============================
    styled = (vendor_df.style
              .set_table_styles([
                  {'selector': 'th', 'props': [('background-color', 'yellow'), ('border', '1px solid black')]},
                  {'selector': 'td', 'props': [('border', '1px solid black')]}
              ])
              .hide(axis="index")
             )
    safe_vendor = vendor.replace(" ", "_").replace("/", "_")
    image_path = f"{safe_vendor}_report.png"
    dfi.export(styled, image_path)
    print(f"[+] Saved data for {vendor} -> {image_path}")

    # ==============================
    # FIND GROUP AND SEND MESSAGE
    # ==============================
    try:
        # Search for the group
        search_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
        search_box.clear()
        search_box.send_keys(group_name)
        time.sleep(WAIT_TIME)
        search_box.send_keys(Keys.ENTER)
        time.sleep(WAIT_TIME)

        # Attach image
        attach_btn = driver.find_element(By.XPATH, '//span[@data-icon="clip"]')
        attach_btn.click()
        time.sleep(2)

        image_input = driver.find_element(By.XPATH, '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
        image_input.send_keys(os.path.abspath(image_path))
        time.sleep(2)

        # Send the image
        send_btn = driver.find_element(By.XPATH, '//span[@data-icon="send"]')
        send_btn.click()
        print(f"[✔] Sent report for {vendor} to group '{group_name}'")
    except Exception as e:
        print(f"[x] Failed to send to group '{group_name}': {e}")

    time.sleep(DELAY_BETWEEN)

# ==============================
# QUIT DRIVER
# ==============================
driver.quit()
print("\n✅ All vendor reports processed!")
