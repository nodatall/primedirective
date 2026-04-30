import { useEffect, useMemo, useRef, type DragEvent } from 'react';
import ButtonBase from '@mui/material/ButtonBase';
import type { CardDTO } from '../../contracts';

export function BoardCard({ card, onOpen, onDragStart }: { card: CardDTO; onOpen: (card: CardDTO) => void; onDragStart?: (card: CardDTO, event: DragEvent<HTMLElement>) => void }) {
  return (
    <ButtonBase className={`card card--${card.status.toLowerCase().replaceAll(' ', '-')}`} draggable onClick={() => onOpen(card)} onDragStart={(event) => onDragStart?.(card, event)}>
      <div className="card__rail" />
      <div className="card__topline"><span>{card.taskType}</span>{card.autoMerge ? <span className="pill">auto-merge</span> : <span className="pill muted">manual PR</span>}</div>
      <strong>{card.title}</strong>
      <p>{card.blockerSummary ?? card.instructions}</p>
      <div className="card__meta"><span>{card.branch ?? 'branch pending'}</span>{card.status === 'Running' ? <RoseThreeLoader /> : <span>{card.status}</span>}</div>
    </ButtonBase>
  );
}

const roseConfig = {
  particleCount: 76,
  trailSpan: 0.31,
  durationMs: 5300,
  rotationDurationMs: 28000,
  pulseDurationMs: 4400,
  strokeWidth: 4.6,
  roseA: 9.2,
  roseABoost: 0.6,
  roseBreathBase: 0.72,
  roseBreathBoost: 0.28,
  roseScale: 3.25
};

function RoseThreeLoader() {
  const groupRef = useRef<SVGGElement | null>(null);
  const pathRef = useRef<SVGPathElement | null>(null);
  const particleRefs = useRef<Array<SVGCircleElement | null>>([]);
  const particleIndexes = useMemo(() => Array.from({ length: roseConfig.particleCount }, (_, index) => index), []);

  useEffect(() => {
    let frame = 0;
    const startedAt = performance.now();
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function render(now: number) {
      const time = reducedMotion ? 0 : now - startedAt;
      const progress = (time % roseConfig.durationMs) / roseConfig.durationMs;
      const detailScale = getDetailScale(time);
      groupRef.current?.setAttribute('transform', `rotate(${getRotation(time)} 50 50)`);
      pathRef.current?.setAttribute('d', buildPath(detailScale));
      particleRefs.current.forEach((node, index) => {
        if (!node) return;
        const particle = getParticle(index, progress, detailScale);
        node.setAttribute('cx', particle.x.toFixed(2));
        node.setAttribute('cy', particle.y.toFixed(2));
        node.setAttribute('r', particle.radius.toFixed(2));
        node.setAttribute('opacity', particle.opacity.toFixed(3));
      });
      if (!reducedMotion) frame = requestAnimationFrame(render);
    }

    render(startedAt);
    return () => cancelAnimationFrame(frame);
  }, []);

  return (
    <span className="card__running-loader" aria-label="Running" title="Running">
      <svg viewBox="0 0 100 100" fill="none" aria-hidden="true" focusable="false">
        <g ref={groupRef}>
          <path ref={pathRef} stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth={roseConfig.strokeWidth} opacity="0.1" />
          {particleIndexes.map((index) => (
            <circle ref={(node) => { particleRefs.current[index] = node; }} fill="currentColor" key={index} />
          ))}
        </g>
      </svg>
    </span>
  );
}

function normalizeProgress(progress: number) {
  return ((progress % 1) + 1) % 1;
}

function getDetailScale(time: number) {
  const pulseProgress = (time % roseConfig.pulseDurationMs) / roseConfig.pulseDurationMs;
  const pulseAngle = pulseProgress * Math.PI * 2;
  return 0.52 + ((Math.sin(pulseAngle + 0.55) + 1) / 2) * 0.48;
}

function getRotation(time: number) {
  return -((time % roseConfig.rotationDurationMs) / roseConfig.rotationDurationMs) * 360;
}

function getRosePoint(progress: number, detailScale: number) {
  const t = progress * Math.PI * 2;
  const a = roseConfig.roseA + detailScale * roseConfig.roseABoost;
  const r = a * (roseConfig.roseBreathBase + detailScale * roseConfig.roseBreathBoost) * Math.cos(3 * t);
  return {
    x: 50 + Math.cos(t) * r * roseConfig.roseScale,
    y: 50 + Math.sin(t) * r * roseConfig.roseScale
  };
}

function buildPath(detailScale: number, steps = 480) {
  return Array.from({ length: steps + 1 }, (_, index) => {
    const point = getRosePoint(index / steps, detailScale);
    return `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`;
  }).join(' ');
}

function getParticle(index: number, progress: number, detailScale: number) {
  const tailOffset = index / (roseConfig.particleCount - 1);
  const point = getRosePoint(normalizeProgress(progress - tailOffset * roseConfig.trailSpan), detailScale);
  const fade = Math.pow(1 - tailOffset, 0.56);
  return {
    x: point.x,
    y: point.y,
    radius: 0.9 + fade * 2.7,
    opacity: 0.04 + fade * 0.96
  };
}
