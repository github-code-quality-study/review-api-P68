import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from urllib.parse import parse_qs, urlparse
import json
import pandas as pd
from datetime import datetime
import uuid
import os
from typing import Callable, Any
from wsgiref.simple_server import make_server

nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('stopwords', quiet=True)

adj_noun_pairs_count = {}
sia = SentimentIntensityAnalyzer()
stop_words = set(stopwords.words('english'))

reviews = pd.read_csv('data/reviews.csv').to_dict('records')

class ReviewAnalyzerServer:
    def __init__(self) -> None:
        # This method is a placeholder for future initialization logic
        pass

    def analyze_sentiment(self, review_body):
        sentiment_scores = sia.polarity_scores(review_body)
        return sentiment_scores

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]) -> bytes:
        """
        The environ parameter is a dictionary containing some useful
        HTTP request information such as: REQUEST_METHOD, CONTENT_LENGTH, QUERY_STRING,
        PATH_INFO, CONTENT_TYPE, etc.
        """

        if environ["REQUEST_METHOD"] == "GET":
            # Create the response body from the reviews and convert to a JSON byte string
            query = parse_qs(environ["QUERY_STRING"])
            
            location = query.get("location")
            start_date = query.get("start_date")
            end_date = query.get("end_date")
        
        
            filtered_reviews = []
            for review in reviews:
                if location and location[0] != review["Location"]:
                    continue

                review_date = datetime.strptime(review["Timestamp"].split(" ")[0], "%Y-%m-%d")
                if start_date:
                    start_date_obj = datetime.strptime(start_date[0], "%Y-%m-%d")
                    if review_date < start_date_obj:
                        continue

                if end_date:
                    end_date_obj = datetime.strptime(end_date[0], "%Y-%m-%d")
                    if review_date > end_date_obj:
                        continue
                
                filtered_reviews.append(review)
                
            # Perform sentiment analysis if needed
            for review in filtered_reviews:
                review["sentiment"] = self.analyze_sentiment(review["ReviewBody"])

            def compound(review):
                return review["sentiment"]["compound"]

            filtered_reviews.sort(key=compound, reverse=True)

            response_body = json.dumps(filtered_reviews, indent=2).encode("utf-8")
        

            # Set the appropriate response headers
            start_response("200 OK", [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response_body)))
             ])
            
            return [response_body]


        if environ["REQUEST_METHOD"] == "POST":
            # Write your code here

            locations = [
    "Albuquerque, New Mexico",
    "Carlsbad, California",
    "Chula Vista, California",
    "Colorado Springs, Colorado",
    "Denver, Colorado",
    "El Cajon, California",
    "El Paso, Texas",
    "Escondido, California",
    "Fresno, California",
    "La Mesa, California",
    "Las Vegas, Nevada",
    "Los Angeles, California",
    "Oceanside, California",
    "Phoenix, Arizona",
    "Sacramento, California",
    "Salt Lake City, Utah",
    "Salt Lake City, Utah",
    "San Diego, California",
    "Tucson, Arizona"
]
            try:
                request_size = int(environ.get('CONTENT_LENGTH', 0))
                
            except (ValueError):
                request_size = 0
            
            if request_size == 0:
                start_response("400 Bad Request", [
                ("Content-Type", "application/json"),
                ("Content-Length", "0")
                 ])
                return []
                

            request_body = environ['wsgi.input'].read(request_size)
            review_data = parse_qs(request_body)
            body = review_data.get(b'ReviewBody',[b''])[0].decode('utf-8')
            location = review_data.get(b'Location',[b''])[0].decode('utf-8')

            if body == '':
                start_response("400 Bad Request", [
                ("Content-Length", "0")
                 ])
                return []
            
            if not location in locations:
                start_response("400 Bad Request", [
                ("Content-Length", "0")
                 ])
                return []


            now = datetime.now()
            time_stamp = now.strftime("%Y-%m-%d %H:%M:%S")
            review_id = str(uuid.uuid4())

            response_body = json.dumps({"ReviewId": review_id, "ReviewBody": body, "Location":location, "Timestamp": time_stamp}, indent=2).encode("utf-8")

             # Set the appropriate response headers
            start_response("201 Created", [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response_body)))
             ])
            
            return [response_body]

if __name__ == "__main__":
    app = ReviewAnalyzerServer()
    port = os.environ.get('PORT', 8000)
    with make_server("", port, app) as httpd:
        print(f"Listening on port {port}...")
        httpd.serve_forever()