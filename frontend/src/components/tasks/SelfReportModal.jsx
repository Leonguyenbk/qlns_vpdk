import { useState } from "react";
import toast from "react-hot-toast";
import { useCatalogGroups, useProducts } from "../../hooks/useKpi";
import { useSelfReportQuantity } from "../../hooks/useTasks";
import { Modal } from "../ui/Modal";
import { Button, FormField, Select } from "../ui/primitives";
import { apiErrorMessage } from "../../lib/api";

/** Tự khai khối lượng thủ tục hành chính xử lý theo lô (vd. văn thư chuyển hồ
 * sơ) — cộng dồn vào một nhiệm vụ duy nhất theo kỳ, không cần người giao việc
 * tạo từng nhiệm vụ nhỏ cho từng hồ sơ. Vẫn phải qua nghiệm thu như bình
 * thường trước khi tính vào KPI. */
export function SelfReportModal({ open, onClose }) {
  const [groupCode, setGroupCode] = useState("");
  const [productId, setProductId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [note, setNote] = useState("");
  const [lastResult, setLastResult] = useState(null);

  const { data: groups } = useCatalogGroups();
  const { data: products } = useProducts(groupCode ? { group_code: groupCode } : undefined);
  const selfReport = useSelfReportQuantity();

  const groupName = (code) => groups?.find((row) => row.code === code)?.name;

  const reset = () => {
    setProductId("");
    setQuantity("");
    setNote("");
    setLastResult(null);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    const qty = Number(quantity);
    if (!productId) {
      toast.error("Vui lòng chọn sản phẩm/thủ tục");
      return;
    }
    if (!qty || qty <= 0) {
      toast.error("Số lượng phải lớn hơn 0");
      return;
    }
    try {
      const resp = await selfReport.mutateAsync({
        product_id: Number(productId),
        quantity: qty,
        note: note || undefined,
      });
      const task = resp.data.data;
      setLastResult(task);
      setQuantity("");
      setNote("");
      toast.success("Đã ghi nhận khối lượng tự khai");
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  return (
    <Modal open={open} onClose={handleClose} title="Tự khai khối lượng theo kỳ" size="sm">
      <form onSubmit={onSubmit} className="grid gap-3">
        <p className="text-sm text-muted">
          Dùng cho thủ tục hành chính xử lý theo lô (vd. chuyển hồ sơ, tiếp nhận…) — khai
          nhiều lần trong kỳ, hệ thống tự cộng dồn vào một nhiệm vụ duy nhất. Cuối kỳ vẫn
          cần nộp và được người có thẩm quyền nghiệm thu như bình thường.
        </p>

        <FormField label="Nhóm sản phẩm" hint="Để lọc danh sách bên dưới, không bắt buộc">
          <Select value={groupCode} onChange={(e) => { setGroupCode(e.target.value); setProductId(""); }}>
            <option value="">Tất cả nhóm</option>
            {groups?.map((g) => (
              <option key={g.code} value={g.code}>{g.code} — {g.name}</option>
            ))}
          </Select>
        </FormField>

        <FormField label="Sản phẩm / thủ tục" required>
          <Select value={productId} onChange={(e) => setProductId(e.target.value)}>
            <option value="">-- Chọn sản phẩm/thủ tục --</option>
            {products?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.code} — {p.name}{!groupCode ? ` (${groupName(p.group_code) || p.group_code})` : ""}
              </option>
            ))}
          </Select>
        </FormField>

        <FormField label="Số lượng" required>
          <input
            type="number"
            step="any"
            min="0"
            className="input"
            placeholder="Số hồ sơ/thủ tục đã xử lý"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
          />
        </FormField>

        <FormField label="Ghi chú" hint="Không bắt buộc — vd. khoảng thời gian, minh chứng">
          <textarea
            className="input"
            rows={2}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
        </FormField>

        {lastResult && (
          <div className="rounded-lg border border-rule bg-paper-2 px-3 py-2 text-sm">
            Đã cộng dồn — tổng khối lượng tự khai kỳ này:{" "}
            <span className="font-semibold text-ink">
              {lastResult.assigned_workload} {lastResult.workload_unit}
            </span>
          </div>
        )}

        <div className="mt-1 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={handleClose}>Đóng</Button>
          <Button type="submit" disabled={selfReport.isPending}>
            {selfReport.isPending ? "Đang lưu…" : "Khai thêm"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
