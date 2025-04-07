import os
import pandas as pd
import numpy as np
from gensim import corpora
from gensim.models import LdaModel, Word2Vec
from nltk.tokenize import word_tokenize
import nltk
from collections import Counter

nltk.download("punkt")

CSV_FILE = "tweets_data.csv"

def extract_top_hashtags(df, top_n=10):
    """Extracts the most frequent hashtags."""
    all_hashtags = []
    for hashtags in df["hashtags"].dropna():
        all_hashtags.extend(hashtags.split(","))

    hashtag_counts = Counter(all_hashtags)
    return hashtag_counts.most_common(top_n)

def train_lda_with_embeddings(df, num_topics=5, embedding_size=100):
    """Trains Word2Vec and LDA models on tweets data."""
    
    df.dropna(subset=['tweet'], inplace=True)  # Drop empty tweets
    df["Processed_Tweet"] = df["tweet"].str.lower().apply(word_tokenize)

    if df["Processed_Tweet"].empty:
        print("No valid documents found for topic modeling.")
        return None, None, None, df

    tokenized_docs = df["Processed_Tweet"].tolist()

    # Train Word2Vec model
    word2vec_model = Word2Vec(
        sentences=tokenized_docs,
        vector_size=embedding_size,
        window=5,
        min_count=1,
        workers=4,
        sg=1
    )

    # Create Dictionary and Corpus for LDA
    dictionary = corpora.Dictionary(tokenized_docs)
    corpus = [dictionary.doc2bow(doc) for doc in tokenized_docs]

    # Train LDA model
    lda_model = LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=num_topics,
        random_state=42,
        passes=10
    )

    # Assign dominant topics
    df["Dominant_Topic"] = [
        max(lda_model[corpus[i]], key=lambda x: x[1])[0] if corpus[i] else -1 
        for i in range(len(corpus))
    ]

    return lda_model, corpus, dictionary, df

if __name__ == "__main__":
    input_file = CSV_FILE
    df = pd.read_csv(input_file)
    num_topics = 5

    lda_model, corpus, dictionary, df = train_lda_with_embeddings(df, num_topics)

    if lda_model:
        output_file = "tweets_with_topics.csv"
        df.to_csv(output_file, index=False)
        print(f"✅ Data with topics saved to {output_file}")

        # Extract and display top hashtags
        top_hashtags = extract_top_hashtags(df, top_n=10)
        print("\n🔝 Top Hashtags:")
        for tag, count in top_hashtags:
            print(f"{tag}: {count} times")
