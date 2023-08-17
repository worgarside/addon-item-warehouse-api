import axios from "axios";

type ItemValue = string | number | boolean | null;

interface ItemsResponse {
  count: number;
  page: number;
  total: number;
  items: Record<string, ItemValue>[];
}

interface WarehouseSchemaProperty {
  autoincrement: string;
  default: string;
  index: boolean;
  key: string;
  nullable: number;
  primary_key: boolean;
  type_kwargs: Record<string, number>;
  type: string;
  unique: boolean;
}

interface Warehouse {
  name: string;
  created_at: string;
  item_name: string;
  item_schema: Record<string, WarehouseSchemaProperty>;
}

interface WarehousesResponse {
  count: number;
  page: number;
  total: number;
  warehouses: Warehouse[];
}

const getItemsFromWarehouse = async (
  warehouseName: string,
  count: string,
  pageNumber: string,
): Promise<ItemsResponse> => {
  const response = await axios.get<ItemsResponse>(
    `http://0.0.0.0:8000/v1/warehouses/${warehouseName}/items?page_size=${count}&page=${
      pageNumber || 1
    }`,
  );

  return response.data;
};

const getWarehouse = async (warehouseName: string): Promise<Warehouse> => {
  const response = await axios.get<Warehouse>(
    `http://0.0.0.0:8000/v1/warehouses/${warehouseName}`,
  );

  return response.data;
};

const getWarehouses = async (): Promise<Warehouse[]> => {
  const response = await axios.get<WarehousesResponse>(
    `http://0.0.0.0:8000/v1/warehouses`,
  );

  return response.data.warehouses;
};

const getWarehouseSchema = async (
  warehouseName: string,
): Promise<WarehouseSchemaProperty> => {
  const response = await axios.get<WarehouseSchemaProperty>(
    `http://0.0.0.0:8000/v1/warehouses/${warehouseName}/schema`,
  );

  return response.data;
};

export {
  getItemsFromWarehouse,
  getWarehouse,
  getWarehouses,
  getWarehouseSchema,
};
export type { ItemsResponse };
