import { useParams, useNavigate } from "react-router-dom";
import { useSurvey } from "../../hooks/useSurveys";
import { PageHeader, Button } from "../../components/ui/primitives";
import { SurveyStatisticsView } from "../../components/surveys/SurveyStatisticsView";

export default function SurveyStatisticsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: survey } = useSurvey(id);

  return (
    <div>
      <PageHeader
        title="Thống kê khảo sát"
        subtitle={survey?.title}
        actions={
          <Button variant="secondary" onClick={() => navigate(`/surveys/${id}`)}>
            ← Thông tin khảo sát
          </Button>
        }
      />
      <SurveyStatisticsView surveyId={id} />
    </div>
  );
}
