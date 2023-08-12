import React from 'react';
import { getItemsFromWarehouse, getWarehouseSchema } from '../services/api';
import styles from '../styles/warehouse.module.css';


const Warehouse: React.FC<{ warehouseName: string }> = async ({ warehouseName }) => {
    const items = await getItemsFromWarehouse(warehouseName);
    const schema = await getWarehouseSchema(warehouseName);
    const fields = Object.keys(schema);

    return (
        <>
            <h1>{warehouseName}</h1>
            <div className={`container p-0 m-0 ${styles.container}`}>
                <table className={`table table-hover table-striped table-bordered ${styles.table}`}>
                    <thead className='thead-dark'>
                        <tr>
                            {fields.map((header) => (
                                <th scope="col" key={header}>{header}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {items.map((item: Record<string, any>, index: number) => (
                            <tr key={index}
                                className={styles.cell}
                            >
                                {fields.map((header) => (
                                    <td key={header}>
                                        <div className={styles.cell}>
                                            <code>{item[header]}</code>
                                        </div>
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </>
    );
}

export default Warehouse;
