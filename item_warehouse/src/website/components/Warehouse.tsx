import React, { useEffect, useState } from 'react';
import { getWarehouses, getItemsFromWarehouse } from '../services/api';


const Warehouse: React.FC<{ warehouseName: string }> = ({ warehouseName }) => {
    const [items, setItems] = useState([]);
    const [warehouses, setWarehouses] = useState([  ]);

    useEffect(() => {
        const fetchWarehouses = async () => {
            const data = await getWarehouses();
            setWarehouses(data);
        };

        const fetchItems = async () => {
            const data = await getItemsFromWarehouse(warehouseName);
            setItems(data);
        };

        fetchItems();
    }, [warehouseName]);


    return (
        <div>
            <h1>{warehouseName}</h1>
            <table>
                <thead>
                    <tr>
                        <th>Created At</th>
                        <th>Name</th>
                    </tr>
                </thead>
                <tbody>
                    {items.map(item => (
                        <tr key={item["id"]}>
                            <td>{item["created_at"]}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default Warehouse;
