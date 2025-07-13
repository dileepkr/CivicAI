#!/usr/bin/env python
"""
Test script to demonstrate the enhanced debate functionality
"""
import asyncio
import json
from datetime import datetime
from api.main import stream_debate_process, session_manager, debug_system

class MockWebSocket:
    """Mock WebSocket for testing"""
    def __init__(self):
        self.messages = []
    
    async def send_text(self, text):
        data = json.loads(text)
        self.messages.append(data)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {data.get('type', 'unknown')}: {data.get('message', data.get('content', 'No content'))}")

async def test_enhanced_debate():
    """Test the enhanced debate system"""
    print("🎭 Testing Enhanced Debate System")
    print("=" * 50)
    
    # Create mock WebSocket
    websocket = MockWebSocket()
    
    # Create test session
    session_id = "test_session_001"
    session_manager.create_session(session_id, "debug", "policy_1")
    
    try:
        # Run enhanced debate
        await stream_debate_process(session_id, debug_system, "policy_1", websocket)
        
        print("\n✅ Enhanced debate completed successfully!")
        print(f"📊 Total messages sent: {len(websocket.messages)}")
        
        # Show message types
        message_types = {}
        for msg in websocket.messages:
            msg_type = msg.get('type', 'unknown')
            message_types[msg_type] = message_types.get(msg_type, 0) + 1
        
        print("\n📈 Message breakdown:")
        for msg_type, count in message_types.items():
            print(f"  {msg_type}: {count}")
        
    except Exception as e:
        print(f"❌ Error during debate: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_debate()) 