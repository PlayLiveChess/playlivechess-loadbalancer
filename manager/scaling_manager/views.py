from django.http import JsonResponse
from django.core.cache import cache
from .server_classes import ServerManagerThread

def available_gameserver(request):
    gameserver_manager = ServerManagerThread.get_instance()
    return JsonResponse({
        'available': gameserver_manager.get_available_server().address
    })

def available_gameserver_list(request):
    gameserver_manager = ServerManagerThread.get_instance()
    server_list = gameserver_manager.get_available_servers()
    ret_list = [s.address for s in server_list]
    return JsonResponse({
        'server_list': ret_list
    })
