import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .queue_manager import get_queue_position, get_queue_count

class QueueConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.specialty = self.scope['url_route']['kwargs']['specialty']
        self.room_group_name = f'queue_{self.specialty.replace(" ", "_")}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'get_position':
            session_key = data.get('session_key')
            queue_number = data.get('queue_number')
            
            position = await sync_to_async(get_queue_position)(self.specialty, session_key)
            total = await sync_to_async(get_queue_count)(self.specialty)
            
            await self.send(text_data=json.dumps({
                'type': 'position_update',
                'position': position,
                'total': total,
                'queue_number': queue_number
            }))

    async def queue_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'queue_update',
            'position': event.get('position'),
            'total': event.get('total'),
            'queue_number': event.get('queue_number'),
            'session_key': event.get('session_key')
        }))
