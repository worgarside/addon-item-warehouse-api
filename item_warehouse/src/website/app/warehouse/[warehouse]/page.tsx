
import Warehouse from "@/components/Warehouse.client"




export default function Page({ params }: { params: { warehouse: string } }) {
    return (
        <Warehouse warehouseName={params.warehouse} />
    )
}
