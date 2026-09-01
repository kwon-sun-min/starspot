import type { SpotSummary } from "../api/types";
import { CATEGORY_LABEL, scoreColor, scoreLabel } from "../lib/score";

interface Props {
  spots: SpotSummary[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  onOpenDetail: (id: number) => void;
}

export function RankingList({ spots, selectedId, onSelect, onOpenDetail }: Props) {
  if (spots.length === 0) {
    return <p className="empty">반경 안에 후보지가 없어요. 반경을 넓혀보세요.</p>;
  }
  return (
    <ol className="ranking-list" aria-label="관측 점수 랭킹">
      {spots.map((s, idx) => (
        <li
          key={s.id}
          className={`ranking-item${s.id === selectedId ? " selected" : ""}`}
          onClick={() => onSelect(s.id)}
          onDoubleClick={() => onOpenDetail(s.id)}
        >
          <span className="rank-no">{idx + 1}</span>
          <span
            className="score-badge"
            style={{ background: scoreColor(s.score) }}
            title={scoreLabel(s.score)}
          >
            {s.score}
          </span>
          <div className="ranking-meta">
            <div className="ranking-name">{s.name}</div>
            <div className="ranking-sub">
              {CATEGORY_LABEL[s.category] ?? s.category} · {s.distance_km}km
            </div>
          </div>
          <button
            className="detail-btn"
            onClick={(e) => {
              e.stopPropagation();
              onOpenDetail(s.id);
            }}
            aria-label={`${s.name} 상세 보기`}
          >
            상세
          </button>
        </li>
      ))}
    </ol>
  );
}
