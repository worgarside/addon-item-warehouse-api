
import Warehouse from "@/components/Warehouse.server"




export default function Page({ params }: { params: { warehouse: string } }) {
    return (
        <Warehouse warehouseName={params.warehouse} />
    )
}
