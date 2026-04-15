import { useEffect, useRef } from 'react';
import type { MapConfig, PlanPoint, PoseData, WaypointPoint } from '../types';

interface MapCanvasProps {
  cfg: MapConfig;
  pose: PoseData | null;
  plan: PlanPoint[];
  waypoints: WaypointPoint[];
  currentWp: number;
}

// World (metres) → canvas pixel. ROS y goes up, canvas y goes down.
function worldToPixel(
  wx: number,
  wy: number,
  cfg: MapConfig,
): [number, number] {
  const px = (wx - cfg.origin.x) / cfg.resolution;
  const py = cfg.height - (wy - cfg.origin.y) / cfg.resolution;
  return [px, py];
}

export function MapCanvas({ cfg, pose, plan, waypoints, currentWp }: MapCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mapImgRef = useRef<HTMLImageElement | null>(null);
  const mapReadyRef = useRef(false);

  // Load map image once
  useEffect(() => {
    const img = new Image();
    img.onload = () => {
      mapReadyRef.current = true;
      mapImgRef.current = img;
      renderFrame();
    };
    img.onerror = () => {
      console.warn('[MapCanvas] Failed to load map image:', cfg.image);
    };
    img.src = cfg.image;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cfg.image]);

  // Re-render whenever data changes
  useEffect(() => {
    renderFrame();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pose, plan, waypoints, currentWp]);

  function renderFrame() {
    const canvas = canvasRef.current;
    if (!canvas || !mapReadyRef.current || !mapImgRef.current) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(mapImgRef.current, 0, 0);

    drawWaypoints(ctx);
    drawPlan(ctx);
    drawRobot(ctx);
  }

  function drawWaypoints(ctx: CanvasRenderingContext2D) {
    if (!waypoints || waypoints.length === 0) return;

    // Dashed loop connecting waypoints
    ctx.strokeStyle = 'rgba(255, 200, 100, 0.55)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([5, 4]);
    ctx.beginPath();
    for (let i = 0; i < waypoints.length; i++) {
      const [px, py] = worldToPixel(waypoints[i].x, waypoints[i].y, cfg);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    // Close the loop
    const [px0, py0] = worldToPixel(waypoints[0].x, waypoints[0].y, cfg);
    ctx.lineTo(px0, py0);
    ctx.stroke();
    ctx.setLineDash([]);

    // Numbered markers; current target highlighted
    for (let i = 0; i < waypoints.length; i++) {
      const [px, py] = worldToPixel(waypoints[i].x, waypoints[i].y, cfg);
      const isCurrent = i === currentWp;
      const r = isCurrent ? 11 : 7;

      ctx.fillStyle = isCurrent ? '#ffa040' : '#ffd780';
      ctx.strokeStyle = '#442200';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(px, py, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = '#1a1a1a';
      ctx.font = `bold ${isCurrent ? 12 : 10}px "Geist Mono", monospace`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(String(i + 1), px, py);
    }
  }

  function drawPlan(ctx: CanvasRenderingContext2D) {
    if (!plan || plan.length < 2) return;
    ctx.strokeStyle = 'rgba(100, 180, 255, 0.85)';
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.beginPath();
    for (let i = 0; i < plan.length; i++) {
      const [px, py] = worldToPixel(plan[i].x, plan[i].y, cfg);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();
  }

  function drawRobot(ctx: CanvasRenderingContext2D) {
    if (!pose) return;
    const [px, py] = worldToPixel(pose.x, pose.y, cfg);
    const r = 8;

    const dx = Math.cos(pose.yaw) * (r * 2);
    const dy = -Math.sin(pose.yaw) * (r * 2); // canvas y is flipped

    // Heading arrow
    ctx.strokeStyle = '#00ff88';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(px, py);
    ctx.lineTo(px + dx, py + dy);
    ctx.stroke();

    // Robot circle
    ctx.fillStyle = '#00ff88';
    ctx.beginPath();
    ctx.arc(px, py, r, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#003322';
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }

  return (
    <canvas
      ref={canvasRef}
      className="map-canvas"
      width={cfg.width}
      height={cfg.height}
    />
  );
}
