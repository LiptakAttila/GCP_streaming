import requests
from constants import YOUTUBE_API_KEY, PLAYLIST_ID
import json
from pprint import pprint
from kafka import KafkaProducer
import logging

def fetch_page(url, parameters, page_token=None):
    params = {**parameters, 'key': YOUTUBE_API_KEY, 'page_token': page_token}
    response = requests.get(url, params)
    payload = json.loads(response.text)
    logging.info('Response: %s', payload)

    return payload

def fetch_page_lists(url, parameters, page_token=None):
    while True:
        payload = fetch_page(url, parameters, page_token)
        yield from payload['items']
        page_token = payload.get('nextPageToken')
        if page_token is None:
            break

def format_response(video):
        video_response = {
            'title': video['snippet']['title'],
            'likes': int(video['statistics'].get('likeCount', 0)),
            'comments': int(video['statistics'].get('commentCount', 0)),
            'views': int(video['statistics'].get('viewCount', 0)),
            'favorites': int(video['statistics'].get('favoriteCount', 0)),
            'thumbnail': video['snippet']['thumbnails']['default']['url']
        }
        return video_response

if __name__ == "__main__":

    #     producer.send('youtube_videos', json.dumps(video_response).encode('utf-8'))
    #     producer.flush()

    logging.basicConfig(level=logging.INFO)
    producer = KafkaProducer(bootstrap_servers=['localhost:9092'])

    for video_item in fetch_page_lists(
            "https://www.googleapis.com/youtube/v3/playlistItems",
            {
                'playlistId': PLAYLIST_ID, 'part': 'snippet,contentDetails,status',},
            None):
        video_id = video_item['contentDetails']['videoId']
        for video in fetch_page_lists(
            "https://www.googleapis.com/youtube/v3/videos",
            {'id': video_id, 'part': 'snippet, statistics'},
            None):
            format_response(video)
            # logging.info('Video here => %s', pprint(format_response(video)))

            producer.send('youtube_videos', json.dumps(format_response(video)).encode('utf-8'))
            producer.flush()