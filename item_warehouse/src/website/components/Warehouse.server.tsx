import React, { useEffect, useState } from 'react';
import { getWarehouses, getItemsFromWarehouse } from '../services/api';


const Warehouse: React.FC<{ warehouseName: string }> = async ({ warehouseName }) => {

    const items = await getItemsFromWarehouse(warehouseName);

    if (items.length === 0) return null;

    const headers = Object.keys(items[0]);

    return (
        <div>
            <h1>{warehouseName}</h1>
            <table>
                <thead>
                    <tr>
                        {headers.map((header) => (
                            <th key={header}>{header}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {items.map((item: Record<string, any>, index: number) => (
                        <tr key={index}>
                            {headers.map((header) => (
                                <td key={header}>{item[header]}</td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export default Warehouse;
