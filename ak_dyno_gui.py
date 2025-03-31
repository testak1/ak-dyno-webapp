import tkinter as tk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import matplotlib.pyplot as plt

def extract_tuning_info(url):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Comment this line to see browser
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        service = Service("chromedriver.exe")
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(url)

        # Simulate tab click via JavaScript to activate Stage 1
        try:
            driver.execute_script("document.querySelector('a[href=\"#stage-1\"]').click();")
        except Exception as e:
            print("⚠️ Could not click tab:", e)

        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        stage1_tab = soup.find("div", {"id": "stage-1"})
        if not stage1_tab:
            print("⚠️ Could not find #stage-1 content")
            return None

        rows = stage1_tab.find_all("tr")
        hk_values, nm_values = [], []

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                text = cols[0].text.strip().upper()
                val_text = cols[1].text.strip().replace("hk", "").replace("Nm", "").replace("+", "").strip()

                if not val_text.isdigit():
                    continue

                val = int(val_text)

                if "HK" in cols[1].text.upper():
                    hk_values.append(val)
                elif "NM" in cols[1].text.upper():
                    nm_values.append(val)

        if len(hk_values) >= 3 and len(nm_values) >= 3:
            hk_values = hk_values[:3]
            nm_values = nm_values[:3]
            return {
                "Original": {"hk": hk_values[0], "Nm": nm_values[0]},
                "Tuned": {"hk": hk_values[1], "Nm": nm_values[1]},
                "Increase": {"hk": hk_values[2], "Nm": nm_values[2]}
            }
        else:
            print("⚠️ Still missing or extra values → HK:", hk_values, "NM:", nm_values)
            return None

    except Exception as e:
        print("❌ Error:", e)
        return None


import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
import matplotlib.image as mpimg

def plot_dyno(data):
    rpm = np.array([1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000])

    # Realistic curve shapes (separate for NM and HK)
    nm_shape = np.array([0.7, 0.9, 1.0, 0.95, 0.85, 0.75, 0.65, 0.5])
    hk_shape = np.array([0.2, 0.45, 0.65, 0.8, 0.9, 1.0, 0.95, 0.85])

    # Scale with actual values
    nm_orig = nm_shape * data["Original"]["Nm"]
    nm_tuned = nm_shape * data["Tuned"]["Nm"]
    hk_orig = hk_shape * data["Original"]["hk"]
    hk_tuned = hk_shape * data["Tuned"]["hk"]

    # Smooth data
    rpm_smooth = np.linspace(rpm.min(), rpm.max(), 300)
    def smooth(y): return make_interp_spline(rpm, y)(rpm_smooth)

    # Create figure
    fig, ax1 = plt.subplots(figsize=(10, 6), facecolor="#222222")
    fig.subplots_adjust(right=0.88)
    ax1.set_facecolor("#222222")

    # ⬇️ ADD LOGO as background watermark
    try:
        logo = mpimg.imread("aktuning-akp.png")
        ax1.imshow(
            logo,
            aspect='auto',
            extent=[1500, 5000, 0, data["Tuned"]["hk"] * 1.1],
            alpha=0.15,
            zorder=-10
        )
    except FileNotFoundError:
        print("⚠️ Logo file not found – skipping watermark.")

    # Plot HK
    ax1.plot(rpm_smooth, smooth(hk_orig), color='deepskyblue', label='Original HK', linewidth=2)
    ax1.plot(rpm_smooth, smooth(hk_tuned), color='red', label='Tuned HK', linewidth=2)
    ax1.set_xlabel("RPM", color='white')
    ax1.set_ylabel("Effekt (HK)", color='white')
    ax1.tick_params(axis='x', colors='white')
    ax1.tick_params(axis='y', colors='white')
    ax1.set_ylim(0, data["Tuned"]["hk"] * 1.1)
    ax1.grid(True, color='gray', linestyle='--', alpha=0.3)
    ax1.set_title("Dyno Chart", color='white', fontsize=14)

    # Plot NM
    ax2 = ax1.twinx()
    ax2.plot(rpm_smooth, smooth(nm_orig), color='deepskyblue', linestyle='--', label='Original NM', linewidth=2)
    ax2.plot(rpm_smooth, smooth(nm_tuned), color='red', linestyle='--', label='Tuned NM', linewidth=2)
    ax2.set_ylabel("Vridmoment (Nm)", color='white')
    ax2.tick_params(axis='y', colors='white')
    ax2.set_ylim(0, data["Tuned"]["Nm"] * 1.1)

    # Legend
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper left',
               facecolor="#444444", edgecolor="white", labelcolor='white')

    # Save as PNG
    plt.savefig("ak_dyno_chart.png", dpi=300)
    print("✅ Saved: ak_dyno_chart.png")

    # Show plot
    plt.show()



def on_submit():
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("Fel", "Klistra in en URL först.")
        return

    result = extract_tuning_info(url)
    if result:
        plot_dyno(result)
    else:
        messagebox.showerror("Fel", "Kunde inte hämta tuningdata.")

# GUI Setup
root = tk.Tk()
root.title("AK Tuning Dyno Viewer")

tk.Label(root, text="Klistra in AK Performance URL:").pack(pady=5)
url_entry = tk.Entry(root, width=80)
url_entry.pack(padx=10, pady=5)

submit_btn = tk.Button(root, text="Visa Dynokarta", command=on_submit)
submit_btn.pack(pady=10)

root.mainloop()
