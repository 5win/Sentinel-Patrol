import asyncio
import math
import os
import threading
from contextlib import asynccontextmanager

import rclpy
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Path
from rclpy.node import Node

DASHBOARD_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dashboard")
)


def quat_to_yaw(qx: float, qy: float, qz: float, qw: float) -> float:
    siny = 2.0 * (qw * qz + qx * qy)
    cosy = 1.0 - 2.0 * (qy * qy + qz * qz)
    return math.atan2(siny, cosy)


class ConnectionManager:
    """Tracks active WebSocket clients and broadcasts messages to them."""

    def __init__(self) -> None:
        self.active: set[WebSocket] = set()
        self.last_pose: dict | None = None
        self.last_plan: list | None = None

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.add(ws)
        if self.last_pose is not None:
            await ws.send_json({"type": "pose", "data": self.last_pose})
        if self.last_plan is not None:
            await ws.send_json({"type": "plan", "data": self.last_plan})

    def disconnect(self, ws: WebSocket) -> None:
        self.active.discard(ws)

    async def broadcast(self, message: dict) -> None:
        dead: list[WebSocket] = []
        for ws in list(self.active):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.discard(ws)


manager = ConnectionManager()
main_loop: asyncio.AbstractEventLoop | None = None


class FleetBackendNode(Node):
    def __init__(self) -> None:
        super().__init__("fleet_backend")
        self.create_subscription(
            PoseWithCovarianceStamped,
            "/amcl_pose",
            self._on_pose,
            10,
        )
        self.create_subscription(
            Path,
            "/plan",
            self._on_plan,
            10,
        )
        self.get_logger().info("fleet_backend subscribed to /amcl_pose, /plan")

    def _on_pose(self, msg: PoseWithCovarianceStamped) -> None:
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        pose = {
            "x": p.x,
            "y": p.y,
            "yaw": quat_to_yaw(q.x, q.y, q.z, q.w),
        }
        manager.last_pose = pose
        if main_loop is not None:
            asyncio.run_coroutine_threadsafe(
                manager.broadcast({"type": "pose", "data": pose}),
                main_loop,
            )

    def _on_plan(self, msg: Path) -> None:
        points = [
            {"x": ps.pose.position.x, "y": ps.pose.position.y}
            for ps in msg.poses
        ]
        manager.last_plan = points
        if main_loop is not None:
            asyncio.run_coroutine_threadsafe(
                manager.broadcast({"type": "plan", "data": points}),
                main_loop,
            )


def ros_spin() -> None:
    rclpy.init()
    node = FleetBackendNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global main_loop
    main_loop = asyncio.get_running_loop()
    thread = threading.Thread(target=ros_spin, daemon=True)
    thread.start()
    yield


app = FastAPI(lifespan=lifespan)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


app.mount("/", StaticFiles(directory=DASHBOARD_DIR, html=True), name="dashboard")
