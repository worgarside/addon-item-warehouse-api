import axios from 'axios';

const getItemsFromWarehouse = async (warehouseName: string) => {
    const response = await axios.get(`http://0.0.0.0:8000/v1/warehouses/${warehouseName}/items?limit=10`);

    return response.data.items;
}

const getWarehouses = async () => {
    const response = await axios.get(`http://0.0.0.0:8000/v1/warehouses`);

    return response.data.warehouses;
}

// const getWarehouseSchema = async (warehouseName: string) => {
    // const response = await axios.get(`http://localhost:8000/v1/warehouses/${warehouseName}/schema`);


export {
    getItemsFromWarehouse,
    getWarehouses
};
