from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import re
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

CSV_FILE = "tweets_data.csv"

def extract_hashtags(text):
    return re.findall(r"#\w+", text)

def scrape_nitter_hashtag(hashtag, duration=60):
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    nitter_url = f"https://nitter.net/search?q=%23{hashtag}"
    driver.get(nitter_url)

    start_time = time.time()
    seen_tweets = set()
    tweets_list = []

    try:
        while time.time() - start_time < duration:
            wait = WebDriverWait(driver, 10)
            tweets = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='tweet-content media-body']")))
            for tweet in tweets:
                text = tweet.text.strip()
                hashtags = extract_hashtags(text)
                if text not in seen_tweets:
                    seen_tweets.add(text)
                    tweets_list.append({"hashtag": hashtag, "tweet": text, "hashtags": ",".join(hashtags)})
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
            time.sleep(1)
    except Exception as e:
        print(f"Scraping error: {e}")
    finally:
        driver.quit()
        save_tweets_to_csv(tweets_list)
        print(f"✅ Scraped {len(tweets_list)} tweets for #{hashtag}")
        return tweets_list

def save_tweets_to_csv(tweets_list):
    df = pd.DataFrame(tweets_list)
    if os.path.exists(CSV_FILE):
        df_existing = pd.read_csv(CSV_FILE)
        df = pd.concat([df_existing, df], ignore_index=True)
    df.to_csv(CSV_FILE, index=False, encoding="utf-8")
    print(f"✅ Saved to {CSV_FILE}")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        hashtag = request.form.get("hashtag")
        if not hashtag:
            return render_template("index.html", error="Hashtag is required")
        scrape_nitter_hashtag(hashtag)
        return redirect(url_for("results", hashtag=hashtag))
    return render_template("index.html")

@app.route("/results")
def results():
    hashtag = request.args.get("hashtag")
    if not hashtag:
        return redirect(url_for("index"))

    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        print("CSV Data Loaded:\n", df.head())
    else:
        df = pd.DataFrame(columns=["hashtag", "tweet", "hashtags"])
        print("No CSV file found")

    df["hashtag"] = df["hashtag"].astype(str).str.lower().str.strip()
    hashtag = hashtag.lower().strip()
    tweets = df[df["hashtag"] == hashtag]["tweet"].tolist()
    print(f"Filtered Tweets for #{hashtag}: {tweets}")

    return render_template("results.html", hashtag=hashtag, tweets=tweets)

if __name__ == "__main__":
    app.run(debug=True)