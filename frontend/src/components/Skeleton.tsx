export function SkeletonLine({ width = "100%" }: { width?: string }) {
  return <div className="skeleton skeleton-line" style={{ width }} aria-hidden />;
}

export function RankingSkeleton() {
  return (
    <ul className="ranking-list" aria-busy="true" aria-label="랭킹 불러오는 중">
      {Array.from({ length: 6 }).map((_, i) => (
        <li key={i} className="ranking-item">
          <div className="skeleton skeleton-badge" aria-hidden />
          <div style={{ flex: 1 }}>
            <SkeletonLine width="60%" />
            <SkeletonLine width="40%" />
          </div>
        </li>
      ))}
    </ul>
  );
}
