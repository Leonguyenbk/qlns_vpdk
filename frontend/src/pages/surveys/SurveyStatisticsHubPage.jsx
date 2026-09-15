import { useState } from "react";
import { useSurveys } from "../../hooks/useSurveys";
import { PageHeader, Select } from "../../components/ui/primitives";
import { EmptyState, LoadingState } from "../../components/ui/DataStates";
import { SurveyStatisticsView } from "../../components/surveys/SurveyStatisticsView";

export default function SurveyStatisticsHubPage() {
  const { data, isLoading } = useSurveys({ page_size: 100 });
  const [surveyId, setSurveyId] = useState("");
  const surveys = data?.items || [];

  return (
    <div>
      <PageHeader title="Thống kê khảo sát" subtitle="Chọn một cuộc khảo sát để xem thống kê chi tiết" />
      {isLoading ? (
        <LoadingState />
      ) : !surveys.length ? (
        <EmptyState title="Chưa có cuộc khảo sát nào" />
      ) : (
        <>
          <div className="mb-5">
            <Select value={surveyId} onChange={(e) => setSurveyId(e.target.value)} className="w-full max-w-sm">
              <option value="">-- Chọn cuộc khảo sát --</option>
              {surveys.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title}
                </option>
              ))}
            </Select>
          </div>
          {surveyId ? (
            <SurveyStatisticsView surveyId={surveyId} />
          ) : (
            <EmptyState title="Hãy chọn một cuộc khảo sát ở trên để xem thống kê" />
          )}
        </>
      )}
    </div>
  );
}
