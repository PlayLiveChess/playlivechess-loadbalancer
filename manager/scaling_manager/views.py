from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from .server_classes import ServerManagerThread

def available_gameserver(request):
    gameserver_manager = ServerManagerThread.get_instance()
    try:
        gs_address = gameserver_manager.get_available_server().address
    except Exception as e:
        print(e)
        gs_address = settings.BACKUP_GAMESERVER
    return JsonResponse({
        'available': gs_address
    })

def available_gameserver_list(request):
    gameserver_manager = ServerManagerThread.get_instance()
    server_list = gameserver_manager.get_available_servers()
    ret_list = [s.address for s in server_list]
    return JsonResponse({
        'server_list': ret_list
    })
