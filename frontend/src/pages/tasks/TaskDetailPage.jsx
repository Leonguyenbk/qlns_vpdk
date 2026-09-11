import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../../auth/AuthContext";
import { useCan } from "../../components/Can";
import { useTask, useTaskMutations, useAssignablePeople } from "../../hooks/useTasks";
import { apiErrorMessage } from "../../lib/api";
import { formatDate, formatDateTime } from "../../lib/format";
import {
  PERMISSIONS,
  TASK_STATUS_LABELS,
  TASK_STATUS_BADGE,
  TASK_PRIORITY_LABELS,
  TASK_PAUSE_REASON_LABELS,
} from "../../lib/constants";
import { PageHeader, Button, Badge, Select, Textarea, TextInput } from "../../components/ui/primitives";
import { LoadingState, ErrorState } from "../../components/ui/DataStates";

function Section({ title, children, actions }) {
  return (
    <section className="card p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-ink">{title}</h3>
        {actions}
      </div>
      {children}
    </section>
  );
}

function Field({ label, value }) {
  return (
    <div>
      <div className="text-xs text-muted">{label}</div>
      <div className="text-sm text-ink-2">{value ?? "—"}</div>
    </div>
  );
}

export default function TaskDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { can } = useCan();
  const { data: task, isLoading, isError, error, refetch } = useTask(id);
  const m = useTaskMutations(id);

  const [progress, setProgress] = useState(0);
  const [note, setNote] = useState("");
  const [resultSummary, setResultSummary] = useState("");
  const [qualityLevel, setQualityLevel] = useState("5");
  const [returnReason, setReturnReason] = useState("");
  const [newDeadline, setNewDeadline] = useState("");
  const [deadlineReason, setDeadlineReason] = useState("");
  const [blockerReason, setBlockerReason] = useState("WAITING_CITIZEN");
  const [blockerNote, setBlockerNote] = useState("");
  const [commentText, setCommentText] = useState("");
  const [assignSearch, setAssignSearch] = useState("");
  const [assignUserId, setAssignUserId] = useState("");
  const [assignRole, setAssignRole] = useState("COLLABORATOR");
  const [assignContribution, setAssignContribution] = useState("");
  const { data: candidates } = useAssignablePeople({ search: assignSearch });

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={refetch} />;

  const isParticipant = task.assignments.some((a) => a.user_id === user?.id);
  const canAccept = can(PERMISSIONS.TASK_ACCEPT);
  const canManage = can(PERMISSIONS.TASK_MANAGE);
  const canAssign = can(PERMISSIONS.TASK_ASSIGN);

  const wrap = (promise, okMsg) =>
    promise.then(() => toast.success(okMsg)).catch((err) => toast.error(apiErrorMessage(err)));

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow={task.code}
        title={task.name}
        subtitle={task.description}
        actions={
          <>
            <span className={`badge ${TASK_STATUS_BADGE[task.status] || "badge-neutral"} self-center`}>
              {TASK_STATUS_LABELS[task.status] || task.status}
            </span>
            {task.is_overdue && <Badge className="badge-danger self-center">Quá hạn</Badge>}
            <Button variant="secondary" onClick={() => navigate(-1)}>Quay lại</Button>
          </>
        }
      />

      <div className="grid gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <Section title="Thông tin nhiệm vụ">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Mức ưu tiên" value={TASK_PRIORITY_LABELS[task.priority]} />
              <Field label="Nguồn" value={task.source} />
              <Field label="Đơn vị giao việc" value={task.assigning_unit?.name} />
              <Field label="Đơn vị thực hiện" value={task.executing_unit?.name} />
              <Field label="Ngày giao" value={formatDate(task.assigned_date)} />
              <Field label="Hạn ban đầu" value={formatDate(task.original_deadline)} />
              <Field label="Hạn gia hạn" value={formatDate(task.extended_deadline)} />
              <Field label="Loại hạn" value={task.deadline_type === "TTHC" ? "Thủ tục hành chính" : "Nội bộ"} />
              <Field label="Khối lượng giao" value={task.assigned_workload ? `${task.assigned_workload} ${task.workload_unit || ""}` : "—"} />
              <Field label="Tiến độ" value={`${task.progress_percent}%`} />
              <Field label="Chất lượng nghiệm thu" value={task.quality_level ? `${task.quality_level}/5` : "Chưa nghiệm thu"} />
              <Field label="Số lần yêu cầu làm lại" value={task.rework_count} />
            </div>
            {task.output_description && <div className="mt-4"><Field label="Yêu cầu đầu ra" value={task.output_description} /></div>}
            {task.quality_standard && <div className="mt-2"><Field label="Tiêu chuẩn chất lượng" value={task.quality_standard} /></div>}
            {task.result_summary && <div className="mt-2"><Field label="Tóm tắt kết quả" value={task.result_summary} /></div>}
          </Section>

          <Section title="Người thực hiện">
            <ul className="divide-y divide-rule">
              {task.assignments.map((a) => (
                <li key={a.id} className="flex items-center justify-between py-2 text-sm">
                  <div>
                    <span className="font-medium text-ink">{a.user_full_name || `#${a.user_id}`}</span>{" "}
                    <span className="text-xs text-muted">
                      ({a.role_in_task === "LEAD" ? "Chủ trì" : a.role_in_task === "REVIEWER" ? "Nghiệm thu" : "Phối hợp"})
                    </span>
                    {a.contribution_percent != null && (
                      <span className="ml-1 text-xs text-muted">— đóng góp {a.contribution_percent}%</span>
                    )}
                    <div className="text-xs text-muted">{a.position_name_snapshot || "—"}</div>
                  </div>
                  {canAssign && (
                    <Button
                      variant="ghost" className="px-2 py-1 text-xs text-danger"
                      onClick={() => wrap(m.removeAssignment.mutateAsync({ assignmentId: a.id, body: { reason: "Điều chỉnh phân công" } }), "Đã gỡ khỏi nhiệm vụ")}
                    >
                      Gỡ
                    </Button>
                  )}
                </li>
              ))}
            </ul>
            {canAssign && (
              <div className="mt-3 grid gap-2 border-t border-rule pt-3 sm:grid-cols-4">
                <TextInput placeholder="Tìm người…" value={assignSearch} onChange={(e) => setAssignSearch(e.target.value)} />
                <Select value={assignUserId} onChange={(e) => setAssignUserId(e.target.value)}>
                  <option value="">Chọn người</option>
                  {candidates?.map((c) => (
                    <option key={c.user_id} value={c.user_id}>{c.full_name} — {c.unit_name || "?"}</option>
                  ))}
                </Select>
                <Select value={assignRole} onChange={(e) => setAssignRole(e.target.value)}>
                  <option value="COLLABORATOR">Phối hợp</option>
                  <option value="LEAD">Chủ trì</option>
                  <option value="REVIEWER">Nghiệm thu</option>
                </Select>
                <div className="flex gap-2">
                  <TextInput type="number" placeholder="% đóng góp" value={assignContribution}
                             onChange={(e) => setAssignContribution(e.target.value)} />
                  <Button
                    disabled={!assignUserId || m.addAssignment.isPending}
                    onClick={() => wrap(m.addAssignment.mutateAsync({
                      user_id: Number(assignUserId), role_in_task: assignRole,
                      contribution_percent: assignContribution ? Number(assignContribution) : null,
                    }), "Đã thêm người thực hiện").then(() => { setAssignUserId(""); setAssignContribution(""); })}
                  >
                    Thêm
                  </Button>
                </div>
              </div>
            )}
          </Section>

          <Section title="Nhật ký & bình luận">
            <ul className="max-h-96 space-y-3 overflow-y-auto">
              {task.logs.length === 0 && <li className="text-sm text-muted">Chưa có hoạt động nào.</li>}
              {[...task.logs].reverse().map((l) => (
                <li key={l.id} className="text-sm">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-ink">{l.user_full_name || "Hệ thống"}</span>
                    <span className="text-xs text-muted">{formatDateTime(l.created_at)}</span>
                  </div>
                  <div className="text-ink-2">{l.content}</div>
                </li>
              ))}
            </ul>
            <div className="mt-3 flex gap-2 border-t border-rule pt-3">
              <TextInput placeholder="Viết bình luận…" value={commentText} onChange={(e) => setCommentText(e.target.value)} />
              <Button
                disabled={!commentText.trim() || m.addComment.isPending}
                onClick={() => wrap(m.addComment.mutateAsync({ content: commentText }), "Đã thêm bình luận").then(() => setCommentText(""))}
              >
                Gửi
              </Button>
            </div>
          </Section>

          {task.pauses.length > 0 && (
            <Section title="Thời gian tạm dừng / chờ">
              <ul className="divide-y divide-rule text-sm">
                {task.pauses.map((p) => (
                  <li key={p.id} className="flex items-center justify-between py-2">
                    <div>
                      <span className="font-medium text-ink">{TASK_PAUSE_REASON_LABELS[p.reason_code] || p.reason_code}</span>
                      <div className="text-xs text-muted">
                        {formatDateTime(p.started_at)} → {p.ended_at ? formatDateTime(p.ended_at) : "đang diễn ra"}
                        {p.note ? ` · ${p.note}` : ""}
                      </div>
                    </div>
                    {p.is_confirmed ? (
                      <Badge className="badge-ok">Đã xác nhận</Badge>
                    ) : canManage ? (
                      <Button variant="ghost" className="px-2 py-1 text-xs"
                              onClick={() => wrap(m.confirmPause.mutateAsync(p.id), "Đã xác nhận thời gian tạm dừng")}>
                        Xác nhận
                      </Button>
                    ) : (
                      <Badge className="badge-neutral">Chưa xác nhận</Badge>
                    )}
                  </li>
                ))}
              </ul>
            </Section>
          )}
        </div>

        <div className="space-y-5">
          {isParticipant && !["COMPLETED", "CANCELLED"].includes(task.status) && (
            <Section title="Cập nhật tiến độ (người thực hiện)">
              <div className="space-y-3">
                <input type="range" min="0" max="100" value={progress}
                       onChange={(e) => setProgress(Number(e.target.value))} className="w-full" />
                <div className="text-sm text-ink-2">{progress}%</div>
                <Textarea placeholder="Ghi chú (không bắt buộc)" value={note} onChange={(e) => setNote(e.target.value)} />
                <Button
                  disabled={m.updateProgress.isPending}
                  onClick={() => wrap(m.updateProgress.mutateAsync({ progress_percent: progress, note }), "Đã cập nhật tiến độ")}
                >
                  Cập nhật tiến độ
                </Button>
                {task.status !== "PENDING_ACCEPTANCE" && (
                  <>
                    <div className="border-t border-rule pt-3 text-xs text-muted">Nộp kết quả (chuyển sang Chờ nghiệm thu):</div>
                    <Textarea placeholder="Tóm tắt kết quả…" value={resultSummary} onChange={(e) => setResultSummary(e.target.value)} />
                    <Button
                      variant="secondary" disabled={!resultSummary.trim() || m.submit.isPending}
                      onClick={() => wrap(m.submit.mutateAsync({ result_summary: resultSummary }), "Đã nộp kết quả, chờ nghiệm thu")}
                    >
                      Nộp kết quả
                    </Button>
                  </>
                )}
                <div className="border-t border-rule pt-3 text-xs text-muted">Báo cáo vướng mắc / xin tạm dừng:</div>
                <Select value={blockerReason} onChange={(e) => setBlockerReason(e.target.value)}>
                  {Object.entries(TASK_PAUSE_REASON_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </Select>
                <Textarea placeholder="Diễn giải, minh chứng…" value={blockerNote} onChange={(e) => setBlockerNote(e.target.value)} />
                <Button
                  variant="secondary" disabled={m.reportBlocker.isPending}
                  onClick={() => wrap(m.reportBlocker.mutateAsync({ reason_code: blockerReason, note: blockerNote }), "Đã báo cáo vướng mắc")}
                >
                  Báo cáo vướng mắc
                </Button>
                {(task.status === "PAUSED" || task.status === "PENDING_COLLAB" || task.is_blocked) && (
                  <Button
                    variant="secondary" disabled={m.resume.isPending}
                    onClick={() => wrap(m.resume.mutateAsync({}), "Đã tiếp tục thực hiện")}
                  >
                    Tiếp tục thực hiện
                  </Button>
                )}
              </div>
            </Section>
          )}

          {canAccept && task.status === "PENDING_ACCEPTANCE" && (
            <Section title="Nghiệm thu (người có thẩm quyền)">
              <div className="space-y-3">
                <div className="label">Đánh giá chất lượng (thang 1-5)</div>
                <Select value={qualityLevel} onChange={(e) => setQualityLevel(e.target.value)}>
                  {[5, 4, 3, 2, 1].map((n) => <option key={n} value={n}>{n}</option>)}
                </Select>
                <Button
                  disabled={m.accept.isPending}
                  onClick={() => wrap(m.accept.mutateAsync({ quality_level: Number(qualityLevel) }), "Nghiệm thu thành công")}
                >
                  Nghiệm thu — Hoàn thành
                </Button>
                <Textarea placeholder="Lý do yêu cầu bổ sung/làm lại…" value={returnReason} onChange={(e) => setReturnReason(e.target.value)} />
                <Button
                  variant="danger" disabled={!returnReason.trim() || m.returnForRevision.isPending}
                  onClick={() => wrap(m.returnForRevision.mutateAsync({ reason: returnReason }), "Đã yêu cầu bổ sung/làm lại").then(() => setReturnReason(""))}
                >
                  Yêu cầu bổ sung/làm lại
                </Button>
              </div>
            </Section>
          )}

          {canManage && !["COMPLETED", "CANCELLED"].includes(task.status) && (
            <Section title="Quản lý nhiệm vụ">
              <div className="space-y-3">
                <div className="label">Gia hạn hoàn thành</div>
                <TextInput type="date" value={newDeadline} onChange={(e) => setNewDeadline(e.target.value)} />
                <TextInput placeholder="Lý do gia hạn…" value={deadlineReason} onChange={(e) => setDeadlineReason(e.target.value)} />
                <Button
                  variant="secondary" disabled={!newDeadline || !deadlineReason.trim() || m.extendDeadline.isPending}
                  onClick={() => wrap(m.extendDeadline.mutateAsync({ new_deadline: newDeadline, reason: deadlineReason }), "Đã cập nhật hạn hoàn thành")}
                >
                  Gia hạn
                </Button>
                <Button
                  variant="danger"
                  disabled={m.cancel.isPending}
                  onClick={() => {
                    const reason = window.prompt("Lý do hủy nhiệm vụ:");
                    if (reason) wrap(m.cancel.mutateAsync({ reason }), "Đã hủy nhiệm vụ");
                  }}
                >
                  Hủy nhiệm vụ
                </Button>
              </div>
            </Section>
          )}
        </div>
      </div>
    </div>
  );
}
