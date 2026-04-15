import asyncio
import math
import os
import threading
from contextlib import asynccontextmanager

import rclpy
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from geometry_msgs.msg import PoseArray, PoseWithCovarianceStamped
from nav_msgs.msg import Path
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from std_msgs.msg import Int32, String

FRONTEND_DIST_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
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
        self.last_state: str | None = None
        self.last_waypoints: list | None = None
        self.last_current_wp: int | None = None

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.add(ws)
        if self.last_pose is not None:
            await ws.send_json({"type": "pose", "data": self.last_pose})
        if self.last_plan is not None:
            await ws.send_json({"type": "plan", "data": self.last_plan})
        if self.last_state is not None:
            await ws.send_json({"type": "state", "data": self.last_state})
        if self.last_waypoints is not None:
            await ws.send_json({"type": "waypoints", "data": self.last_waypoints})
        if self.last_current_wp is not None:
            await ws.send_json({"type": "current_wp", "data": self.last_current_wp})

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
        self.create_subscription(
            String,
            "/patrol/state",
            self._on_state,
            10,
        )
        # Match the patrol_manager's latched publisher
        latching_qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.create_subscription(
            PoseArray,
            "/patrol/waypoints",
            self._on_waypoints,
            latching_qos,
        )
        self.create_subscription(
            Int32,
            "/patrol/current_waypoint",
            self._on_current_wp,
            10,
        )
        self.get_logger().info(
            "fleet_backend subscribed to /amcl_pose, /plan, /patrol/state, "
            "/patrol/waypoints, /patrol/current_waypoint"
        )

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

    def _on_state(self, msg: String) -> None:
        state = msg.data
        manager.last_state = state
        if main_loop is not None:
            asyncio.run_coroutine_threadsafe(
                manager.broadcast({"type": "state", "data": state}),
                main_loop,
            )

    def _on_waypoints(self, msg: PoseArray) -> None:
        waypoints = [
            {
                "x": p.position.x,
                "y": p.position.y,
                "yaw": quat_to_yaw(
                    p.orientation.x,
                    p.orientation.y,
                    p.orientation.z,
                    p.orientation.w,
                ),
            }
            for p in msg.poses
        ]
        manager.last_waypoints = waypoints
        if main_loop is not None:
            asyncio.run_coroutine_threadsafe(
                manager.broadcast({"type": "waypoints", "data": waypoints}),
                main_loop,
            )

    def _on_current_wp(self, msg: Int32) -> None:
        idx = msg.data
        manager.last_current_wp = idx
        if main_loop is not None:
            asyncio.run_coroutine_threadsafe(
                manager.broadcast({"type": "current_wp", "data": idx}),
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


app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
