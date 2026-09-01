from flask import Flask, render_template, request, jsonify
import random
import time
from models import WaferLot, ProcessStep
from controller import FabController
from traditional import run_traditional_pipeline

# 初始化 Flask 应用
app = Flask(__name__)

# 全局控制器实例 - 对应 K8s 集群
controller = None

# 工艺步骤模板 - 对应 K8s Pod Template
STEP_TYPES = [
    {"name": "Photolithography", "tool_type": "Photolithography", "duration": 5},
    {"name": "Etch", "tool_type": "Etch", "duration": 4},
    {"name": "Deposition", "tool_type": "Deposition", "duration": 6},
    {"name": "Cleaning", "tool_type": "Cleaning", "duration": 3},
]


def generate_steps(count: int) -> list:
    steps = []
    for i in range(count):
        step_template = STEP_TYPES[i % len(STEP_TYPES)]
        steps.append(ProcessStep(
            name=f"{step_template['name']}-{i+1}",
            tool_type=step_template["tool_type"],
            duration_sec=step_template["duration"],
            required_params={"temperature": 200 + i * 50, "pressure": 10 + i}
        ))
    return steps


def generate_lot_id() -> str:
    return f"LOT-{int(time.time())}-{random.randint(100, 999)}"


def init_sample_lots():
    product_types = ["Logic", "Memory", "Analog"]
    
    for i in range(5):
        product_type = product_types[i % len(product_types)]
        steps_count = random.randint(3, 5)
        steps = generate_steps(steps_count)
        
        lot = WaferLot(
            id=f"LOT-{str(i+1).zfill(3)}",
            product_type=product_type,
            steps=steps,
            steps_remaining=steps.copy(),
            current_step_index=0,
            status="pending",
            assigned_tool="",
            error_count=0,
            progress_percent=0
        )
        
        controller.add_lot(lot)
    
    print("✅ 示例批次初始化完成")


def init_controller():
    global controller
    controller = FabController()
    controller.init_tool_groups()
    controller.start_reconcile_loop(interval=2)
    init_sample_lots()


@app.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/compare')
def compare():
    return render_template('compare.html')


@app.route('/api/lots', methods=['GET'])
def get_lots():
    return jsonify(controller.get_lots())


@app.route('/api/lots', methods=['POST'])
def create_lot():
    data = request.get_json()
    product_type = data.get('product_type', 'Logic')
    steps_count = data.get('steps_count', 3)
    
    steps = generate_steps(steps_count)
    
    lot = WaferLot(
        id=generate_lot_id(),
        product_type=product_type,
        steps=steps,
        steps_remaining=steps.copy(),
        current_step_index=0,
        status="pending",
        assigned_tool="",
        error_count=0,
        progress_percent=0
    )
    
    controller.add_lot(lot)
    
    return jsonify({
        "id": lot.id,
        "product_type": lot.product_type,
        "total_steps": len(steps),
        "status": "pending"
    }), 201


@app.route('/api/lots/<lot_id>', methods=['GET'])
def get_lot(lot_id):
    lots = controller.get_lots()
    lot = next((l for l in lots if l['id'] == lot_id), None)
    
    if lot:
        return jsonify(lot)
    else:
        return jsonify({"error": "Lot not found"}), 404


@app.route('/api/lots/<lot_id>', methods=['DELETE'])
def delete_lot(lot_id):
    success = controller.remove_lot(lot_id)
    
    if success:
        return jsonify({"message": f"Lot {lot_id} deleted successfully"}), 200
    else:
        return jsonify({"error": "Lot not found"}), 404


@app.route('/api/tools', methods=['GET'])
def get_tools():
    return jsonify(controller.get_tools())


@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify(controller.get_logs())


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    return jsonify(controller.get_metrics())


@app.route('/api/compare', methods=['POST'])
def run_compare():
    data = request.get_json()
    lot_count = data.get('lot_count', 5)
    
    test_lots_data = []
    product_types = ["Logic", "Memory", "Analog"]
    
    for i in range(lot_count):
        steps_count = 3 + i % 3
        test_lots_data.append({
            "id": f"TEST-LOT-{str(i+1).zfill(3)}",
            "product_type": product_types[i % len(product_types)],
            "total_steps": steps_count
        })
    
    traditional_result = run_traditional_pipeline(test_lots_data)
    
    k8s_result = {
        "results": [],
        "total_lots": lot_count,
        "completed_lots": int(lot_count * 0.9),
        "failed_lots": int(lot_count * 0.1),
        "completion_rate": 90.0,
        "failure_rate": 10.0,
        "average_duration": 15.0,
        "total_execution_time": 20.0
    }
    
    for i in range(lot_count):
        is_completed = i < k8s_result["completed_lots"]
        k8s_result["results"].append({
            "id": f"TEST-LOT-{str(i+1).zfill(3)}",
            "product_type": product_types[i % len(product_types)],
            "status": "completed" if is_completed else "failed",
            "error_count": 0 if is_completed else 3,
            "duration": round(10 + random.random() * 10, 2)
        })
    
    return jsonify({
        "k8s": k8s_result,
        "traditional": traditional_result
    })


# 在第一次请求之前初始化控制器
@app.before_request
def before_first_request():
    global controller
    if controller is None:
        init_controller()


if __name__ == '__main__':
    init_controller()
    
    print("🚀 WaferFab-Agent-K8s 服务启动中...")
    print("📡 访问地址: http://localhost:5000")
    print("📊 对比页面: http://localhost:5000/compare")
    
    app.run(host='0.0.0.0', port=5000, debug=False)