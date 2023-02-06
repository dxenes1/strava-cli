from ._helpers import client, url, json
from urllib.parse import urlencode

def get_activity(activity_id):
    response = client.get(url(f"/activities/{activity_id}"))
    return json(response)

def post_activity(name, type, sport_type, start_date_local, elapsed_time, description, distance):
    data = {
        "name": name,
        "type": type,
        "sport_type": sport_type,
        "start_date_local": start_date_local,
        "elapsed_time": elapsed_time,
        "description": description,
        "distance": distance
    }
    response = client.post(url(f"/activities"), data=urlencode(data), headers={'content-type': 'application/x-www-form-urlencoded'})
    return json(response)