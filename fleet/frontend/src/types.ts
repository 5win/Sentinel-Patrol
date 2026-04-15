// ── WebSocket message types ──────────────────────────────────────────────────

export interface PoseData {
  x: number;
  y: number;
  yaw: number;
}

export interface WaypointPoint {
  x: number;
  y: number;
}

export interface PlanPoint {
  x: number;
  y: number;
}

export type RobotState =
  | 'idle'
  | 'patrolling'
  | 'wait'
  | 'emergency'
  | 'avoiding'
  | 'returning';

export type WsConnectionStatus = 'connecting' | 'connected' | 'disconnected';

// ── Fleet state (aggregated by the reducer) ─────────────────────────────────

export interface FleetState {
  wsStatus: WsConnectionStatus;
  pose: PoseData | null;
  state: RobotState | null;
  waypoints: WaypointPoint[];
  currentWp: number;
  plan: PlanPoint[];
}

// ── MAP_CONFIG shape (loaded via window.MAP_CONFIG from prepare_map.py) ──────

export interface MapConfig {
  image: string;       // relative URL to the map PNG
  width: number;       // canvas pixel width
  height: number;      // canvas pixel height
  resolution: number;  // metres / pixel
  origin: {
    x: number;         // world x of the bottom-left pixel (metres)
    y: number;         // world y of the bottom-left pixel (metres)
  };
}

declare global {
  interface Window {
    MAP_CONFIG?: MapConfig;
  }
}
