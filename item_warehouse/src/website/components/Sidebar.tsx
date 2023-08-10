'use client'

import Link from 'next/link';
import styles from '../styles/sidebar.module.css'
import React, { useState, useEffect } from 'react';
import { getWarehouses } from '../services/api';
import Icon from '@mdi/react';
import { mdiWarehouse } from '@mdi/js';
interface Warehouse {
    name: string;
}

interface SidebarProps {
}

const Sidebar: React.FC<SidebarProps> = () => {
    const [warehouses, setWarehouses] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            const warehouseData = await getWarehouses();
            setWarehouses(warehouseData);
        };

        fetchData();
    }, []);

    return (
        <div className={styles.sidebar}>
            <h2 className={`text-center my-1 fw-bold ${styles.header}`}>Warehouses</h2>
            <div className='list-group'>
                {warehouses.map((warehouse: Warehouse) => (
                    <Link className='list-group-item text-decoration-none' href={`/warehouse/${encodeURIComponent(warehouse.name)}`}>
                        <Icon class="me-2" path={mdiWarehouse} size={1} />{warehouse.name}
                    </Link>
                ))}
            </div>
        </div>
    );
}

export default Sidebar;
