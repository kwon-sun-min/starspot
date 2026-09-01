interface Props {
  value: number;
  onChange: (km: number) => void;
}

export function RadiusSlider({ value, onChange }: Props) {
  return (
    <div className="radius-slider">
      <label htmlFor="radius">
        반경 <strong>{value}km</strong>
      </label>
      <input
        id="radius"
        type="range"
        min={20}
        max={200}
        step={10}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-valuetext={`${value}킬로미터`}
      />
    </div>
  );
}
