import WarehousePage from "../../../components/WarehousePage.server";

export default function Page({
  params,
  searchParams,
}: {
  params: { warehouse: string };
  searchParams: { page: string };
}) {
  return (
    <WarehousePage warehouseName={params.warehouse} page={searchParams.page} />
  );
}
