import threading
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.core.cache import cache
from .server_classes import ServerManager

def available_gameserver(request):
    gameserver_manager = cache.get("gameserver_manager")
    return JsonResponse({
        'available': gameserver_manager.get_available_server().address
    })

def available_gameserver_list(request):
    gameserver_manager = cache.get("gameserver_manager")
    server_list = gameserver_manager.get_available_servers()
    ret_list = [s.address for s in server_list]
    return JsonResponse({
        'server_list': ret_list
    })

def server_update(request):
    if(cache.get("thread_running")):
        return HttpResponse("Already In Progress")
    else:
        cache.set("thread_running", True)
        gameserver_manager = cache.get("gameserver_manager")
        initiation_thread = threading.Thread(target=gameserver_manager.server_update)
        initiation_thread.setDaemon(True)
        initiation_thread.start()
        return HttpResponse("Initiating")