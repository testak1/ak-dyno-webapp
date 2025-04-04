import streamlit as st
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from scipy.interpolate import make_interp_spline
import numpy as np
import pandas as pd
import io

# --------------- Extract tuning data from AK Performance -------------------
@st.cache_data
def get_tuning_data(url, stage_name=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    # TEMP: Save HTML for debugging
    with open("debug.html", "w", encoding="utf-8") as f:
        f.write(soup.prettify())

    # Your scraping logic continues here ↓
    stage_tabs = soup.select("ul#stageTabs li a")
    stage_map = {tab.text.strip(): tab["href"].strip("#") for tab in stage_tabs}

    selected_id = None

    if stage_map:
        selected_id = stage_map.get(stage_name) if stage_name else list(stage_map.values())[0]
        stage_keys = list(stage_map.keys())
    else:
        tab_content = soup.find("div", class_="tab-content")
        active_pane = tab_content.find("div", class_="tab-pane active") if tab_content else None
        if active_pane:
            selected_id = active_pane.get("id")
            stage_keys = ["Default"]
        else:
            return None, [], "❌ Could not find any visible tuning stage."

    stage_div = soup.find("div", {"id": selected_id})
    if not stage_div:
        return None, stage_keys, f"❌ Could not find content for stage: {selected_id}"

    values = stage_div.select("table tbody td")
    texts = [v.get_text(strip=True).replace("+", "").replace("hk", "").replace("Nm", "") for v in values]

    hk_vals = [int(s.split()[0]) for s in texts if "hk" in s.lower()]
    nm_vals = [int(s.split()[0]) for s in texts if "nm" in s.lower()]

    if len(hk_vals) >= 3 and len(nm_vals) >= 3:
        data = {
            "Original": {"hk": hk_vals[0], "Nm": nm_vals[0]},
            "Tuned": {"hk": hk_vals[1], "Nm": nm_vals[1]},
            "Increase": {"hk": hk_vals[2], "Nm": nm_vals[2]},
        }
        return data, stage_keys, None

    return None, stage_keys, "❌ Could not extract hk/Nm values."


# --------------- Plot Dyno Chart -------------------
def plot_dyno(data):
    rpm = np.array([1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000])
    nm_shape = np.array([0.7, 0.9, 1.0, 0.95, 0.85, 0.75, 0.65, 0.5])
    hk_shape = np.array([0.2, 0.45, 0.65, 0.8, 0.9, 1.0, 0.95, 0.85])

    nm_orig = nm_shape * data["Original"]["Nm"]
    nm_tuned = nm_shape * data["Tuned"]["Nm"]
    hk_orig = hk_shape * data["Original"]["hk"]
    hk_tuned = hk_shape * data["Tuned"]["hk"]

    rpm_smooth = np.linspace(rpm.min(), rpm.max(), 300)
    def smooth(y): return make_interp_spline(rpm, y)(rpm_smooth)

    fig, ax1 = plt.subplots(figsize=(10, 6), facecolor="#222222")
    fig.subplots_adjust(right=0.88)
    ax1.set_facecolor("#222222")

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
        pass  # Skip logo if not found

    ax1.plot(rpm_smooth, smooth(hk_orig), color='deepskyblue', label='Original HK', linewidth=2)
    ax1.plot(rpm_smooth, smooth(hk_tuned), color='red', label='Tuned HK', linewidth=2)
    ax1.set_xlabel("RPM", color='white')
    ax1.set_ylabel("Effekt (HK)", color='white')
    ax1.tick_params(axis='x', colors='white')
    ax1.tick_params(axis='y', colors='white')
    ax1.set_ylim(0, data["Tuned"]["hk"] * 1.1)
    ax1.grid(True, color='gray', linestyle='--', alpha=0.3)
    ax1.set_title("Dyno Chart", color='white', fontsize=14)

    ax2 = ax1.twinx()
    ax2.plot(rpm_smooth, smooth(nm_orig), color='deepskyblue', linestyle='--', label='Original NM', linewidth=2)
    ax2.plot(rpm_smooth, smooth(nm_tuned), color='red', linestyle='--', label='Tuned NM', linewidth=2)
    ax2.set_ylabel("Vridmoment (Nm)", color='white')
    ax2.tick_params(axis='y', colors='white')
    ax2.set_ylim(0, data["Tuned"]["Nm"] * 1.1)

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc='upper left',
               facecolor="#444444", edgecolor="white", labelcolor='white')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300)
    buf.seek(0)
    plt.close()
    return buf


# --------------- Streamlit UI -------------------
st.set_page_config(page_title="AK Dyno Chart Generator", layout="centered")
st.title("🧰 AK Performance – Dyno Chart Generator")
st.caption("Klistra in en AK Performance tuninglänk för att generera en dynokarta.")

url = st.text_input("🔗 AK Performance Tuning URL")

if url:
    data, stages, error = get_tuning_data(url)

    if error:
        st.warning(error)

    selected_stage = "Default"
    if stages and len(stages) > 1:
        selected_stage = st.selectbox("🎛 Välj tuning stage", stages)
        data, _, error = get_tuning_data(url, stage_name=selected_stage)

    if data:
        st.success(f"✅ Tuningdata hämtad ({selected_stage})")
        st.json(data)

        chart_buf = plot_dyno(data)
        st.image(chart_buf, caption="Dyno Chart", use_column_width=True)

        st.download_button("📥 Ladda ner dynokarta (PNG)", chart_buf, file_name="dyno_chart.png")

        df = pd.DataFrame({
            "RPM": [1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000],
            "Original HK": np.array([0.2, 0.45, 0.65, 0.8, 0.9, 1.0, 0.95, 0.85]) * data["Original"]["hk"],
            "Tuned HK": np.array([0.2, 0.45, 0.65, 0.8, 0.9, 1.0, 0.95, 0.85]) * data["Tuned"]["hk"],
            "Original NM": np.array([0.7, 0.9, 1.0, 0.95, 0.85, 0.75, 0.65, 0.5]) * data["Original"]["Nm"],
            "Tuned NM": np.array([0.7, 0.9, 1.0, 0.95, 0.85, 0.75, 0.65, 0.5]) * data["Tuned"]["Nm"]
        })
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📊 Ladda ner CSV-data", csv, file_name="dyno_data.csv", mime="text/csv")
