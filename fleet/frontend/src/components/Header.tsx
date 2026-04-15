import type { RobotState, WsConnectionStatus } from '../types';

interface HeaderProps {
  wsStatus: WsConnectionStatus;
  robotState: RobotState | null;
  pose: { x: number; y: number; yaw: number } | null;
}

// Maps robotState → CSS class suffix used in index.css
const STATE_LABEL: Record<RobotState, string> = {
  idle: 'IDLE',
  patrolling: 'PATROLLING',
  wait: 'WAIT',
  emergency: 'EMERGENCY',
  avoiding: 'AVOIDING',
  returning: 'RETURNING',
};

function rad2deg(rad: number): string {
  return (rad * (180 / Math.PI)).toFixed(1);
}

export function Header({ wsStatus, robotState, pose }: HeaderProps) {
  const stateClass = robotState ? `state-pill state-pill--${robotState}` : 'state-pill state-pill--idle';
  const stateLabel = robotState ? STATE_LABEL[robotState] : '—';

  const wsClass =
    wsStatus === 'connected'
      ? 'ws-badge ws-badge--connected'
      : wsStatus === 'connecting'
        ? 'ws-badge ws-badge--connecting'
        : 'ws-badge ws-badge--disconnected';

  const wsLabel =
    wsStatus === 'connected'
      ? 'connected'
      : wsStatus === 'connecting'
        ? 'connecting…'
        : 'disconnected';

  const poseText = pose
    ? `x=${pose.x.toFixed(2)}  y=${pose.y.toFixed(2)}  yaw=${rad2deg(pose.yaw)}°`
    : 'pose: —';

  return (
    <header className="header">
      <div className="header__brand">
        {/* Minimal radar-style icon */}
        <svg
          className="header__logo"
          width="28"
          height="28"
          viewBox="0 0 28 28"
          fill="none"
          aria-hidden="true"
        >
          <circle cx="14" cy="14" r="12" stroke="var(--accent)" strokeWidth="1.5" />
          <circle cx="14" cy="14" r="7" stroke="var(--accent)" strokeWidth="1" opacity="0.5" />
          <circle cx="14" cy="14" r="2.5" fill="var(--accent)" />
          <line x1="14" y1="14" x2="22" y2="6" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        <span className="header__title">Sentinel Patrol</span>
      </div>

      <div className="header__indicators">
        <span className={wsClass} aria-label={`WebSocket ${wsLabel}`}>
          <span className="ws-badge__dot" />
          {wsLabel}
        </span>

        <span className={stateClass}>{stateLabel}</span>

        <span className="header__pose">{poseText}</span>
      </div>
    </header>
  );
}
