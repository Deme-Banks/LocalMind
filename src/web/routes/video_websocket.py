"""
WebSocket routes for real-time video generation progress
"""

from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging

logger = logging.getLogger(__name__)

# Global SocketIO instance (will be initialized in server.py)
socketio: SocketIO = None


def init_socketio(app: Flask):
    """Initialize SocketIO"""
    global socketio
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=False,
        engineio_logger=False
    )
    return socketio


def setup_video_websocket_routes(socketio_instance: SocketIO, server_instance):
    """Setup WebSocket routes for video generation"""
    
    @socketio_instance.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info("Client connected to video WebSocket")
        emit('connected', {'status': 'ok'})
    
    @socketio_instance.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info("Client disconnected from video WebSocket")
    
    @socketio_instance.on('join_video_room')
    def handle_join_room(data):
        """Join a video generation room"""
        video_id = data.get('video_id')
        if video_id:
            room = f"video_{video_id}"
            join_room(room)
            logger.info(f"Client joined room: {room}")
            emit('joined_room', {'room': room, 'video_id': video_id})
    
    @socketio_instance.on('leave_video_room')
    def handle_leave_room(data):
        """Leave a video generation room"""
        video_id = data.get('video_id')
        if video_id:
            room = f"video_{video_id}"
            leave_room(room)
            logger.info(f"Client left room: {room}")
            emit('left_room', {'room': room, 'video_id': video_id})
    
    @socketio_instance.on('get_video_status')
    def handle_get_status(data):
        """Get video generation status"""
        video_id = data.get('video_id')
        if not video_id:
            emit('error', {'message': 'video_id required'})
            return
        
        if hasattr(server_instance, 'video_queue'):
            import asyncio
            try:
                # Run async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                status = loop.run_until_complete(
                    server_instance.video_queue.get_status(video_id)
                )
                loop.close()
                
                if status:
                    emit('video_status', status)
                else:
                    emit('error', {'message': 'Video not found'})
            except Exception as e:
                logger.error(f"Error getting video status: {e}")
                emit('error', {'message': str(e)})
        else:
            emit('error', {'message': 'Video queue not available'})


def emit_video_progress(video_id: str, progress: float, status: str = None):
    """Emit video generation progress"""
    if socketio:
        room = f"video_{video_id}"
        socketio.emit('video_progress', {
            'video_id': video_id,
            'progress': progress,
            'status': status
        }, room=room)


def emit_video_complete(video_id: str, result: dict):
    """Emit video generation completion"""
    if socketio:
        room = f"video_{video_id}"
        socketio.emit('video_complete', {
            'video_id': video_id,
            'result': result
        }, room=room)


def emit_video_error(video_id: str, error: str):
    """Emit video generation error"""
    if socketio:
        room = f"video_{video_id}"
        socketio.emit('video_error', {
            'video_id': video_id,
            'error': error
        }, room=room)

