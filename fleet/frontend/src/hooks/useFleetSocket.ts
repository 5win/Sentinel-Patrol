import { useEffect, useReducer, useRef } from 'react';
import type {
  FleetState,
  PoseData,
  PlanPoint,
  RobotState,
  WaypointPoint,
  WsConnectionStatus,
} from '../types';

// ── Action types ─────────────────────────────────────────────────────────────

type Action =
  | { type: 'WS_STATUS'; payload: WsConnectionStatus }
  | { type: 'POSE'; payload: PoseData }
  | { type: 'PLAN'; payload: PlanPoint[] }
  | { type: 'STATE'; payload: RobotState }
  | { type: 'WAYPOINTS'; payload: WaypointPoint[] }
  | { type: 'CURRENT_WP'; payload: number };

// ── Reducer ──────────────────────────────────────────────────────────────────

const initialState: FleetState = {
  wsStatus: 'connecting',
  pose: null,
  state: null,
  waypoints: [],
  currentWp: -1,
  plan: [],
};

function fleetReducer(state: FleetState, action: Action): FleetState {
  switch (action.type) {
    case 'WS_STATUS':
      return { ...state, wsStatus: action.payload };
    case 'POSE':
      return { ...state, pose: action.payload };
    case 'PLAN':
      return { ...state, plan: action.payload };
    case 'STATE':
      return { ...state, state: action.payload };
    case 'WAYPOINTS':
      return { ...state, waypoints: action.payload };
    case 'CURRENT_WP':
      return { ...state, currentWp: action.payload };
    default:
      return state;
  }
}

// ── Hook ─────────────────────────────────────────────────────────────────────

const RECONNECT_DELAY_MS = 1000;

export function useFleetSocket(): FleetState {
  const [fleetState, dispatch] = useReducer(fleetReducer, initialState);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Keep a ref so the cleanup function can always access the current ws instance
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;

    function connect() {
      if (!isMountedRef.current) return;

      dispatch({ type: 'WS_STATUS', payload: 'connecting' });

      const ws = new WebSocket(`ws://${location.host}/ws`);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isMountedRef.current) return;
        dispatch({ type: 'WS_STATUS', payload: 'connected' });
      };

      ws.onclose = () => {
        if (!isMountedRef.current) return;
        dispatch({ type: 'WS_STATUS', payload: 'disconnected' });
        reconnectTimerRef.current = setTimeout(connect, RECONNECT_DELAY_MS);
      };

      ws.onerror = () => {
        // onclose will fire next, which triggers reconnect
      };

      ws.onmessage = (ev: MessageEvent) => {
        if (!isMountedRef.current) return;
        try {
          const msg = JSON.parse(ev.data as string) as { type: string; data: unknown };
          switch (msg.type) {
            case 'pose':
              dispatch({ type: 'POSE', payload: msg.data as PoseData });
              break;
            case 'plan':
              dispatch({ type: 'PLAN', payload: msg.data as PlanPoint[] });
              break;
            case 'state':
              dispatch({ type: 'STATE', payload: (msg.data as string).toLowerCase() as RobotState });
              break;
            case 'waypoints':
              dispatch({ type: 'WAYPOINTS', payload: msg.data as WaypointPoint[] });
              break;
            case 'current_wp':
              dispatch({ type: 'CURRENT_WP', payload: msg.data as number });
              break;
            default:
              console.debug('[fleet-ws] unhandled message type:', msg.type);
          }
        } catch (err) {
          console.warn('[fleet-ws] failed to parse message:', err);
        }
      };
    }

    connect();

    return () => {
      isMountedRef.current = false;
      if (reconnectTimerRef.current !== null) {
        clearTimeout(reconnectTimerRef.current);
      }
      wsRef.current?.close();
    };
  }, []);

  return fleetState;
}
