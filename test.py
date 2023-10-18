import requests

def get_proxy_from_api():
    response = requests.get("http://127.0.0.1:8000/getProxy")  # Replace with your API URL
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to obtain a proxy. API responded with status code {response.status_code}")

def release_proxy_to_api(proxy_id):
    response = requests.get(f"http://127.0.0.1:8000/release/{proxy_id}")  # Replace with your API URL
    if response.status_code == 200:
        print(f"Proxy released successfully: {proxy_id}")
    else:
        print(f"Failed to release the proxy: {proxy_id}. API responded with status code {response.status_code}")

def test_proxy():
    proxy = get_proxy_from_api()
    proxy_id = proxy['proxy_id']

    try:
        response = requests.get("https://www.google.com", proxies=proxy['proxy_info'], timeout=10)
        response.raise_for_status()
        print(f"Google response using proxy {proxy_id}: {response.status_code}")

    except Exception as e:
        print(f"Proxy not working: {proxy_id}, {str(e)}")

    release_proxy_to_api(proxy_id)

if __name__ == "__main__":
    test_proxy()
