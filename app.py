import asyncio
from aiohttp import web
import os
import socket
import random
import aiohttp
import requests
#Sti \1. Uni\OneDrive - Aarhus Universitet\Dokumenter\5. semester\Distruberede Systemer\Project2\bully-in-kubernetes-grp7>
POD_IP = str(os.environ['POD_IP'])
WEB_PORT = int(os.environ['WEB_PORT'])
POD_ID = random.randint(0, 100)
#leader_id = -1
#global other_pods
#data = dict()
async def setup_k8s():
    # If you need to do setup of Kubernetes, i.e. if using Kubernetes Python client
	print("K8S setup completed")
async def start_leader_setup():
    await asyncio.sleep(5) # wait for everything to be up
    ip_list = []
    print("Making a DNS lookup to service")
    response = socket.getaddrinfo("bully-service",0,0,0,0)
    print("Get response from DNS")
    for result in response:
        ip_list.append(result[-1][0])
    ip_list = list(set(ip_list))
    
    # Remove own POD ip from the list of pods
    ip_list.remove(POD_IP)
    print("Got %d other pod ip's" % (len(ip_list)))
    
    # Get ID's of other pods by sending a GET request to them
    await asyncio.sleep(2)
    other_pods = dict()
    for pod_ip in ip_list:
        endpoint = '/pod_id'
        url = 'http://' + str(pod_ip) + ':' + str(WEB_PORT) + endpoint
        response = requests.get(url)
        other_pods[str(pod_ip)] = response.json()
        
    # Other pods in network
    print(other_pods)
    
    max_id = max(other_pods.values())
    if (max_id < POD_ID):  
        print(f"Sending out our first coordinator_id which is {POD_ID}")
        send_out_coordinator(ip_list)


async def run_bully():
    while True:
        print("Running bully")
        
        
        # Get all pods doing bully
        ip_list = []
        print("Making a DNS lookup to service")
        response = socket.getaddrinfo("bully-service",0,0,0,0)
        print("Get response from DNS")
        for result in response:
            ip_list.append(result[-1][0])
        ip_list = list(set(ip_list))
        
        # Remove own POD ip from the list of pods
        ip_list.remove(POD_IP)
        print("Got %d other pod ip's" % (len(ip_list)))
        
        # Get ID's of other pods by sending a GET request to them
        await asyncio.sleep(2)
        other_pods = dict()
        for pod_ip in ip_list:
            endpoint = '/pod_id'
            url = 'http://' + str(pod_ip) + ':' + str(WEB_PORT) + endpoint
            response = requests.get(url)
            other_pods[str(pod_ip)] = response.json()
            
        # Other pods in network
        print(other_pods)
        
        print("checking alive")
        for pod_ip in ip_list:
            endpoint = "/pod_status"
            url = "http://" + str(pod_ip) + ':' + str(WEB_PORT) + endpoint
            response = requests.get(url)
        # Sleep a bit, then repeat
        await asyncio.sleep(2)




async def test_send(ip_list):
    for pod_ip in ip_list:
        endpoint = "/pod_status"
        url = "http://" + str(pod_ip) + ':' + str(WEB_PORT) + endpoint
        response = requests.get(url)
        print (response.status)

async def health_check_all():
    ip_list = []
    print("Making a DNS lookup to service")
    response = socket.getaddrinfo("bully-service",0,0,0,0)
    print("Get response from DNS")
    for result in response:
        ip_list.append(result[-1][0])
    ip_list = list(set(ip_list))
    
    # Remove own POD ip from the list of pods
    ip_list.remove(POD_IP)
    print("Got %d other pod ip's" % (len(ip_list)))
    
    # Get ID's of other pods by sending a GET request to them
    await asyncio.sleep(2)
    other_pods = dict()
    for pod_ip in ip_list:
        endpoint = '/pod_id'
        url = 'http://' + str(pod_ip) + ':' + str(WEB_PORT) + endpoint
        response = requests.get(url)
        other_pods[str(pod_ip)] = response.json()

async def leader_not_in_dict(dictionary): #Leader dead check
    return (leader_id not in dictionary.values())

#Check highest id which we received from discovery service
async def find_highest_ids_ip_address(): #maybe use other_pods
    return max(ip_list, key=ip_list.get)

#GET /pod_id
async def pod_id(request):
    return web.json_response(POD_ID)
    
#POST /receive_answer
async def send_answer(request):
    return web.json_response({"status": "alive"})

async def am_alive(request):
    return web.json_response("status", "200")

#POST /receive#_election
async def start_election(request): 
    leader_id = request.message

#Leader function to send out its ID to all pods
def send_out_coordinator(ip_list, POD_ID = POD_ID):
    for ip in ip_list:
        url = 'http://' + str(ip) + ':' + str(WEB_PORT) + "/send_out_coordinator" + "/" + str(POD_ID)
        requests.post(url)
#POST worker POD function - update individual leader ID
async def update_coordinator(request): #
    #coordinator_id
    leader_id = str(request.match_info['name'])
    print ("New leader: ", leader_id)
    return web.json_response("")

    
#GET /check_last_leader
async def leader_alive(request):
    for ip in ip_list:
        endpoint = "/send_answer"
        url =  'http://' + str(ip) + ':' + str(WEB_PORT) + endpoint
        response = requests.get(url)
        if not response.json() == "alive":
            print("TESTING")
    return

async def background_tasks(app):
    task1 = asyncio.create_task(start_leader_setup())
    #yield
    #task1.cancel()
    await task1
    task = asyncio.create_task(run_bully())
    yield
    task.cancel()
    await task

if __name__ == "__main__":
    app = web.Application()

    app.router.add_post('/update_coordinator', update_coordinator)
    app.router.add_get('/pod_id', pod_id)
    app.router.add_get('/leader_alive', leader_alive)
    
    app.router.add_post('/start_election', start_election)

    app.router.add_post('/send_out_coordinator/{name}', update_coordinator)
    

    #app.router.add_websocket("/ws")
    
    app.cleanup_ctx.append(background_tasks)
    web.run_app(app, host='0.0.0.0', port=WEB_PORT)


    #TODO:
    #implement known loader as leader_id

    #plan
    """
    plan:
    realize leader is dead
    check who is alive find highest id = find_highest_ids_ip_address
    ask it to check with last leader
    send out new leader id if needed
    

    """