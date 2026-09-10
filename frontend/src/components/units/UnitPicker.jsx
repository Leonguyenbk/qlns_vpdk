import { useEffect, useMemo, useState } from "react";
import { Select } from "../ui/primitives";

/**
 * Chọn đơn vị theo 2 bước: Phòng / Chi nhánh -> Bộ phận (tuỳ chọn).
 * Giá trị phát ra là id của Bộ phận nếu có chọn, ngược lại là id của Phòng / Chi nhánh.
 *
 * props:
 *  - units:    danh sách phẳng từ GET /units (mỗi phần tử có unit_type, parent_id)
 *  - value:    id đơn vị hiện tại (string | number | "")
 *  - onChange: (unitId: string) => void
 *  - error:    thông báo lỗi (hiển thị ở ô Phòng / Chi nhánh)
 */
export function UnitPicker({ units = [], value, onChange, error }) {
  const groups = useMemo(
    () =>
      units
        .filter((u) => ["HEAD_OFFICE", "DEPARTMENT", "BRANCH"].includes(u.unit_type))
        .sort((a, b) => a.name.localeCompare(b.name, "vi")),
    [units]
  );
  const byId = useMemo(() => new Map(units.map((u) => [String(u.id), u])), [units]);

  const [groupId, setGroupId] = useState("");
  const [sectionId, setSectionId] = useState("");

  // Đồng bộ khi value được set từ bên ngoài (vd nạp nhân sự để chuyển đơn vị).
  useEffect(() => {
    const u = byId.get(String(value ?? ""));
    if (!u) {
      setGroupId("");
      setSectionId("");
    } else if (u.unit_type === "SECTION") {
      setGroupId(String(u.parent_id ?? ""));
      setSectionId(String(u.id));
    } else {
      setGroupId(String(u.id));
      setSectionId("");
    }
  }, [value, byId]);

  const sections = useMemo(
    () =>
      units
        .filter((u) => u.unit_type === "SECTION" && String(u.parent_id) === String(groupId))
        .sort((a, b) => a.name.localeCompare(b.name, "vi")),
    [units, groupId]
  );

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <Select
        value={groupId}
        error={error}
        onChange={(e) => {
          const g = e.target.value;
          setGroupId(g);
          setSectionId("");
          onChange?.(g || "");
        }}
      >
        <option value="">-- Phòng / Chi nhánh --</option>
        {groups.map((u) => (
          <option key={u.id} value={u.id}>
            {u.name}
          </option>
        ))}
      </Select>

      <Select
        value={sectionId}
        disabled={!groupId || sections.length === 0}
        onChange={(e) => {
          const s = e.target.value;
          setSectionId(s);
          onChange?.(s || groupId || "");
        }}
      >
        <option value="">
          {!groupId
            ? "-- Chọn Phòng / Chi nhánh trước --"
            : sections.length === 0
              ? "(không có bộ phận)"
              : "-- Toàn Phòng / Chi nhánh --"}
        </option>
        {sections.map((u) => (
          <option key={u.id} value={u.id}>
            {u.name}
          </option>
        ))}
      </Select>
    </div>
  );
}
