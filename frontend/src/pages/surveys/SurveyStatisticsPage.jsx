import { useParams } from "react-router-dom";
import { SurveyStatisticsView } from "../../components/surveys/SurveyStatisticsView";

export default function SurveyStatisticsPage() {
  const { id } = useParams();
  return <SurveyStatisticsView surveyId={id} />;
}
