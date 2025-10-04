import pandas as pd
import dataframe_image as dfi
import pywhatkit
import time
import argparse
import os

# ==============================
# ARGUMENT PARSER
# ==============================
parser = argparse.ArgumentParser(description="Send vendor reports via WhatsApp")
parser.add_argument("excel_file", help="Path to Excel file (.xlsx)")
parser.add_argument("--sheet", default="Sheet2", help="Sheet name to read (default=Sheet2)")
parser.add_argument("--country_code", default="+91", help="Default country code, e.g., +91")
parser.add_argument("--wait_time", type=int, default=15, help="Wait time before sending message")
parser.add_argument("--delay_between", type=int, default=5, help="Delay between vendors")
args = parser.parse_args()

excel_file = args.excel_file
sheet_name = args.sheet
country_code = args.country_code
wait_time = args.wait_time
delay_between_sends = args.delay_between




# ==============================
# READ EXCEL (row 4 headers)
# ==============================
if not os.path.exists(excel_file):
    raise FileNotFoundError(f"Excel file not found: {excel_file}")

df = pd.read_excel(excel_file, sheet_name=sheet_name, header=3)

# ==============================
# DROP UNWANTED COLUMNS
# ==============================
# Exclude any column containing these keywords (case-insensitive)
exclude_keywords = ["HSK", "NLM", "Buffer"]
cols_to_keep = [col for col in df.columns if not any(k.lower() in str(col).lower() for k in exclude_keywords)]
df = df[cols_to_keep]

# Required columns check
required_cols = {"Vendor Name", "Vendor MobileNumber"}
if not required_cols.issubset(df.columns):
    raise ValueError(f"Excel file must have columns: {required_cols}, found {df.columns.tolist()}")

# ==============================
# FILTER VALID VENDORS
# ==============================
df = df[df["Vendor Name"].notna() & df["Vendor MobileNumber"].notna()]
df["Vendor MobileNumber"] = df["Vendor MobileNumber"].apply(
    lambda x: str(int(x)) if pd.notna(x) and isinstance(x, float) else str(x)
)

# ==============================
# LOOP THROUGH UNIQUE VENDORS
# ==============================
unique_vendors = df[["Vendor Name", "Vendor MobileNumber"]].drop_duplicates()

for _, row in unique_vendors.iterrows():
    vendor = str(row["Vendor Name"]).strip()
    phone_number = row["Vendor MobileNumber"]

    # Convert phone_number to string safely
    if isinstance(phone_number, float):
        phone_number = str(int(phone_number))
    else:
        phone_number = str(phone_number).strip()

    if not phone_number:
        continue

    if not phone_number.startswith("+"):
        phone_number = country_code + phone_number

    # Filter data for this vendor
    vendor_df = df[df["Vendor Name"].str.lower() == vendor.lower()]
    if vendor_df.empty:
        continue

    # ==============================
    # STYLE DATAFRAME WITH BORDERS AND HEADER COLOR
    # ==============================
    styled = (vendor_df.style
              .set_table_styles([
                  {'selector': 'th', 'props': [('background-color', 'yellow'), ('border', '1px solid black')]},
                  {'selector': 'td', 'props': [('border', '1px solid black')]}
              ])
              .hide(axis="index")   # correct way to hide index
             )

    # Save as image
    safe_vendor = vendor.replace(" ", "_").replace("/", "_")
    image_path = f"{safe_vendor}_report.png"
    dfi.export(styled, image_path)
    print(f"[+] Saved data for {vendor} -> {image_path}")

    # ==============================
    # SEND VIA WHATSAPP
    # ==============================
    print(f"[+] Sending WhatsApp message to {vendor} ({phone_number})...")
    try:
        pywhatkit.sendwhats_image(
            receiver=phone_number,
            img_path=image_path,
            caption=f"Report for {vendor}",
            wait_time=wait_time,
            tab_close=True
        )
        print(f"[✔] Sent successfully to {vendor} ({phone_number})")
    except Exception as e:
        print(f"[x] Failed to send to {vendor} ({phone_number}): {e}")

    time.sleep(delay_between_sends)

print("\n✅ All vendor reports processed!")
