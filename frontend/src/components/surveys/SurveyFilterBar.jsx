import { useUnits } from "../../hooks/useUnits";
import { DATE_PRESET_LABELS } from "../../lib/constants";
import { Select, TextInput } from "../ui/primitives";

export function SurveyFilterBar({ filters, onChange, branchOnly = false }) {
  const { data: units } = useUnits({ only_active: true });
  const usingCustomRange = !!(filters.date_from || filters.date_to);

  return (
    <div className="mb-5 flex flex-wrap items-end gap-3">
      {!branchOnly && (
        <>
          <div>
            <label className="label">Khoảng thời gian</label>
            <Select
              value={usingCustomRange ? "" : filters.preset || ""}
              onChange={(e) => onChange({ preset: e.target.value, date_from: "", date_to: "" })}
              className="w-40"
            >
              <option value="">Tất cả</option>
              {Object.entries(DATE_PRESET_LABELS).map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label className="label">Từ ngày</label>
            <TextInput
              type="date"
              value={filters.date_from || ""}
              onChange={(e) => onChange({ date_from: e.target.value, preset: "" })}
            />
          </div>
          <div>
            <label className="label">Đến ngày</label>
            <TextInput
              type="date"
              value={filters.date_to || ""}
              onChange={(e) => onChange({ date_to: e.target.value, preset: "" })}
            />
          </div>
        </>
      )}
      <div>
        <label className="label">Chi nhánh</label>
        <Select
          value={filters.branch_id || ""}
          onChange={(e) => onChange({ branch_id: e.target.value })}
          className="w-56"
        >
          <option value="">Tất cả chi nhánh</option>
          {units?.map((u) => (
            <option key={u.id} value={u.id}>
              {u.path || u.name}
            </option>
          ))}
        </Select>
      </div>
    </div>
  );
}
