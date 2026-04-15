import { useFleetSocket } from './hooks/useFleetSocket';
import { Header } from './components/Header';
import { MapCanvas } from './components/MapCanvas';
import type { MapConfig } from './types';

const cfg = window.MAP_CONFIG as MapConfig | undefined;

export default function App() {
  const { wsStatus, pose, state, waypoints, currentWp, plan } = useFleetSocket();

  if (!cfg) {
    return (
      <div className="no-config">
        <p>
          <strong>map_config.js</strong> not found.
          <br />
          Run <code>prepare_map.py</code> first, then reload.
        </p>
      </div>
    );
  }

  return (
    <div className="app">
      <Header wsStatus={wsStatus} robotState={state} pose={pose} />
      <main className="map-area">
        <MapCanvas
          cfg={cfg}
          pose={pose}
          plan={plan}
          waypoints={waypoints}
          currentWp={currentWp}
        />
      </main>
    </div>
  );
}
