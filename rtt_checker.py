#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import time
import statistics
from datetime import datetime

def install_package(package):
    """패키지 자동 설치"""
    print(f"📦 {package} 패키지를 설치하는 중...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} 설치 완료!")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {package} 설치 실패!")
        return False

def check_and_install_flask():
    """Flask 패키지 확인 및 자동 설치"""
    try:
        import flask
        return True
    except ImportError:
        print("Flask가 설치되어 있지 않습니다.")
        if install_package("flask"):
            try:
                import flask
                return True
            except ImportError:
                return False
        return False

if not check_and_install_flask():
    print("❌ Flask 설치에 실패했습니다. 수동으로 'pip install flask'를 실행해주세요.")
    sys.exit(1)

from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

class RTTChecker:
    def __init__(self):
        self.client_rtts = {}
        
    def store_client_rtt(self, client_id, rtt):
        """클라이언트의 RTT 데이터 저장"""
        if client_id not in self.client_rtts:
            self.client_rtts[client_id] = []
        self.client_rtts[client_id].append({
            'rtt': rtt,
            'timestamp': datetime.now()
        })
    
    def get_client_stats(self, client_id):
        """클라이언트의 RTT 통계 계산"""
        if client_id not in self.client_rtts or not self.client_rtts[client_id]:
            return {"error": "RTT 데이터가 없습니다."}
        
        rtts = [data['rtt'] for data in self.client_rtts[client_id]]
        
        return {
            "client_id": client_id,
            "count": len(rtts),
            "min": min(rtts),
            "max": max(rtts),
            "avg": statistics.mean(rtts),
            "median": statistics.median(rtts),
            "recent_rtts": rtts[-10:],  # 최근 10개 RTT
            "timestamps": [data['timestamp'].strftime("%H:%M:%S") for data in self.client_rtts[client_id][-10:]]
        }

rtt_checker = RTTChecker()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RTT 체커</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container { 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { 
            color: #333; 
            text-align: center; 
            margin-bottom: 30px;
        }
        .input-section { 
            margin-bottom: 30px; 
            padding: 20px; 
            background: #f9f9f9; 
            border-radius: 5px;
        }
        .input-group { 
            margin-bottom: 15px; 
        }
        label { 
            display: block; 
            margin-bottom: 5px; 
            font-weight: bold; 
        }
        input[type="text"], input[type="number"] { 
            width: 100%; 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 4px; 
            box-sizing: border-box;
        }
        button { 
            background: #007bff; 
            color: white; 
            padding: 12px 25px; 
            border: none; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 16px;
        }
        button:hover { 
            background: #0056b3; 
        }
        button:disabled { 
            background: #ccc; 
            cursor: not-allowed; 
        }
        .results { 
            margin-top: 30px; 
        }
        .stats { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; 
            margin-bottom: 20px;
        }
        .stat-card { 
            background: #e3f2fd; 
            padding: 15px; 
            border-radius: 5px; 
            text-align: center;
        }
        .stat-value { 
            font-size: 24px; 
            font-weight: bold; 
            color: #1976d2; 
        }
        .stat-label { 
            color: #666; 
            margin-top: 5px; 
        }
        .logs { 
            background: #f8f9fa; 
            border: 1px solid #dee2e6; 
            border-radius: 5px; 
            padding: 15px; 
            max-height: 400px; 
            overflow-y: auto;
        }
        .log-entry { 
            font-family: monospace; 
            margin-bottom: 5px; 
            padding: 5px; 
            background: white; 
            border-radius: 3px;
        }
        .error { 
            color: #dc3545; 
            background: #f8d7da; 
            padding: 15px; 
            border-radius: 5px; 
            margin: 15px 0;
        }
        .loading { 
            text-align: center; 
            color: #666; 
            font-style: italic;
        }
        .progress { 
            width: 100%; 
            background-color: #e0e0e0; 
            border-radius: 10px; 
            margin: 15px 0;
        }
        .progress-bar { 
            height: 20px; 
            background-color: #4caf50; 
            border-radius: 10px; 
            transition: width 0.3s ease;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐 실시간 클라이언트-서버 RTT 모니터</h1>
        
        <div class="input-section">
            <div class="input-group">
                <label for="interval">측정 간격 (초):</label>
                <input type="number" id="interval" value="1" min="0.1" max="10" step="0.1" onchange="updateInterval()">
            </div>
            <div class="input-group">
                <label>상태:</label>
                <span id="status" style="color: #4caf50; font-weight: bold;">🟢 실시간 측정 중</span>
            </div>
        </div>

        <div id="results" class="results"></div>
    </div>

    <script>
        let testInterval = null;
        let rtts = [];
        let clientId = Math.random().toString(36).substr(2, 9);
        let totalMeasurements = 0;
        
        function startContinuousRTT() {
            const interval = parseFloat(document.getElementById('interval').value) * 1000;
            
            if (testInterval) {
                clearInterval(testInterval);
            }
            
            testInterval = setInterval(async () => {
                const startTime = performance.now();
                
                try {
                    const response = await fetch('/ping', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            client_id: clientId,
                            timestamp: startTime
                        })
                    });
                    
                    const endTime = performance.now();
                    const rtt = endTime - startTime;
                    
                    if (response.ok) {
                        rtts.push(rtt);
                        totalMeasurements++;
                        
                        // 최근 100개의 RTT만 유지하여 메모리 관리
                        if (rtts.length > 100) {
                            rtts.shift();
                        }
                        
                        updateRealTimeResults();
                        
                        // 상태 업데이트
                        const statusElement = document.getElementById('status');
                        statusElement.innerHTML = `🟢 실시간 측정 중 (${totalMeasurements}번째 측정, 최근: ${rtt.toFixed(2)}ms)`;
                    }
                } catch (error) {
                    console.error('RTT 측정 오류:', error);
                    const statusElement = document.getElementById('status');
                    statusElement.innerHTML = `🔴 연결 오류 발생`;
                    statusElement.style.color = '#f44336';
                }
            }, interval);
        }
        
        function updateInterval() {
            // 간격이 변경되면 측정을 재시작
            startContinuousRTT();
        }
        
        // 페이지 로드 시 자동 시작
        window.onload = function() {
            startContinuousRTT();
        };

        function updateRealTimeResults() {
            if (rtts.length === 0) return;
            
            const resultsDiv = document.getElementById('results');
            const min = Math.min(...rtts);
            const max = Math.max(...rtts);
            const avg = rtts.reduce((a, b) => a + b, 0) / rtts.length;
            const sorted = [...rtts].sort((a, b) => a - b);
            const median = sorted.length % 2 === 0 
                ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
                : sorted[Math.floor(sorted.length / 2)];
            const variance = rtts.reduce((acc, rtt) => acc + Math.pow(rtt - avg, 2), 0) / rtts.length;
            const stddev = Math.sqrt(variance);
            
            let html = `
                <h3>📊 실시간 RTT 통계 (최근 ${rtts.length}개 샘플)</h3>
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-value">${rtts[rtts.length - 1].toFixed(2)}</div>
                        <div class="stat-label">현재 RTT (ms)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${avg.toFixed(2)}</div>
                        <div class="stat-label">평균 RTT (ms)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${median.toFixed(2)}</div>
                        <div class="stat-label">중간값 RTT (ms)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stddev.toFixed(2)}</div>
                        <div class="stat-label">표준편차 (ms)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${min.toFixed(2)}</div>
                        <div class="stat-label">최소 RTT (ms)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${max.toFixed(2)}</div>
                        <div class="stat-label">최대 RTT (ms)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${totalMeasurements}</div>
                        <div class="stat-label">총 측정 횟수</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${rtts.length}</div>
                        <div class="stat-label">표본 크기</div>
                    </div>
                </div>
                <h4>📈 최근 RTT 기록 (최신 10개)</h4>
                <div class="logs">
                    ${rtts.slice(-10).reverse().map((rtt, i) => {
                        const measurementNum = totalMeasurements - i;
                        return `<div class="log-entry">#${measurementNum}: ${rtt.toFixed(2)}ms</div>`;
                    }).join('')}
                </div>
            `;
            
            resultsDiv.innerHTML = html;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/ping', methods=['POST'])
def ping():
    """클라이언트의 ping 요청을 처리하고 RTT 데이터를 저장"""
    data = request.json
    client_id = data.get('client_id')
    client_timestamp = data.get('timestamp')
    
    if not client_id:
        return jsonify({"error": "클라이언트 ID가 필요합니다."}), 400
    
    # 서버에서의 처리 시간을 시뮬레이션 (실제로는 매우 작음)
    server_time = time.time() * 1000  # ms로 변환
    
    return jsonify({
        "status": "pong",
        "client_id": client_id,
        "server_timestamp": server_time,
        "client_timestamp": client_timestamp
    })

@app.route('/stats/<client_id>')
def get_client_stats(client_id):
    """특정 클라이언트의 RTT 통계 조회"""
    stats = rtt_checker.get_client_stats(client_id)
    return jsonify(stats)

if __name__ == '__main__':
    print("🌐 RTT 체커 웹서버를 시작합니다...")
    print("📡 http://localhost:5000 에서 접속 가능합니다.")
    app.run(debug=True, host='0.0.0.0', port=5000)