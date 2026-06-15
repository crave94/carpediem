import os
import json
import requests

STATIC_IMG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "images", "flames"))
JSON_OUTPUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "flames_scraped_data.json"))

CDN_BASE = "https://pub-37581592c5a045f3ad8b1881608a2769.r2.dev/images"

IMAGES_TO_DOWNLOAD = [
    f"{CDN_BASE}/items/flames/flame-black.png",
    f"{CDN_BASE}/items/flames/flame-crimson.png",
    f"{CDN_BASE}/items/flames/flame-rainbow.png",
    f"{CDN_BASE}/items/flames/flame-100.png",
    f"{CDN_BASE}/items/flames/flame-110.png",
    f"{CDN_BASE}/items/flames/flame-120.png",
    f"{CDN_BASE}/items/flames/flame-130.png",
    f"{CDN_BASE}/items/flames/flame-140.png",
    f"{CDN_BASE}/items/flames/flame-150.png",
    f"{CDN_BASE}/items/flames/karma-arf.png",
    f"{CDN_BASE}/guide/flame-stats-1.png",
    f"{CDN_BASE}/guide/flame-stats-2.png",
    f"{CDN_BASE}/guide/flame-stats-3.png"
]

SCRAPED_DATA = {
  "special": [
    {
      "category": "Common Flame Stats",
      "stats": [
        {
          "name": "Pure Stats",
          "values": ["-", "-", "33", "44", "55", "66", "77"],
          "image_url": "/static/images/flames/flame-stats-1.png"
        },
        {
          "name": "Mixed Stats",
          "values": ["-", "-", "18", "24", "30", "36", "42"],
          "image_url": ""
        },
        {
          "name": "Max HP/MP",
          "values": ["-", "-", "1800", "2400", "3000", "3600", "4200"],
          "image_url": ""
        },
        {
          "name": "Defense",
          "values": ["-", "-", "33", "44", "55", "66", "77"],
          "image_url": ""
        },
        {
          "name": "All Stats%",
          "values": ["-", "-", "3%", "4%", "5%", "6%", "7%"],
          "image_url": ""
        },
        {
          "name": "Equip Level Reduction",
          "values": ["-", "-", "-15", "-20", "-25", "-30", "-35"],
          "image_url": ""
        }
      ]
    },
    {
      "category": "Weapon-only Flame Stats",
      "stats": [
        {
          "name": "Weapon WA/MA",
          "values": ["-", "-", "64", "94", "129", "170", "218"],
          "image_url": ""
        },
        {
          "name": "Boss%",
          "values": ["-", "-", "6%", "8%", "10%", "12%", "14%"],
          "image_url": ""
        },
        {
          "name": "Damage%",
          "values": ["-", "-", "3%", "4%", "5%", "6%", "7%"],
          "image_url": ""
        }
      ]
    },
    {
      "category": "Armor-only Flame Stats",
      "stats": [
        {
          "name": "Armor WA/MA",
          "values": ["-", "-", "3", "4", "5", "6", "7"],
          "image_url": ""
        },
        {
          "name": "Speed",
          "values": ["-", "-", "3", "4", "5", "6", "7"],
          "image_url": ""
        },
        {
          "name": "Jump",
          "values": ["-", "-", "3", "4", "5", "6", "7"],
          "image_url": ""
        }
      ]
    }
  ],
  "normal": [
    {
      "category": "Common Flame Stats",
      "stats": [
        {
          "name": "Pure Stats",
          "values": ["11", "22", "33", "44", "55", "-", "-"],
          "image_url": ""
        },
        {
          "name": "Mixed Stats",
          "values": ["6", "12", "18", "24", "30", "-", "-"],
          "image_url": ""
        },
        {
          "name": "Max HP/MP",
          "values": ["600", "1200", "1800", "2400", "3000", "-", "-"],
          "image_url": ""
        },
        {
          "name": "Defense",
          "values": ["11", "22", "33", "44", "55", "-", "-"],
          "image_url": ""
        },
        {
          "name": "All Stats%",
          "values": ["1%", "2%", "3%", "4%", "5%", "-", "-"],
          "image_url": ""
        },
        {
          "name": "Equip Level Reduction",
          "values": ["-5", "-10", "-15", "-20", "-25", "-", "-"],
          "image_url": ""
        }
      ]
    },
    {
      "category": "Weapon-only Flame Stats",
      "stats": [
        {
          "name": "Weapon WA/MA",
          "values": ["22", "47", "77", "113", "156", "-", "-"],
          "image_url": ""
        },
        {
          "name": "Boss%",
          "values": ["2%", "4%", "6%", "8%", "10%", "-", "-"],
          "image_url": ""
        },
        {
          "name": "Damage%",
          "values": ["1%", "2%", "3%", "4%", "5%", "-", "-"],
          "image_url": ""
        }
      ]
    },
    {
      "category": "Armor-only Flame Stats",
      "stats": [
        {
          "name": "Armor WA/MA",
          "values": ["1", "2", "3", "4", "5", "-", "-"],
          "image_url": ""
        },
        {
          "name": "Speed",
          "values": ["1", "2", "3", "4", "5", "-", "-"],
          "image_url": ""
        },
        {
          "name": "Jump",
          "values": ["1", "2", "3", "4", "5", "-", "-"],
          "image_url": ""
        }
      ]
    }
  ]
}

def run_download_and_save():
    os.makedirs(STATIC_IMG_DIR, exist_ok=True)
    
    # Download images
    print("Starting image downloads...")
    for img_url in IMAGES_TO_DOWNLOAD:
        filename = img_url.split("/")[-1]
        dest_path = os.path.join(STATIC_IMG_DIR, filename)
        
        try:
            print(f"Downloading {img_url} to {dest_path}...")
            resp = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            resp.raise_for_status()
            with open(dest_path, "wb") as f:
                f.write(resp.content)
            print(f"Successfully downloaded {filename}")
        except Exception as e:
            print(f"Failed to download {img_url}: {e}")
            
    # Save JSON data
    print(f"Saving scraped data JSON to {JSON_OUTPUT_PATH}...")
    try:
        with open(JSON_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(SCRAPED_DATA, f, indent=2)
        print("Successfully saved scraped data JSON.")
    except Exception as e:
        print(f"Failed to save JSON data: {e}")

if __name__ == "__main__":
    run_download_and_save()
