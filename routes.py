import json
import logging
from flask import render_template, request, jsonify
from app import app
from nova_core import NovaCore
from openai_integration import OpenAIIntegration

logger = logging.getLogger(__name__)

# Initialize Nova components
openai_integration = OpenAIIntegration()
nova = NovaCore(openai_integration)

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint with enhanced API capabilities"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Process message through Nova core
        response_data = nova.process_message(message)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({
            'error': 'An error occurred processing your message',
            'response': "I'm having trouble right now. Please try again.",
            'type': 'error'
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get memory and usage statistics"""
    try:
        stats = nova.get_memory_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Could not retrieve stats'}), 500

@app.route('/api/agent/daily-plan', methods=['GET'])
def get_daily_plan():
    """Get AI-generated daily plan"""
    try:
        plan = nova.agent.generate_daily_plan()
        return jsonify({
            'response': 'Here\'s your personalized daily plan:',
            'type': 'daily_plan',
            'plan': plan
        })
    except Exception as e:
        logger.error(f"Error generating daily plan: {e}")
        return jsonify({'error': 'Could not generate daily plan'}), 500

@app.route('/api/agent/insights', methods=['GET'])
def get_insights():
    """Get proactive insights from the agent"""
    try:
        insights = nova.agent.get_recent_insights()
        return jsonify({
            'response': 'Here are some insights based on your activity:',
            'type': 'insights',
            'insights': insights
        })
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        return jsonify({'error': 'Could not retrieve insights'}), 500

@app.route('/api/agent/status', methods=['GET'])
def get_agent_status():
    """Get current agent status and pending actions"""
    try:
        status = nova.agent.get_status()
        return jsonify({
            'response': 'Current agent status:',
            'type': 'agent_status',
            'status': status
        })
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return jsonify({'error': 'Could not retrieve agent status'}), 500

@app.route('/api/agent/action', methods=['POST'])
def execute_agent_action():
    """Execute a specific agent action"""
    try:
        data = request.get_json()
        action_id = data.get('action_id')
        
        if not action_id:
            return jsonify({'error': 'Action ID is required'}), 400
            
        result = nova.agent.execute_action(action_id)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error executing agent action: {e}")
        return jsonify({'error': 'Could not execute action'}), 500

@app.route('/api/agent/daily-briefing', methods=['GET'])
def get_daily_briefing():
    """Get AI-generated daily briefing"""
    try:
        briefing = nova.agent.generate_daily_briefing()
        return jsonify({
            'response': 'Here\'s your daily briefing:',
            'type': 'daily_briefing', 
            'data': briefing
        })
    except Exception as e:
        logger.error(f"Error generating daily briefing: {e}")
        return jsonify({'error': 'Could not generate daily briefing'}), 500

@app.route('/api/config/api-key', methods=['POST'])
def save_api_key():
    """Save API key for external services"""
    try:
        data = request.get_json()
        service = data.get('service')
        api_key = data.get('api_key')
        
        if not service or not api_key:
            return jsonify({'error': 'Service and API key are required'}), 400
        
        # Update the API key in the integrations
        if service == 'weather':
            nova.api_integrations.apis['weather']['api_key'] = api_key
            nova.api_integrations.apis['weather']['status'] = 'online'
        elif service == 'news':
            nova.api_integrations.apis['news']['api_key'] = api_key
            nova.api_integrations.apis['news']['status'] = 'online'
        else:
            return jsonify({'error': 'Unknown service'}), 400
        
        # Test the new API key
        nova.api_integrations._test_api_connectivity()
        
        return jsonify({'message': f'{service.title()} API key saved successfully'})
        
    except Exception as e:
        logger.error(f"Error saving API key: {e}")
        return jsonify({'error': 'Could not save API key'}), 500

@app.route('/api/external/status', methods=['GET'])
def get_api_status():
    """Get status of external API integrations"""
    try:
        status = nova.api_integrations.get_all_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting API status: {e}")
        return jsonify({'error': 'Could not retrieve API status'}), 500
