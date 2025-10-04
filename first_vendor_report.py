import pandas as pd
import dataframe_image as dfi
import pywhatkit
import time

# ==============================
# CONFIGURATION
# ==============================
excel_file = r"C:\Balaji Paala\vendor\F&V_BLR_Indent_051025.xlsx"
country_code = "+91"          # Default country code, change if required
wait_time = 15                # Seconds to wait before sending each image

# ==============================
# STEP 1: READ EXCEL DATA
# ==============================
df = pd.read_excel(excel_file)

print(df)

# Ensure required columns exist
required_cols = {"VendorName", "MobileNumber"}
if not required_cols.issubset(df.columns):
    raise ValueError(f"Excel file must have columns: {required_cols}")

# ==============================
# STEP 2: LOOP OVER UNIQUE VENDORS
# ==============================
unique_vendors = df["VendorName"].unique()

for vendor in unique_vendors:
    filtered_df = df[df["VendorName"].str.lower() == vendor.lower()]
    if filtered_df.empty:
        continue

    # ==============================
    # SAVE FILTERED DATA AS IMAGE
    # ==============================
    image_path = f"{vendor}_data.png"
    dfi.export(filtered_df, image_path)
    print(f"[+] Saved data for {vendor} -> {image_path}")

    # ==============================
    # GET MOBILE NUMBER
    # ==============================
    phone_number = str(filtered_df.iloc[0]["MobileNumber"]).strip()

    if not phone_number.startswith("+"):
        phone_number = country_code + phone_number  # prepend country code if missing

    print(f"[+] Sending WhatsApp message to {vendor} ({phone_number})...")

    # ==============================
    # SEND IMAGE VIA WHATSAPP
    # ==============================
    try:
        pywhatkit.sendwhats_image(
            receiver=phone_number,
            img_path=image_path,
            caption=f"Indent For {vendor}",
            wait_time=wait_time,
            tab_close=True
        )
        print(f"[✔] Sent successfully to {vendor}")
    except Exception as e:
        print(f"[x] Failed to send to {vendor} ({phone_number}): {e}")

    # Give a small delay before next vendor
    time.sleep(5)

print("\n✅ All vendors processed!")
