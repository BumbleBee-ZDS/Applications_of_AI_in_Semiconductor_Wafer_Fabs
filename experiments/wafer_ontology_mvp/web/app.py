import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import json
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# FastAPI 后端地址
FASTAPI_URL = "http://localhost:8000"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/investigate', methods=['POST'])
def investigate():
    """代理调用 FastAPI 的调查接口"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "查询不能为空"}), 400
        
        response = requests.post(
            f"{FASTAPI_URL}/investigate",
            json={"query": query},
            timeout=120
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": f"后端服务错误: {response.status_code}"}), response.status_code
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"连接后端服务失败: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"处理请求失败: {str(e)}"}), 500


@app.route('/api/health')
def health():
    """检查后端服务状态"""
    try:
        response = requests.get(f"{FASTAPI_URL}/health", timeout=10)
        return jsonify({"backend": "healthy" if response.status_code == 200 else "unhealthy"})
    except Exception:
        return jsonify({"backend": "unreachable"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
