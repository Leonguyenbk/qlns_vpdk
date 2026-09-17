import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useCan } from "../../components/Can";
import { useScore, useScoreMutations } from "../../hooks/useKpi";
import { apiErrorMessage } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import { PERMISSIONS, KPI_SCORE_STATUS_LABELS, KPI_SCORE_STATUS_BADGE } from "../../lib/constants";
import { PageHeader, Button, Badge, TextInput } from "../../components/ui/primitives";
import { LoadingState, ErrorState } from "../../components/ui/DataStates";

function DetailRow({ d }) {
  return (
    <tr className="border-b border-rule last:border-0">
      <td className="px-4 py-3">
        <div className="font-medium text-ink">{d.criteria_name}</div>
        {d.needs_confirmation && (
          <div className="mt-1 text-xs text-warn-text">
            ⚠ Quy tắc xác định tử số/mẫu số cho tiêu chí này là suy luận riêng của phần mềm, chưa được xác nhận chính thức.
          </div>
        )}
      </td>
      <td className="px-4 py-3 text-ink-2">{d.max_points}</td>
      <td className="px-4 py-3 text-ink-2">
        {d.no_data ? (
          <span className="text-muted">Chưa đủ dữ liệu/Chờ xác nhận</span>
        ) : d.ratio_percent !== null ? (
          `${d.ratio_percent}% (${d.raw_numerator}/${d.raw_denominator})`
        ) : "—"}
      </td>
      <td className="px-4 py-3 font-semibold text-ink">{d.points_earned ?? "—"}</td>
      <td className="px-4 py-3 text-xs text-ink-2">{d.evaluator_comment || "—"}</td>
    </tr>
  );
}

export default function KpiScoreDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { can } = useCan();
  const { data: score, isLoading, isError, error, refetch } = useScore(id);
  const m = useScoreMutations(id);
  const [officialRating, setOfficialRating] = useState("");
  const [adjustReason, setAdjustReason] = useState("");
  const [commentText, setCommentText] = useState("");

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const wrap = (promise, okMsg) =>
    promise.then(() => { toast.success(okMsg); refetch(); }).catch((err) => toast.error(apiErrorMessage(err)));

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow={`Kết quả KPI #${score.id}`}
        title={score.user_full_name || `Tài khoản #${score.user_id}`}
        subtitle={`${score.position_name_snapshot || ""} — kỳ #${score.period_id} (dự thảo/thí điểm, chưa đối chiếu văn bản chính thức)`}
        actions={
          <>
            <span className={`badge ${KPI_SCORE_STATUS_BADGE[score.status] || "badge-neutral"} self-center`}>
              {KPI_SCORE_STATUS_LABELS[score.status] || score.status}
            </span>
            <Button variant="secondary" onClick={() => navigate(-1)}>Quay lại</Button>
          </>
        }
      />

      <div className="grid gap-3 sm:grid-cols-4">
        <div className="card p-4">
          <div className="text-xs text-muted">Điểm tạm tính</div>
          <div className="text-xl font-bold text-ink">{score.provisional_total ?? "—"}</div>
        </div>
        <div className="card p-4">
          <div className="text-xs text-muted">Tự đánh giá</div>
          <div className="text-xl font-bold text-ink">{score.self_assessed_total ?? "—"}</div>
        </div>
        <div className="card p-4">
          <div className="text-xs text-muted">Điểm xác nhận</div>
          <div className="text-xl font-bold text-ink">{score.confirmed_total ?? "—"}</div>
        </div>
        <div className="card p-4">
          <div className="text-xs text-muted">Mức đề xuất</div>
          <div className="text-sm font-semibold text-ink">{score.proposed_rating || "—"}</div>
        </div>
      </div>

      <section className="card overflow-hidden">
        <div className="border-b border-rule px-5 py-3">
          <h3 className="text-sm font-semibold text-ink">Chi tiết từng tiêu chí</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="tabular min-w-full text-sm">
            <thead>
              <tr className="border-b border-rule-2">
                {["Tiêu chí", "Điểm tối đa", "Tỷ lệ % (tử số/mẫu số)", "Điểm đạt", "Nhận xét"].map((h) => (
                  <th key={h} className="eyebrow px-4 py-2.5 text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {score.details.map((d) => <DetailRow key={d.id} d={d} />)}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card p-5">
        <h3 className="mb-3 text-sm font-semibold text-ink">Quy trình đánh giá</h3>
        <div className="flex flex-wrap gap-2">
          {can(PERMISSIONS.KPI_SELF_ASSESS) && score.status === "DRAFT" && (
            <Button disabled={m.selfAssess.isPending} onClick={() => wrap(m.selfAssess.mutateAsync({}), "Đã lưu tự đánh giá")}>
              Tự đánh giá (chốt điểm tạm tính hiện tại)
            </Button>
          )}
          {can(PERMISSIONS.KPI_REVIEW) && !score.is_locked && (
            <Button variant="secondary" disabled={m.review.isPending} onClick={() => wrap(m.review.mutateAsync({}), "Đã lưu theo dõi, đánh giá")}>
              Xác nhận theo dõi, đánh giá
            </Button>
          )}
          {can(PERMISSIONS.KPI_AGGREGATE) && !score.is_locked && (
            <Button variant="secondary" disabled={m.aggregate.isPending} onClick={() => wrap(m.aggregate.mutateAsync({}), "Đã tổng hợp")}>
              Tổng hợp
            </Button>
          )}
        </div>

        {can(PERMISSIONS.KPI_APPROVE) && !score.is_locked && (
          <div className="mt-4 flex flex-wrap items-end gap-2 border-t border-rule pt-4">
            <div className="w-64">
              <label className="label">Mức xếp loại chính thức (bắt buộc chọn — hệ thống không tự động)</label>
              <select className="input" value={officialRating} onChange={(e) => setOfficialRating(e.target.value)}>
                <option value="">— Chọn mức xếp loại —</option>
                <option value="Hoàn thành xuất sắc nhiệm vụ">Hoàn thành xuất sắc nhiệm vụ</option>
                <option value="Hoàn thành tốt nhiệm vụ">Hoàn thành tốt nhiệm vụ</option>
                <option value="Hoàn thành nhiệm vụ">Hoàn thành nhiệm vụ</option>
                <option value="Không hoàn thành nhiệm vụ">Không hoàn thành nhiệm vụ</option>
              </select>
            </div>
            <Button
              disabled={!officialRating || m.approve.isPending}
              onClick={() => wrap(m.approve.mutateAsync({ official_rating: officialRating }), "Đã phê duyệt xếp loại chính thức")}
            >
              Phê duyệt & khoá kết quả
            </Button>
          </div>
        )}

        {can(PERMISSIONS.KPI_ADJUST) && score.is_locked && (
          <div className="mt-4 flex flex-wrap items-end gap-2 border-t border-rule pt-4">
            <TextInput className="w-80" placeholder="Lý do điều chỉnh (sai sót phát hiện sau khi xếp loại)…"
                       value={adjustReason} onChange={(e) => setAdjustReason(e.target.value)} />
            <Button
              variant="danger" disabled={!adjustReason.trim() || m.adjust.isPending}
              onClick={() => wrap(m.adjust.mutateAsync({ reason: adjustReason }), "Đã tạo kết quả điều chỉnh — bản gốc vẫn được giữ nguyên")
                .then(() => setAdjustReason(""))}
            >
              Tạo kết quả điều chỉnh (Mẫu số 15)
            </Button>
          </div>
        )}

        {score.is_locked && (
          <p className="mt-3 text-xs text-muted">
            Kết quả đã khoá. Muốn sửa phải dùng chức năng điều chỉnh — bản gốc luôn được giữ nguyên trong hồ sơ để truy vết.
          </p>
        )}
      </section>

      {score.history?.length > 0 && (
        <section className="card p-5">
          <h3 className="mb-3 text-sm font-semibold text-ink">Lịch sử kết quả đã thay thế</h3>
          <ul className="divide-y divide-rule text-sm">
            {score.history.map((h) => (
              <li key={h.id} className="py-2">
                <Badge className="badge-neutral">#{h.id}</Badge>{" "}
                {h.official_rating || h.status} — {h.replace_reason || "—"}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="card p-5">
        <h3 className="mb-3 text-sm font-semibold text-ink">Ý kiến / giải trình / biên bản họp</h3>
        <ul className="mb-3 space-y-2">
          {score.comments.length === 0 && <li className="text-sm text-muted">Chưa có ý kiến nào.</li>}
          {score.comments.map((c) => (
            <li key={c.id} className="text-sm">
              <span className="font-medium text-ink">{c.author_role_label || "Người dùng"}</span>{" "}
              <span className="text-xs text-muted">{formatDateTime(c.created_at)}</span>
              <div className="text-ink-2">{c.content}</div>
            </li>
          ))}
        </ul>
        <div className="flex gap-2">
          <TextInput placeholder="Nhập ý kiến / giải trình…" value={commentText} onChange={(e) => setCommentText(e.target.value)} />
          <Button
            disabled={!commentText.trim() || m.addComment.isPending}
            onClick={() => wrap(m.addComment.mutateAsync({ content: commentText, comment_type: "EXPLANATION" }), "Đã gửi ý kiến")
              .then(() => setCommentText(""))}
          >
            Gửi
          </Button>
        </div>
      </section>
    </div>
  );
}
