import time
import redis
import requests
from fastapi import FastAPI, HTTPException
from fastapi_utils.tasks import repeat_every
from proxy import proxies
import random

app = FastAPI()

# Redis connection
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Initialize proxy status in Redis with all proxies as free
for i in range(0, len(proxies)):
    redis_client.set(f'proxy:{i}', 'free')

# Function to check proxy latency
def check_proxy_latency(proxy_id):
    proxy = None
    try:
        proxy = proxies[proxy_id]
    except:
        return

    try:
        # Replace httpbin with a ping website that you are sure will return 200 every request with latency close to 0
        response = requests.get("https://httpbin.org/ip", proxies=proxy, timeout=10)
        response.raise_for_status()  # Raise an exception if response status is not 200

        # Set the proxy as free
        redis_client.set(f'proxy:{proxy_id}', 'free')

    except Exception as e:
        # If there was an exception (proxy is not working), mark the proxy as 'in use'
        redis_client.set(f'proxy:{proxy_id}', 'in use')
        # print("PROXY NOT WORKING:", proxy['https'], str(e))

def checkFreeProxy():
    availableProxies = []
    for i in range(0, len(proxies)):
        proxy = proxies[i]
        status = redis_client.get(f'proxy:{i}')
        if status == b'free':
            availableProxies.append(i)
    random.shuffle(availableProxies)
    return availableProxies
    

# Get a free proxy
@app.get("/getProxy")
async def get_proxy():
    availableProxies = checkFreeProxy()
    for j in range(0, len(availableProxies)):
        i = availableProxies[j]
        proxy = proxies[i]
        status = redis_client.get(f'proxy:{i}')
        if status == b'free':
            redis_client.set(f'proxy:{i}', 'in use')
            return {'proxy_id': i, 'proxy_info': proxy}
    raise HTTPException(status_code=503, detail="No free proxies available.")

# Release a proxy by proxy_id
@app.get("/release/{proxy_id}")
async def release_proxy(proxy_id: int):
    status = redis_client.get(f'proxy:{proxy_id}')
    if status == b'in use':
        redis_client.set(f'proxy:{proxy_id}', 'free')
        return {'message': 'Proxy released successfully.'}
    else:
        return {'message': 'Proxy is not in use or does not exist.'}

@app.get("/releaseAll")
async def release_all_proxies():
    for i in range(0, len(proxies)):
        proxy = proxies[i]
        status = redis_client.get(f'proxy:{i}')
        if status == b'in use':
            redis_client.set(f'proxy:{i}', 'free')
    return {'message': 'All proxies released successfully.'}

@app.get("/")
async def status():
    return {'message': 'ONLINE'}


# Create a separate thread for checking and releasing proxies
@app.on_event("startup")
@repeat_every(seconds=60 * 10)  # Replace here with check time (default to 10 minutes)
def check_and_release_proxies() -> None:
    for i in range(0, len(proxies)):
        proxy = proxies[i]
        status = redis_client.get(f'proxy:{i}')
        if status == b'free':
            redis_client.set(f'proxy:{i}', 'in use')

            check_proxy_latency(i)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, workers=5)
