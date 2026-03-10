#!/usr/bin/env python3
"""
OpenClaw 会话搜索服务 - 纯服务端渲染版本
"""
import json
import os
import urllib.parse
import configparser
from flask import Flask, jsonify, render_template_string, request

# 读取配置文件
config = configparser.ConfigParser()
config_file = os.path.join(os.path.dirname(__file__), 'config.ini')
config.read(config_file)

HOST = config.get('server', 'host', fallback='0.0.0.0')
PORT = config.getint('server', 'port', fallback=5000)
AGENTS_DIR = config.get('agents', 'agents_dir', fallback=r"C:\Users\user\.openclaw\agents")

app = Flask(__name__)

def load_session_messages(session_file, max_chars=50000):
    """加载会话的消息内容"""
    messages = []
    if session_file and os.path.exists(session_file):
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if sum(len(m) for m in messages) > max_chars:
                        break
                    try:
                        msg = json.loads(line)
                        content = msg.get('message', {}).get('content', [])
                        for c in content:
                            if isinstance(c, dict):
                                text = c.get('text', '') or c.get('content', '')
                                if text:
                                    messages.append(text)
                    except:
                        pass
        except Exception as e:
            print(f"Error loading {session_file}: {e}")
    return '\n\n'.join(messages)

def load_all_sessions():
    sessions = []
    
    for agent_name in os.listdir(AGENTS_DIR):
        sessions_dir = os.path.join(AGENTS_DIR, agent_name, "sessions")
        sessions_file = os.path.join(sessions_dir, "sessions.json")
        
        if os.path.exists(sessions_file):
            try:
                with open(sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, dict):
                                value['key'] = key
                                value['agentId'] = agent_name
                                session_file = value.get('sessionFile')
                                value['messages'] = load_session_messages(session_file)
                                sessions.append(value)
            except Exception as e:
                print(f"Error loading {sessions_file}: {e}")
    
    return sessions

def search_sessions(keyword, agent_filter=None):
    sessions = load_all_sessions()
    
    if not keyword:
        return sessions
    
    keyword = keyword.lower()
    results = []
    
    for s in sessions:
        search_text = (
            s.get('key', '') + ' ' + 
            s.get('agentId', '') + ' ' + 
            s.get('messages', '')
        ).lower()
        
        if keyword in search_text:
            if agent_filter and s.get('agentId') != agent_filter:
                continue
            results.append(s)
    
    return results

def escape_html(text):
    if not text:
        return ''
    return (str(text)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;'))

@app.route('/')
def index():
    keyword = request.args.get('keyword', '').strip()
    agent_filter = request.args.get('agent', '').strip()
    detail_key = request.args.get('detail', '').strip()
    
    if keyword or agent_filter:
        sessions = search_sessions(keyword, agent_filter if agent_filter else None)
    else:
        sessions = load_all_sessions()
    
    # 如果有 detail 参数，显示详情页面
    if detail_key:
        for s in sessions:
            if s.get('key') == detail_key:
                return show_detail_page(s)
    
    # 显示列表页面
    return show_list_page(sessions, keyword, agent_filter)

def show_list_page(sessions, keyword='', agent_filter=''):
    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenClaw 会话搜索</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background: linear-gradient(135deg, #e8f4f8 0%, #f5f0ff 50%, #fff5f0 100%); min-height: 100vh; padding: 40px 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        
        /* 头部 */
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #333; font-size: 32px; font-weight: 600; margin-bottom: 8px; }
        .header p { color: #666; font-size: 14px; }
        
        /* 搜索框 */
        .search-box { background: white; padding: 24px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin-bottom: 24px; }
        .search-form { display: flex; gap: 12px; flex-wrap: wrap; }
        .search-form input { flex: 1; min-width: 200px; padding: 12px 16px; border: 2px solid #e8e8e8; border-radius: 10px; font-size: 14px; transition: border-color 0.3s; }
        .search-form input:focus { outline: none; border-color: #667eea; }
        .search-form select { padding: 12px 16px; border: 2px solid #e8e8e8; border-radius: 10px; font-size: 14px; background: white; cursor: pointer; transition: border-color 0.3s; }
        .search-form select:focus { outline: none; border-color: #667eea; }
        .search-form button { padding: 12px 28px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 10px; font-size: 14px; font-weight: 500; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
        .search-form button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }
        .search-form { display: flex; gap: 12px; flex-wrap: wrap; }
        .search-form input { flex: 1; min-width: 200px; padding: 12px 16px; border: 2px solid #e8e8e8; border-radius: 10px; font-size: 14px; transition: border-color 0.3s; }
        .search-form input:focus { outline: none; border-color: #667eea; }
        .search-form select { padding: 12px 16px; border: 2px solid #e8e8e8; border-radius: 10px; font-size: 14px; background: white; cursor: pointer; transition: border-color 0.3s; }
        .search-form select:focus { outline: none; border-color: #667eea; }
        .search-form button { padding: 12px 28px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 10px; font-size: 14px; font-weight: 500; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
        .search-form button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }
        
        /* 统计 */
        .stats { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; color: #333; font-size: 14px; }
        .stats .count { font-size: 16px; font-weight: 500; color: #333; }
        
        /* 会话列表 */
        .session-list { list-style: none; }
        .session-item { background: white; margin-bottom: 12px; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); transition: transform 0.2s, box-shadow 0.2s; }
        .session-item:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.12); }
        
        .session-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; gap: 12px; flex-wrap: wrap; }
        .session-key { font-weight: 600; color: #333; font-size: 14px; word-break: break-all; flex: 1; }
        .detail-link { color: #667eea; text-decoration: none; transition: color 0.2s; }
        .detail-link:hover { color: #764ba2; }
        
        .agent-tag { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 500; }
        .agent-main { background: #E3F2FD; color: #1976D2; }
        .agent-work { background: #E8F5E9; color: #388E3C; }
        .agent-tech { background: #FFF3E0; color: #F57C00; }
        .agent-food { background: #FCE4EC; color: #C2185B; }
        
        .session-meta { color: #888; font-size: 12px; margin-top: 8px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
        .session-meta span { display: flex; align-items: center; gap: 4px; }
        .token-icon { width: 14px; height: 14px; }
        
        .message-preview { font-size: 12px; color: #999; margin-top: 10px; padding-top: 10px; border-top: 1px solid #f0f0f0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        
        /* 空状态 */
        .empty { text-align: center; padding: 60px 20px; color: #333; }
        .empty-icon { font-size: 48px; margin-bottom: 16px; }
        .empty p { font-size: 16px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 OpenClaw 会话搜索</h1>
            <p>管理和搜索您的 AI 助手会话</p>
        </div>
        
        <div class="search-box">
            <form method="get" class="search-form">
                <input type="text" name="keyword" placeholder="搜索会话关键字..." value="''' + escape_html(keyword) + '''">
                <select name="agent">
                    <option value="">所有 Agent</option>
                    <option value="main"''' + (' selected' if agent_filter == 'main' else '') + '''>🤖 main</option>
                    <option value="work"''' + (' selected' if agent_filter == 'work' else '') + '''>💼 work</option>
                    <option value="tech"''' + (' selected' if agent_filter == 'tech' else '') + '''>📰 tech</option>
                    <option value="food"''' + (' selected' if agent_filter == 'food' else '') + '''>🍜 food</option>
                </select>
                <button type="submit">搜索</button>
            </form>
        </div>
        
        <div class="stats">
            <span class="count">共 ''' + str(len(sessions)) + ''' 个会话''' + (' (匹配"' + escape_html(keyword) + '")' if keyword else '') + '''</span>
        </div>'''
    
    if not sessions:
        html += '''
        <div class="empty">
            <div class="empty-icon">📭</div>
            <p>没有找到匹配的会话</p>
        </div>'''
    else:
        html += '<ul class="session-list">'
    
    for s in sessions:
        key = s.get('key', 'N/A')
        token = s.get('totalTokens', 'N/A')
        agent = s.get('agentId', 'N/A')
        messages = s.get('messages', '')
        msg_preview = messages[:200] if messages else ''
        detail_url = '/?detail=' + urllib.parse.quote(key)
        
        # Agent 标签样式
        agent_class = 'agent-' + agent if agent else ''
        agent_emoji = {'main': '🤖', 'work': '💼', 'tech': '📰', 'food': '🍜'}.get(agent, '🔹')
        
        html += '''
        <li class="session-item">
            <div class="session-header">
                <a href="''' + detail_url + '''" class="session-key detail-link">''' + escape_html(key) + '''</a>
                <span class="agent-tag ''' + agent_class + '''">''' + agent_emoji + ' ' + escape_html(agent) + '''</span>
            </div>
            <div class="session-meta">
                <span>💰 Token: ''' + str(token) + '''</span>'''
        if msg_preview:
            html += '''
                <span class="message-preview">''' + escape_html(msg_preview) + '''</span>'''
        html += '''
            </div>
        </li>'''
    
    html += '''
    </ul>
    </div>
    </body>
    </html>'''
    
    return html

def show_detail_page(session):
    key = session.get('key', 'N/A')
    token_total = session.get('totalTokens', 'N/A')
    token_input = session.get('inputTokens', 'N/A')
    token_output = session.get('outputTokens', 'N/A')
    token_cache_read = session.get('cacheRead', 0)
    token_cache_write = session.get('cacheWrite', 0)
    agent = session.get('agentId', 'N/A')
    session_id = session.get('sessionId', 'N/A')
    messages = session.get('messages', '(无消息内容)')
    
    # 对消息进行 JSON 转义
    messages_json = json.dumps(messages)
    
    # Agent 标签样式
    agent_class = 'agent-' + agent if agent else ''
    agent_emoji = {'main': '🤖', 'work': '💼', 'tech': '📰', 'food': '🍜'}.get(agent, '🔹')
    
    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>会话详情 - ''' + escape_html(key) + '''</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 40px 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        
        .header { margin-bottom: 20px; }
        .header a, .header button { margin-right: 10px; }
        
        .btn { padding: 10px 20px; border: none; border-radius: 8px; text-decoration: none; display: inline-block; cursor: pointer; font-size: 14px; font-weight: 500; transition: transform 0.2s, box-shadow 0.2s; }
        .btn-back { background: white; color: #667eea; }
        .btn-back:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .btn-copy { background: white; color: #667eea; border: 2px solid #667eea; }
        .btn-copy:hover { background: #f0f4ff; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .btn-copy.copied { background: #f0f4ff; color: #667eea; border-color: #667eea; }
        
        .detail-box { background: white; padding: 24px; border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.15); }
        .detail-title { color: #333; font-size: 20px; font-weight: 600; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee; }
        
        .detail-row { margin-bottom: 20px; }
        .detail-label { font-weight: 500; color: #888; font-size: 12px; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
        .detail-value { color: #333; font-size: 14px; word-break: break-all; }
        
        .message-content { background: #f8f9fa; padding: 16px; border-radius: 10px; max-height: 400px; overflow-y: auto; white-space: pre-wrap; font-size: 13px; line-height: 1.6; color: #444; font-family: "SF Mono", Monaco, "Courier New", monospace; }
        
        .token-tags { display: flex; flex-wrap: wrap; gap: 8px; }
        .token-tag { display: inline-block; padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: 500; }
        .token-total { background: #E3F2FD; color: #1976D2; }
        .token-input { background: #F3E5F5; color: #7B1FA2; }
        .token-output { background: #E8F5E9; color: #388E3C; }
        .token-cache { background: #FFF3E0; color: #F57C00; }
        
        .agent-tag { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 500; }
        .agent-main { background: #E3F2FD; color: #1976D2; }
        .agent-work { background: #E8F5E9; color: #388E3C; }
        .agent-tech { background: #FFF3E0; color: #F57C00; }
        .agent-food { background: #FCE4EC; color: #C2185B; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <a href="/" class="btn btn-back">← 返回列表</a>
            <button class="btn btn-copy" id="copyBtn" onclick="copyMessages()">📋 复制消息内容</button>
        </div>
        
        <div class="detail-box">
            <h2 class="detail-title">📄 会话详情</h2>
            
            <div class="detail-row">
                <div class="detail-label">会话 ID</div>
                <div class="detail-value">''' + escape_html(session_id) + '''</div>
            </div>
            
            <div class="detail-row">
                <div class="detail-label">会话 Key</div>
                <div class="detail-value">''' + escape_html(key) + '''</div>
            </div>
            
            <div class="detail-row">
                <div class="detail-label">Agent</div>
                <div class="detail-value"><span class="agent-tag ''' + agent_class + '''">''' + agent_emoji + ' ' + escape_html(agent) + '''</span></div>
            </div>
            
            <div class="detail-row">
                <div class="detail-label">Token 使用</div>
                <div class="token-tags">
                    <span class="token-tag token-total">💰 总: ''' + str(token_total) + '''</span>
                    <span class="token-tag token-input">📥 输入: ''' + str(token_input) + '''</span>
                    <span class="token-tag token-output">📤 输出: ''' + str(token_output) + '''</span>
                    <span class="token-tag token-cache">📚 缓存读: ''' + str(token_cache_read) + '''</span>
                    <span class="token-tag token-cache">📝 缓存写: ''' + str(token_cache_write) + '''</span>
                </div>
            </div>
            
            <div class="detail-row">
                <div class="detail-label">消息内容</div>
                <div class="message-content" id="msgContent">''' + escape_html(messages) + '''</div>
            </div>
        </div>
    </div>
    
    <script>
    function copyMessages() {
        var text = document.getElementById('msgContent').innerText;
        navigator.clipboard.writeText(text).then(function() {
            var btn = document.getElementById('copyBtn');
            btn.innerText = '✅ 已复制！';
            btn.classList.add('copied');
            setTimeout(function() {
                btn.innerText = '📋 复制消息内容';
                btn.classList.remove('copied');
            }, 2000);
        }).catch(function() {
            alert('复制失败，请手动选中消息内容 Ctrl+C 复制');
        });
    }
    </script>
</body>
</html>'''
    
    return html

@app.route('/api/sessions')
def api_sessions():
    sessions = load_all_sessions()
    return jsonify(sessions)

@app.route('/copy')
def copy_content():
    """提供纯文本内容供复制"""
    key = request.args.get('key', '').strip()
    sessions = load_all_sessions()
    
    for s in sessions:
        if s.get('key') == key:
            messages = s.get('messages', '')
            return '```\n' + messages + '\n```', 200, {'Content-Type': 'text/plain; charset=utf-8'}
    
    return '会话未找到', 404

if __name__ == '__main__':
    print("启动 OpenClaw 会话搜索服务...")
    print(f"访问 http://localhost:{PORT} 查看/搜索会话")
    app.run(host=HOST, port=PORT, debug=True)
