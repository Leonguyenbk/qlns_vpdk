import { useState } from "react";
import toast from "react-hot-toast";
import { useCriteriaSets, useCriteriaSet, useKpiAdminMutations } from "../../../hooks/useKpi";
import { apiErrorMessage } from "../../../lib/api";
import { formatDate, todayISO } from "../../../lib/format";
import { CATALOG_STATUS_LABELS } from "../../../lib/constants";
import { Button, FormField, TextInput } from "../../../components/ui/primitives";
import { LoadingState, ErrorState, EmptyState } from "../../../components/ui/DataStates";

function CriterionNode({ node, depth = 0 }) {
  return (
    <li style={{ paddingLeft: depth * 16 }} className="py-1.5">
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className={depth === 0 ? "font-medium text-ink" : "text-ink-2"}>{node.name}</span>
        <span className="tabular shrink-0 text-ink">{node.max_points} đ</span>
      </div>
      {node.needs_confirmation && (
        <div className="text-xs text-warn-text">⚠ Cần cấp có thẩm quyền xác nhận trước khi áp dụng chính thức</div>
      )}
      {node.children?.length > 0 && (
        <ul className="border-l border-rule pl-2">
          {node.children.map((c) => <CriterionNode key={c.id} node={c} depth={depth + 1} />)}
        </ul>
      )}
    </li>
  );
}

function CriteriaSetCard({ cset }) {
  const [expanded, setExpanded] = useState(false);
  const { data: full } = useCriteriaSet(expanded ? cset.id : null);
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-medium text-ink">#{cset.id} — {cset.name}</div>
          <div className="text-xs text-muted">
            {CATALOG_STATUS_LABELS[cset.status] || cset.status} · hiệu lực từ {formatDate(cset.effective_from)}
          </div>
        </div>
        <Button variant="ghost" onClick={() => setExpanded((v) => !v)}>{expanded ? "Thu gọn" : "Xem chi tiết"}</Button>
      </div>
      {cset.notes && <p className="mt-2 text-xs text-muted">{cset.notes}</p>}
      {expanded && full && (
        <ul className="mt-3 divide-y divide-rule border-t border-rule pt-2">
          {full.criteria.map((c) => <CriterionNode key={c.id} node={c} />)}
        </ul>
      )}
    </div>
  );
}

export default function CriteriaSetsPage() {
  const { data, isLoading, isError, error, refetch } = useCriteriaSets();
  const m = useKpiAdminMutations();
  const [effectiveFrom, setEffectiveFrom] = useState(todayISO());

  const onCreateDefault = () => {
    m.createDefaultCriteriaSet.mutateAsync({ effective_from: effectiveFrom })
      .then(() => toast.success("Đã tạo bộ tiêu chí dự thảo đầy đủ theo tài liệu"))
      .catch((err) => toast.error(apiErrorMessage(err)));
  };

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  return (
    <div className="space-y-5">
      <div className="card space-y-3 p-4">
        <p className="text-sm text-ink-2">
          Tạo sẵn bộ tiêu chí đầy đủ (30 điểm tiêu chí chung + 70 điểm kết quả nhiệm vụ, cả khung viên chức
          quản lý và không giữ chức vụ quản lý) theo đúng số liệu tại tài liệu dự thảo — dùng làm điểm khởi
          đầu để chỉnh sửa khi ban hành Quy chế chính thức, thay vì phải nhập tay từ đầu.
        </p>
        <div className="flex flex-wrap items-end gap-2">
          <FormField label="Ngày hiệu lực"><TextInput type="date" value={effectiveFrom} onChange={(e) => setEffectiveFrom(e.target.value)} /></FormField>
          <Button disabled={m.createDefaultCriteriaSet.isPending} onClick={onCreateDefault}>
            + Tạo bộ tiêu chí dự thảo theo tài liệu
          </Button>
        </div>
      </div>

      {data.length === 0 ? (
        <EmptyState title="Chưa có bộ tiêu chí nào" />
      ) : (
        <div className="space-y-3">
          {data.map((c) => <CriteriaSetCard key={c.id} cset={c} />)}
        </div>
      )}
    </div>
  );
}
