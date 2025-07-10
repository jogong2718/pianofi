import { FC } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, Clock, Music, CheckCircle } from "lucide-react";

interface MetricsCardsProps {
  metrics: any;
  loading: boolean;
}

const MetricsCards: FC<MetricsCardsProps> = ({ metrics, loading }) => {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            Total Transcriptions
          </CardTitle>
          <FileText className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {loading ? "..." : metrics?.total_transcriptions || 0}
          </div>
          <p className="text-xs text-muted-foreground">
            All time transcriptions
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Processing</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {loading ? "..." : metrics?.processing_count || 0}
          </div>
          <p className="text-xs text-muted-foreground">
            Currently being processed
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">This Month</CardTitle>
          <Music className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {loading ? "..." : metrics?.this_month_count || 0}
          </div>
          <p className="text-xs text-muted-foreground">
            Transcriptions this month
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            Transcriptions Left this Month
          </CardTitle>
          <CheckCircle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {loading
              ? "..."
              : metrics?.transcriptions_left === null
              ? "∞"
              : metrics?.transcriptions_left || 0}
          </div>
          <p className="text-xs text-muted-foreground">
            {metrics?.transcriptions_left === null
              ? "Unlimited plan"
              : "Remaining this month"}
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default MetricsCards;
