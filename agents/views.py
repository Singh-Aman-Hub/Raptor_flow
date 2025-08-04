from django.http import JsonResponse
from .api import run_agent_logic  # replace with actual function




from django.views.decorators.csrf import csrf_exempt
import json
import asyncio


@csrf_exempt
def run_agent(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_input = data.get('user_input', '')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_agent_logic(user_input))
        return JsonResponse(result)
    return JsonResponse({"error": "POST request required"}, status=400)