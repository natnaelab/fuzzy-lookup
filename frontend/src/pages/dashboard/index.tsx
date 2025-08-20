import { AreaChartComponent } from "@/components/charts/area-chart";
import { BarChartSide } from "@/components/charts/bar-chart-side";
import MainWrapper from "@/layouts/wrappers/main-wrapper";

export function Dashboard() {
  return (
    <MainWrapper>
      <div className="flex items-center">
        <h1 className="text-lg font-semibold md:text-2xl">Dashboard</h1>
      </div>
      <div className="flex flex-col items-start justify-start rounded-lg border border-dashed shadow-sm p-5">
        {/* <div className="flex flex-row flex-wrap items-center gap-1 text-center"> */}
        <AreaChartComponent />
        {/* </div> */}
        <div className="mt-4">
          <BarChartSide />
        </div>
      </div>
    </MainWrapper>
  );
}
