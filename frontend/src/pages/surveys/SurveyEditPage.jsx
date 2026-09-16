import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import toast from "react-hot-toast";
import {
  useSurvey,
  useSurveyMutations,
  exportSurvey,
} from "../../hooks/useSurveys";
import { useCan } from "../../components/Can";
import {
  PERMISSIONS,
  SURVEY_STATUS_LABELS,
  SURVEY_STATUS_BADGE,
} from "../../lib/constants";
import { surveySchema } from "../../schemas";
import { apiErrorMessage } from "../../lib/api";
import {
  PageHeader,
  Button,
  Badge,
  Card,
  FormField,
  TextInput,
  Textarea,
} from "../../components/ui/primitives";
import { LoadingState, ErrorState } from "../../components/ui/DataStates";
import { QRCodeModal } from "../../components/surveys/QRCodeModal";
import { PreviewModal } from "../../components/surveys/PreviewModal";
import { BranchLimitsCard } from "../../components/surveys/BranchLimitsCard";

function toLocalInput(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromLocalInput(value) {
  if (!value) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d.toISOString();
}

const NEXT_STATUS = {
  draft: { status: "active", label: "Xuất bản" },
  paused: { status: "active", label: "Mở lại" },
  closed: { status: "archived", label: "Lưu trữ" },
};

export default function SurveyEditPage() {
  const { id } = useParams();
  const isNew = !id;
  const navigate = useNavigate();
  const { can } = useCan();
  const { data: survey, isLoading, isError, error, refetch } = useSurvey(id);
  const { create, update, changeStatus, duplicate } = useSurveyMutations();
  const [showQr, setShowQr] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [exporting, setExporting] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(surveySchema),
    defaultValues: { is_anonymous: true },
  });

  useEffect(() => {
    if (survey) {
      reset({
        title: survey.title,
        description: survey.description || "",
        welcome_message: survey.welcome_message || "",
        is_anonymous: survey.is_anonymous,
        start_at: toLocalInput(survey.start_at),
        end_at: toLocalInput(survey.end_at),
      });
    }
  }, [survey, reset]);

  const locked =
    survey && (survey.status === "closed" || survey.status === "archived");
  const canEdit = isNew
    ? can(PERMISSIONS.SURVEY_CREATE)
    : can(PERMISSIONS.SURVEY_UPDATE);

  const onSubmit = async (values) => {
    const body = {
      title: values.title,
      description: values.description || null,
      welcome_message: values.welcome_message || null,
      is_anonymous: values.is_anonymous,
      start_at: fromLocalInput(values.start_at),
      end_at: fromLocalInput(values.end_at),
    };
    try {
      if (isNew) {
        const resp = await create.mutateAsync(body);
        toast.success("Tạo khảo sát thành công, tiếp tục thêm câu hỏi");
        navigate(`/surveys/${resp.data.data.id}/questions`);
      } else {
        await update.mutateAsync({ id, body });
        toast.success("Cập nhật khảo sát thành công");
      }
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const onChangeStatus = async (status, label) => {
    try {
      await changeStatus.mutateAsync({ id, status });
      toast.success(`${label} thành công`);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const onDuplicate = async () => {
    try {
      const resp = await duplicate.mutateAsync(id);
      toast.success("Đã sao chép khảo sát");
      navigate(`/surveys/${resp.data.data.id}`);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    }
  };

  const onExport = async () => {
    setExporting(true);
    try {
      await exportSurvey(id);
    } catch (err) {
      toast.error(apiErrorMessage(err, "Xuất Excel thất bại"));
    } finally {
      setExporting(false);
    }
  };

  if (!isNew && isLoading) return <LoadingState />;
  if (!isNew && isError) return <ErrorState error={error} onRetry={refetch} />;

  const next = survey && NEXT_STATUS[survey.status];

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <button
          type="button"
          onClick={() => navigate("/surveys")}
          className="mb-4 flex items-center gap-1.5 text-sm text-muted hover:text-accent-text transition-colors"
        >
          ← Quay lại Danh sách khảo sát
        </button>
        <PageHeader
          title={isNew ? "Tạo khảo sát" : "Sửa khảo sát"}
          subtitle={!isNew && `/khao-sat/${survey?.slug}`}
          actions={
            survey && (
              <Badge className={SURVEY_STATUS_BADGE[survey.status]}>
                {SURVEY_STATUS_LABELS[survey.status]}
              </Badge>
            )
          }
        />
        <Card>
          <form className="grid gap-4" onSubmit={handleSubmit(onSubmit)}>
            {locked && (
              <p className="rounded-lg border border-rule bg-paper-2 px-3 py-2 text-xs text-muted">
                Khảo sát đã đóng/lưu trữ nên không thể sửa thông tin.
              </p>
            )}
            <FormField
              label="Tên khảo sát"
              required
              error={errors.title?.message}
            >
              <TextInput
                {...register("title")}
                error={errors.title}
                disabled={locked || !canEdit}
              />
            </FormField>
            <FormField
              label="Lời chào"
              hint="Hiển thị đầu trang khảo sát công khai, trước khi chọn chi nhánh/nhập thông tin"
              error={errors.welcome_message?.message}
            >
              <Textarea
                {...register("welcome_message")}
                disabled={locked || !canEdit}
                rows={2}
              />
            </FormField>
            <FormField label="Mô tả ngắn" error={errors.description?.message}>
              <Textarea
                {...register("description")}
                disabled={locked || !canEdit}
                rows={3}
              />
            </FormField>
            <div className="grid grid-cols-2 gap-4">
              <FormField label="Ngày bắt đầu">
                <TextInput
                  type="datetime-local"
                  {...register("start_at")}
                  disabled={locked || !canEdit}
                />
              </FormField>
              <FormField label="Ngày kết thúc">
                <TextInput
                  type="datetime-local"
                  {...register("end_at")}
                  disabled={locked || !canEdit}
                />
              </FormField>
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                {...register("is_anonymous")}
                disabled={locked || !canEdit}
              />
              Khảo sát ẩn danh (không bắt buộc nhập họ tên/SĐT — người dân vẫn
              luôn thấy ô nhập, chỉ khác là không bắt buộc điền)
            </label>
            {canEdit && !locked && (
              <div>
                <Button
                  type="submit"
                  disabled={create.isPending || update.isPending}
                >
                  {isNew ? "Tạo khảo sát" : "Lưu thay đổi"}
                </Button>
              </div>
            )}
          </form>
        </Card>
      </div>

      {!isNew && survey && (
        <div className="grid content-start gap-4">
          <Card>
            <h3 className="mb-3 font-semibold text-slate-800">Thao tác</h3>
            <div className="grid gap-2">
              <Button
                variant="secondary"
                onClick={() => navigate(`/surveys/${id}/questions`)}
              >
                Quản lý câu hỏi
              </Button>
              <Button variant="secondary" onClick={() => setShowPreview(true)}>
                Xem trước
              </Button>
              {survey.status === "active" && (
                <Button variant="secondary" onClick={() => setShowQr(true)}>
                  Tạo mã QR
                </Button>
              )}
              {can(PERMISSIONS.SURVEY_VIEW_STATISTICS) && (
                <Button
                  variant="secondary"
                  onClick={() => navigate(`/surveys/${id}/statistics`)}
                >
                  Xem thống kê
                </Button>
              )}
              {can(PERMISSIONS.SURVEY_VIEW_STATISTICS) && (
                <Button
                  variant="secondary"
                  onClick={() => navigate(`/surveys/${id}/responses`)}
                >
                  Kết quả khảo sát
                </Button>
              )}
              {can(PERMISSIONS.SURVEY_EXPORT) && (
                <Button
                  variant="secondary"
                  onClick={onExport}
                  disabled={exporting}
                >
                  {exporting ? "Đang xuất…" : "Xuất Excel"}
                </Button>
              )}
              {can(PERMISSIONS.SURVEY_CREATE) && (
                <Button variant="secondary" onClick={onDuplicate}>
                  Sao chép khảo sát
                </Button>
              )}
            </div>
          </Card>

          {can(PERMISSIONS.SURVEY_UPDATE) &&
            (next ||
              survey.status === "active" ||
              survey.status === "paused") && (
              <Card>
                <h3 className="mb-3 font-semibold text-slate-800">
                  Vòng đời khảo sát
                </h3>
                <div className="grid gap-2">
                  {next && (
                    <Button
                      onClick={() => onChangeStatus(next.status, next.label)}
                    >
                      {next.label}
                    </Button>
                  )}
                  {survey.status === "active" && (
                    <Button
                      variant="secondary"
                      onClick={() => onChangeStatus("paused", "Tạm khóa")}
                    >
                      Tạm khóa
                    </Button>
                  )}
                  {(survey.status === "active" ||
                    survey.status === "paused") && (
                    <Button
                      variant="danger"
                      onClick={() => onChangeStatus("closed", "Đóng khảo sát")}
                    >
                      Đóng khảo sát
                    </Button>
                  )}
                </div>
              </Card>
            )}

          <BranchLimitsCard
            surveyId={id}
            canEdit={can(PERMISSIONS.SURVEY_UPDATE) && !locked}
          />
        </div>
      )}

      <QRCodeModal
        survey={showQr ? survey : null}
        onClose={() => setShowQr(false)}
      />
      <PreviewModal
        survey={showPreview ? survey : null}
        onClose={() => setShowPreview(false)}
      />
    </div>
  );
}
