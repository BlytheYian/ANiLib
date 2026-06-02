import json
from channels.generic.websocket import AsyncWebsocketConsumer

_waiting: list = []
_rooms_ready: dict = {}   # room_group → set of channel_names that pressed ready


class ArenaConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_group  = None
        self._body_color = '#47A5E7'
        user = self.scope['user']
        if user.is_authenticated:
            self.username = user.username
            self._avatar  = str(user.avatar) if hasattr(user, 'avatar') and user.avatar else 'avatar_default.png'
        else:
            self.username = f'Guest_{self.channel_name[-6:]}'
            self._avatar  = 'avatar_default.png'
        await self.accept()

    async def disconnect(self, close_code):
        if self in _waiting:
            _waiting.remove(self)
        if self.room_group:
            _rooms_ready.pop(self.room_group, None)
            await self.channel_layer.group_discard(self.room_group, self.channel_name)
            await self.channel_layer.group_send(self.room_group, {
                'type': 'opponent_disconnected',
                'sender': self.channel_name,
            })
            self.room_group = None

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        t = data.get('type')
        if t == 'join_queue':
            await self._join_queue(data)
        elif t == 'ready' and self.room_group:
            await self._handle_ready()
        elif t == 'state_update' and self.room_group:
            await self.channel_layer.group_send(self.room_group, {
                'type': 'relay_state',
                'data': data,
                'sender': self.channel_name,
            })
        elif t == 'game_action' and self.room_group:
            await self.channel_layer.group_send(self.room_group, {
                'type': 'relay_action',
                'data': data,
                'sender': self.channel_name,
            })

    # ── 配對 ──────────────────────────────────────────────
    async def _join_queue(self, data):
        self._body_color = data.get('bodyColor', '#47A5E7')
        if _waiting:
            opponent = _waiting.pop(0)
            room = f'arena__{min(id(self), id(opponent))}__{max(id(self), id(opponent))}'
            self.room_group = room
            opponent.room_group = room
            await self.channel_layer.group_add(room, self.channel_name)
            await self.channel_layer.group_add(room, opponent.channel_name)
            await self.channel_layer.group_send(room, {
                'type':         'game_start',
                'host':         opponent.channel_name,
                'guest':        self.channel_name,
                'host_name':    opponent.username,
                'guest_name':   self.username,
                'host_color':   opponent._body_color,
                'guest_color':  self._body_color,
                'host_avatar':  opponent._avatar,
                'guest_avatar': self._avatar,
            })
        else:
            _waiting.append(self)
            await self.send(json.dumps({'type': 'waiting'}))

    # ── Ready 雙方確認 ──────────────────────────────────────
    async def _handle_ready(self):
        if self.room_group not in _rooms_ready:
            _rooms_ready[self.room_group] = set()
        _rooms_ready[self.room_group].add(self.channel_name)

        await self.channel_layer.group_send(self.room_group, {
            'type': 'player_ready',
            'sender': self.channel_name,
        })

        if len(_rooms_ready[self.room_group]) >= 2:
            _rooms_ready.pop(self.room_group, None)
            await self.channel_layer.group_send(self.room_group, {
                'type': 'game_begin',
            })

    # ── Group handlers ─────────────────────────────────────
    async def game_start(self, event):
        role       = 'host' if event['host'] == self.channel_name else 'guest'
        opp_name   = event['guest_name']   if role == 'host' else event['host_name']
        opp_color  = event['guest_color']  if role == 'host' else event['host_color']
        opp_avatar = event['guest_avatar'] if role == 'host' else event['host_avatar']
        await self.send(json.dumps({
            'type':           'game_start',
            'role':           role,
            'opponentName':   opp_name,
            'opponentColor':  opp_color,
            'opponentAvatar': opp_avatar,
        }))

    async def player_ready(self, event):
        if event['sender'] != self.channel_name:
            await self.send(json.dumps({'type': 'opponent_ready'}))

    async def game_begin(self, event):
        await self.send(json.dumps({'type': 'game_begin'}))

    async def relay_state(self, event):
        if event['sender'] != self.channel_name:
            await self.send(json.dumps(event['data']))

    async def relay_action(self, event):
        if event['sender'] != self.channel_name:
            await self.send(json.dumps(event['data']))

    async def opponent_disconnected(self, event):
        if event['sender'] != self.channel_name:
            await self.send(json.dumps({'type': 'opponent_disconnected'}))
            self.room_group = None
